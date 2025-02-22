import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def init_redis():
    """Подключение к Redis"""
    global redis_client
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


async def close_redis():
    """Закрытие соединения с Redis"""
    await redis_client.close()
