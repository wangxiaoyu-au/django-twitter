from django.core import serializers
from utils.json_encoder import JSONEncoder


class DjangoModelSerializer:

    @classmethod
    def serialize(cls, instance):
        # Django serializers can only be fed by data in structure of
        # QuerySet or List, that's why it needs put the instance in [],
        # in this way an instance turns into a list
        return serializers.serialize('json', [instance], cls=JSONEncoder)

    @classmethod
    def deserialize(cls, serialized_data):
        # notice that serializer.deserialize() can only return
        # DeserializedObject, to obtain the original model,
        # it needs a further step .object
        return list(serializers.deserialize('json', serialized_data))[0].object
