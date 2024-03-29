from django_hbase.client import HBaseClient
from .exceptions import EmptyColumnError, BadRowKeyError
from .fields import HBaseField, IntegerField, TimestampField
from django.conf import settings


class  HBaseModel:

    class Meta:
        table_name = None
        row_key = ()

    def __init__(self, **kwargs):
        for key, filed in self.get_field_hash().items():
            value = kwargs.get(key)
            setattr(self, key, value)

    @classmethod
    def init_from_row(cls, row_key, row_data):
        if not row_data:
            return None
        data = cls.deserialize_row_key(row_key)
        for column_key, column_value in row_data.items():
            # remove column family
            column_key = column_key.decode('utf-8')
            key = column_key[column_key.find(':') + 1:]
            data[key] = cls.deserialize_field(key, column_value)
        return cls(**data)

    @classmethod
    def get_field_hash(cls):
        field_hash = {}
        for field in cls.__dict__:
            field_obj = getattr(cls, field)
            if isinstance(field_obj, HBaseField):
                field_hash[field] = field_obj
        return field_hash

    @classmethod
    def serialize_field(cls, field, value):
        value = str(value)
        if isinstance(field, IntegerField):
            while len(value) < 16:
                #
                # In lexicographical order, some undesired cases like 1 10 2 may appear,
                # to stave off such cases, we can fix the length of value as 16 digits,
                # by complementing 0 from the high-order
                # Notice: it must be '0' before value, cannot be value + '0'
                value = '0' + value
        if field.reverse:
            value = value[::-1]
        return value

    @classmethod
    def deserialize_field(cls, key, value):
        field = cls.get_field_hash()[key]
        if field.reverse:
            value = value[::-1]
        if field.field_type in [IntegerField.field_type, TimestampField.field_type]:
            return int(value)
        return value

    @classmethod
    def serialize_row_key(cls, data, is_prefix=False):
        """
        serialize dict to bytes (not str):
        {key1: val1} => b'val1'
        {key1: val1, key2: val2} => b'val1:val2'
        {key1: val1, key2: val2, key3: val3} => b'val1:val2:val3'
        """
        field_hash = cls.get_field_hash()
        values = []
        for key, field in field_hash.items():
            if field.column_family:
                continue
            value = data.get(key)
            if value is None:
                if not is_prefix:
                    raise BadRowKeyError(f"{key} is missing in row key.")
                break
            value = cls.serialize_field(field, value)
            if ':' in value:
                raise BadRowKeyError(f"{key} should not contain ':' in value: {value}")
            values.append(value)
        return bytes(':'.join(values), encoding='utf-8')

    @classmethod
    def serialize_row_key_from_tuple(cls, row_key_tuple):
        if row_key_tuple is None:
            return None
        data = {
            key: value
            for key, value in zip(cls.Meta.row_key, row_key_tuple)
        }
        return cls.serialize_row_key(data, is_prefix=True)

    @classmethod
    def deserialize_row_key(cls, row_key):
        """
        'val1' => {key1: val1}
        'val1:val2' => {key1: val1, key2: val2}
        'val1:val2:val3' => {key1: val1, key2: val2, key3: val3}
        """
        data = {}
        if isinstance(row_key, bytes):
            row_key = row_key.decode('utf-8')
        # putting a colon to the tail that val1:val2 => val1:val2:,
        # it can easily find a val through find(':')
        row_key = row_key + ':'
        for key in cls.Meta.row_key:
            index = row_key.find(':')
            if index == -1:
                break
            data[key] = cls.deserialize_field(key, row_key[:index])
            row_key = row_key[index + 1:]
        return data

    @classmethod
    def serialize_row_data(cls, data):
        row_data = {}
        field_hash = cls.get_field_hash()
        for key, field in field_hash.items():
            if not field.column_family:
                continue
            column_key = '{}:{}'.format(field.column_family, key)
            column_value = data.get(key)
            if column_value is None:
                continue
            row_data[column_key] = cls.serialize_field(field, column_value)
        return row_data

    @property
    def row_key(self):
        return self.serialize_row_key(self.__dict__)

    @classmethod
    def get_table(cls):
        conn = HBaseClient.get_connection()
        return conn.table(cls.get_table_name())

    def save(self):
        row_data = self.serialize_row_data(self.__dict__)
        # if row_data is null, hbase would ignore this record but raise an exception,
        # so it needs to give EmptyColumnError() exception manually
        if len(row_data) == 0:
            raise EmptyColumnError()
        table = self.get_table()
        table.put(self.row_key, row_data)

    @classmethod
    def get(cls, **kwargs):
        row_key = cls.serialize_row_key(kwargs)
        table = cls.get_table()
        row = table.row(row_key)
        return cls.init_from_row(row_key, row)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        instance.save()
        return instance

    @classmethod
    def filter(cls, start=None, stop=None, prefix=None, limit=None, reverse=False):
        # serialize tuple to string
        row_start = cls.serialize_row_key_from_tuple(start)
        row_stop = cls.serialize_row_key_from_tuple(stop)
        row_prefix = cls.serialize_row_key_from_tuple(prefix)

        # scan table
        table = cls.get_table()
        rows = table.scan(row_start, row_stop, row_prefix, limit=limit, reverse=reverse)

        # deserialize to instance list
        results = []
        for row_key, row_data in rows:
            instance = cls.init_from_row(row_key, row_data)
            results.append(instance)
        return results

    @classmethod
    def get_table_name(cls):
        if not cls.Meta.table_name:
            raise NotImplementedError('Missing table_name in HBaseModel meta class')
        if settings.TESTING:
            return f'test_{cls.Meta.table_name}'
        return cls.Meta.table_name

    @classmethod
    def create_table(cls):
        if not settings.TESTING:
            raise Exception('You cannot create table outside the unit tests')
        conn = HBaseClient.get_connection()

        # decode() is to  convert table names from bytes to string
        tables = [table.decode('utf-8') for table in conn.tables()]
        if cls.get_table_name() in tables:
            return
        column_families = {
            field.column_family: dict()
            for key, field in cls.get_field_hash().items()
            if field.column_family is not None
        }
        conn.create_table(cls.get_table_name(), column_families)

    @classmethod
    def drop_table(cls):
        if not settings.TESTING:
            raise Exception('You cannot drop table outside the unit tests')
        conn = HBaseClient.get_connection()
        conn.delete_table(cls.get_table_name(), True)
