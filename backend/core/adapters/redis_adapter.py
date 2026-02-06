"""
Redis Adapter - Implementation of CachePort for Redis.

Wraps the existing cache.py and distributed_lock.py functionality
with the CachePort interface. Preserves connection pooling and lock semantics.
"""

import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import redis.asyncio as redis

from core.config import settings
from core.ports.cache import LockResult

logger = logging.getLogger(__name__)


class RedisAdapter:
    """
    Redis implementation of CachePort.

    Features:
    - Key-value caching with TTL
    - Distributed locking with ownership tracking
    - Atomic operations
    - Connection pooling
    """

    LOCK_KEY_PREFIX = "distributed_lock:"

    def __init__(
        self,
        *,
        redis_url: str | None = None,
    ) -> None:
        self._redis_url = redis_url or settings.redis_url
        self._redis: redis.Redis | None = None
        self._instance_id = uuid.uuid4().hex

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        try:
            r = await self._get_redis()
            value = await r.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error("Cache get error for key %s: %s", key, e)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set a value in cache."""
        try:
            r = await self._get_redis()
            serialized = json.dumps(value) if not isinstance(value, str) else value
            if ttl_seconds:
                await r.setex(key, ttl_seconds, serialized)
            else:
                await r.set(key, serialized)
            return True
        except Exception as e:
            logger.error("Cache set error for key %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        try:
            r = await self._get_redis()
            result = await r.delete(key)
            return result > 0
        except Exception as e:
            logger.error("Cache delete error for key %s: %s", key, e)
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        try:
            r = await self._get_redis()
            return await r.exists(key) > 0
        except Exception as e:
            logger.error("Cache exists error for key %s: %s", key, e)
            return False

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache."""
        if not keys:
            return {}

        try:
            r = await self._get_redis()
            values = await r.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error("Cache get_many error: %s", e)
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set multiple values in cache."""
        if not mapping:
            return True

        try:
            r = await self._get_redis()
            serialized = {
                k: json.dumps(v) if not isinstance(v, str) else v
                for k, v in mapping.items()
            }

            async with r.pipeline() as pipe:
                if ttl_seconds:
                    for key, value in serialized.items():
                        pipe.setex(key, ttl_seconds, value)
                else:
                    pipe.mset(serialized)
                await pipe.execute()
            return True
        except Exception as e:
            logger.error("Cache set_many error: %s", e)
            return False

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys from cache."""
        if not keys:
            return 0

        try:
            r = await self._get_redis()
            return await r.delete(*keys)
        except Exception as e:
            logger.error("Cache delete_many error: %s", e)
            return 0

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        try:
            r = await self._get_redis()
            keys = []
            async for key in r.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await r.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Cache delete_pattern error for %s: %s", pattern, e)
            return 0

    async def increment(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """Atomically increment a value."""
        try:
            r = await self._get_redis()
            return await r.incrby(key, amount)
        except Exception as e:
            logger.error("Cache increment error for key %s: %s", key, e)
            return 0

    async def decrement(
        self,
        key: str,
        amount: int = 1,
    ) -> int:
        """Atomically decrement a value."""
        try:
            r = await self._get_redis()
            return await r.decrby(key, amount)
        except Exception as e:
            logger.error("Cache decrement error for key %s: %s", key, e)
            return 0

    async def get_ttl(self, key: str) -> int | None:
        """Get remaining TTL for a key."""
        try:
            r = await self._get_redis()
            ttl = await r.ttl(key)
            if ttl == -2:  # Key doesn't exist
                return -2
            if ttl == -1:  # No expiry
                return None
            return ttl
        except Exception as e:
            logger.error("Cache get_ttl error for key %s: %s", key, e)
            return -2

    async def set_ttl(self, key: str, ttl_seconds: int) -> bool:
        """Set TTL on an existing key."""
        try:
            r = await self._get_redis()
            return await r.expire(key, ttl_seconds)
        except Exception as e:
            logger.error("Cache set_ttl error for key %s: %s", key, e)
            return False

    # =========================================================================
    # Distributed Locking
    # =========================================================================

    def _get_lock_key(self, lock_name: str) -> str:
        """Generate Redis key for the lock."""
        return f"{self.LOCK_KEY_PREFIX}{lock_name}"

    def _get_lock_token(self) -> str:
        """Generate a unique lock token."""
        return f"{self._instance_id}:{uuid.uuid4().hex[:8]}"

    async def acquire_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
        blocking: bool = False,
        blocking_timeout: float | None = None,
    ) -> LockResult:
        """Acquire a distributed lock."""
        try:
            r = await self._get_redis()
            key = self._get_lock_key(lock_name)
            lock_token = self._get_lock_token()

            # Try to acquire with SET NX EX
            acquired = await r.set(key, lock_token, nx=True, ex=ttl_seconds)

            if acquired:
                logger.debug("Acquired lock: %s", lock_name)
                return LockResult(acquired=True, lock_token=lock_token)

            if not blocking:
                logger.debug("Failed to acquire lock: %s (already held)", lock_name)
                return LockResult(acquired=False)

            # Blocking mode - poll for lock
            import asyncio
            import time

            start = time.time()
            timeout = blocking_timeout or 30.0

            while time.time() - start < timeout:
                await asyncio.sleep(0.1)
                acquired = await r.set(key, lock_token, nx=True, ex=ttl_seconds)
                if acquired:
                    logger.debug("Acquired lock after waiting: %s", lock_name)
                    return LockResult(acquired=True, lock_token=lock_token)

            return LockResult(
                acquired=False,
                error_message="Lock acquisition timed out",
            )

        except Exception as e:
            logger.error("Error acquiring lock %s: %s", lock_name, e)
            # Fail-open: allow operation on Redis errors
            return LockResult(acquired=True, lock_token=None)

    async def release_lock(
        self,
        lock_name: str,
        lock_token: str,
    ) -> bool:
        """Release a distributed lock."""
        if not lock_token:
            return True

        try:
            r = await self._get_redis()
            key = self._get_lock_key(lock_name)

            # Lua script for atomic check-and-delete
            release_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await r.eval(release_script, 1, key, lock_token)

            if result:
                logger.debug("Released lock: %s", lock_name)
                return True
            else:
                logger.warning("Could not release lock %s: token mismatch", lock_name)
                return False

        except Exception as e:
            logger.error("Error releasing lock %s: %s", lock_name, e)
            return False

    async def extend_lock(
        self,
        lock_name: str,
        lock_token: str,
        additional_seconds: int,
    ) -> bool:
        """Extend the TTL of a held lock."""
        if not lock_token:
            return False

        try:
            r = await self._get_redis()
            key = self._get_lock_key(lock_name)

            # Verify ownership and extend
            extend_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """

            result = await r.eval(
                extend_script, 1, key, lock_token, additional_seconds
            )
            return bool(result)

        except Exception as e:
            logger.error("Error extending lock %s: %s", lock_name, e)
            return False

    @asynccontextmanager
    async def distributed_lock(
        self,
        lock_name: str,
        ttl_seconds: int = 60,
    ) -> AsyncIterator[bool]:
        """Context manager for distributed locking."""
        result = await self.acquire_lock(lock_name, ttl_seconds)
        try:
            yield result.acquired
        finally:
            if result.acquired and result.lock_token:
                await self.release_lock(lock_name, result.lock_token)

    # =========================================================================
    # Health and Stats
    # =========================================================================

    async def ping(self) -> bool:
        """Check if cache is available."""
        try:
            r = await self._get_redis()
            return await r.ping()
        except Exception as e:
            logger.error("Cache ping error: %s", e)
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        try:
            r = await self._get_redis()
            info = await r.info()
            return {
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_keys": info.get("db0", {}).get("keys", 0)
                if isinstance(info.get("db0"), dict)
                else 0,
                "uptime_seconds": info.get("uptime_in_seconds"),
                "redis_version": info.get("redis_version"),
            }
        except Exception as e:
            logger.error("Cache get_stats error: %s", e)
            return {"error": str(e)}

    async def flush_all(self) -> bool:
        """Clear all cache data (use with caution!)."""
        try:
            r = await self._get_redis()
            await r.flushdb()
            logger.warning("Flushed all cache data")
            return True
        except Exception as e:
            logger.error("Cache flush_all error: %s", e)
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Default instance
redis_adapter = RedisAdapter()
