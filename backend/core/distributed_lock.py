"""
Distributed Locking Service

Provides Redis-backed distributed locks for preventing job overlap when running
multiple backend instances (pods). This solves the limitation of APScheduler's
`max_instances=1` which only works per-process.

Usage:
    from core.distributed_lock import distributed_lock

    async def my_scheduled_job():
        async with distributed_lock.acquire("job:my_job_name", timeout=300) as acquired:
            if not acquired:
                logger.info("Job already running on another instance, skipping")
                return
            # ... job logic ...

Implementation notes:
- Uses Redis SET with NX (only set if not exists) and EX (expire) flags
- Lock auto-expires to prevent deadlocks if a pod crashes
- Non-blocking by default - returns immediately if lock is held
- Thread-safe via Redis atomic operations
"""

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class DistributedLockService:
    """
    Redis-backed distributed lock service.

    Provides advisory locks that work across multiple server instances to prevent
    concurrent execution of background jobs.
    """

    REDIS_KEY_PREFIX = "distributed_lock:"

    def __init__(self) -> None:
        """Initialize the distributed lock service."""
        self._redis: redis.Redis | None = None
        # Unique identifier for this instance to support lock ownership
        self._instance_id = uuid.uuid4().hex

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _get_key(self, lock_name: str) -> str:
        """
        Generate Redis key for the lock.

        Args:
            lock_name: Logical name of the lock (e.g., "job:expire_requests")

        Returns:
            Redis key string
        """
        return f"{self.REDIS_KEY_PREFIX}{lock_name}"

    def _get_lock_value(self) -> str:
        """
        Generate a unique lock value for ownership tracking.

        Returns:
            Unique identifier combining instance ID and a random component
        """
        return f"{self._instance_id}:{uuid.uuid4().hex[:8]}"

    async def try_acquire(
        self,
        lock_name: str,
        timeout: int = 60,
    ) -> tuple[bool, str | None]:
        """
        Try to acquire a distributed lock without blocking.

        Args:
            lock_name: Name of the lock to acquire
            timeout: Lock timeout in seconds (auto-expires to prevent deadlocks)

        Returns:
            Tuple of (acquired: bool, lock_token: str | None)
            lock_token is needed to release the lock and verify ownership
        """
        try:
            r = await self._get_redis()
            key = self._get_key(lock_name)
            lock_token = self._get_lock_value()

            # SET key value NX EX timeout
            # NX - only set if not exists
            # EX - expire after timeout seconds
            acquired = await r.set(key, lock_token, nx=True, ex=timeout)

            if acquired:
                logger.debug(
                    "Acquired distributed lock: %s (timeout=%ds)", lock_name, timeout
                )
                return True, lock_token
            else:
                logger.debug(
                    "Failed to acquire distributed lock: %s (already held)", lock_name
                )
                return False, None

        except Exception as e:
            logger.error("Error acquiring distributed lock %s: %s", lock_name, e)
            # On Redis errors, allow the job to proceed (fail-open)
            # This prevents Redis issues from blocking all job execution
            return True, None

    async def release(self, lock_name: str, lock_token: str | None) -> bool:
        """
        Release a distributed lock.

        Uses Lua script for atomic check-and-delete to prevent releasing
        a lock that was acquired by another instance after our lock expired.

        Args:
            lock_name: Name of the lock to release
            lock_token: Token returned by try_acquire (for ownership verification)

        Returns:
            True if lock was released, False otherwise
        """
        if lock_token is None:
            # Lock was acquired in fail-open mode, nothing to release
            return True

        try:
            r = await self._get_redis()
            key = self._get_key(lock_name)

            # Lua script for atomic check-and-delete
            # Only delete if the lock value matches our token
            release_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """

            result = await r.eval(release_script, 1, key, lock_token)

            if result:
                logger.debug("Released distributed lock: %s", lock_name)
                return True
            else:
                logger.warning(
                    "Could not release lock %s: token mismatch (lock may have expired)",
                    lock_name,
                )
                return False

        except Exception as e:
            logger.error("Error releasing distributed lock %s: %s", lock_name, e)
            return False

    async def is_locked(self, lock_name: str) -> bool:
        """
        Check if a lock is currently held.

        Args:
            lock_name: Name of the lock to check

        Returns:
            True if lock is held, False otherwise
        """
        try:
            r = await self._get_redis()
            key = self._get_key(lock_name)
            return await r.exists(key) > 0
        except Exception as e:
            logger.error("Error checking lock status %s: %s", lock_name, e)
            return False

    async def get_lock_ttl(self, lock_name: str) -> int:
        """
        Get the remaining time-to-live for a lock.

        Args:
            lock_name: Name of the lock

        Returns:
            TTL in seconds, -1 if lock doesn't exist, -2 if no TTL set
        """
        try:
            r = await self._get_redis()
            key = self._get_key(lock_name)
            return await r.ttl(key)
        except Exception as e:
            logger.error("Error getting lock TTL %s: %s", lock_name, e)
            return -1

    @asynccontextmanager
    async def acquire(
        self,
        lock_name: str,
        timeout: int = 60,
    ) -> AsyncIterator[bool]:
        """
        Context manager for acquiring a distributed lock.

        Automatically releases the lock when the context exits.

        Args:
            lock_name: Name of the lock to acquire
            timeout: Lock timeout in seconds (auto-expires to prevent deadlocks)

        Yields:
            True if lock was acquired, False otherwise

        Usage:
            async with distributed_lock.acquire("job:my_job", timeout=300) as acquired:
                if not acquired:
                    logger.info("Job already running, skipping")
                    return
                # ... job logic ...
        """
        acquired, lock_token = await self.try_acquire(lock_name, timeout)
        try:
            yield acquired
        finally:
            if acquired:
                await self.release(lock_name, lock_token)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
distributed_lock = DistributedLockService()
