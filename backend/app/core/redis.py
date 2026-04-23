import redis.asyncio as aioredis
from redis.asyncio import Redis
from app.core.config import settings
from functools import lru_cache
import json
from typing import Any, Optional
from fastapi.encoders import jsonable_encoder


_redis_pool: Optional[Redis] = None


async def get_redis() -> Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def redis_get(key: str) -> Optional[Any]:
    r = await get_redis()
    value = await r.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


async def redis_set(key: str, value: Any, ttl: int = 300) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(jsonable_encoder(value)))


async def redis_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def redis_exists(key: str) -> bool:
    r = await get_redis()
    return bool(await r.exists(key))


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
