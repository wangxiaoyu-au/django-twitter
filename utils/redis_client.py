from django.conf import settings
import redis


class RedisClient:
    conn = None

    @classmethod
    def get_connection(cls):
        # adopting singleton scheme, only create one connection globally
        if cls.conn:
            return cls.conn

        cls.conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        return cls.conn

    @classmethod
    def clear(cls):
        # for testing purpose, clear all keys in redis
        if not settings.TESTING:
            raise Exception('You cannot flush redis in production environment!')
        conn = cls.get_connection()
        conn.flushdb()
