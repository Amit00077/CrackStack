from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


_redis_unavailable: bool = False


async def get_redis() -> aioredis.Redis | None:
    global _redis, _redis_unavailable
    if _redis is None and not _redis_unavailable:
        try:
            _redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
                retry_on_timeout=False,
            )
            await _redis.ping()
        except Exception:
            logger.warning("Redis unavailable, running without it")
            _redis_unavailable = True
            _redis = None
            return None
    return _redis


async def close_redis() -> None:
    global _redis, _redis_unavailable
    if _redis:
        await _redis.close()
        _redis = None
    _redis_unavailable = False


async def blacklist_token(token: str, ttl: int) -> None:
    r = await get_redis()
    if r is None:
        return
    try:
        await r.setex(f"blacklist:{token}", ttl, "1")
    except RedisError:
        logger.warning("Redis error during blacklist_token, ignoring")
        global _redis_unavailable
        _redis_unavailable = True
        await close_redis()


async def is_token_blacklisted(token: str) -> bool:
    r = await get_redis()
    if r is None:
        return False
    try:
        return await r.exists(f"blacklist:{token}") == 1
    except RedisError:
        logger.warning("Redis error during is_token_blacklisted, ignoring")
        global _redis_unavailable
        _redis_unavailable = True
        await close_redis()
        return False
