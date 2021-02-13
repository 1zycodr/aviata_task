import aioredis

class RedisConnection(object):
    obj = None
    connection = None

    @classmethod
    async def __new__(cls, *args):
        if cls.obj is None:
            cls.obj = object.__new__(cls)
            cls.connection = await aioredis.create_redis('redis://localhost')
        return cls.obj