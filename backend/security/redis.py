import redis.asyncio as redis
from config import settings

_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)
redis_client = redis.Redis(connection_pool=_pool)


async def get_redis() -> redis.Redis:
    return redis_client
