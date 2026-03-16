import redis.asyncio as aioredis
from app.core.config import settings

_redis_pool = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def publish_telemetry(drone_id: str, data: dict):
    r = await get_redis()
    import json
    await r.publish(f"telemetry:{drone_id}", json.dumps(data))


async def publish_event(channel: str, data: dict):
    r = await get_redis()
    import json
    await r.publish(channel, json.dumps(data))
