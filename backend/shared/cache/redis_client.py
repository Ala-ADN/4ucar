"""Redis client factory."""

import redis.asyncio as aioredis

_client: aioredis.Redis | None = None


def get_redis(url: str) -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(url, decode_responses=True)
    return _client


async def publish(redis_client: aioredis.Redis, channel: str, message: str) -> None:
    await redis_client.publish(channel, message)
