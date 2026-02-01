"""
Account Lockout Service

Provides brute-force protection by tracking failed login attempts per email/account
and temporarily locking accounts after too many failed attempts.

This complements the existing IP-based rate limiting by adding account-level protection,
which prevents distributed attacks from multiple IPs against a single account.

Usage:
    from core.account_lockout import account_lockout

    # Check if account is locked before authentication
    if await account_lockout.is_locked(email):
        raise HTTPException(429, "Account temporarily locked")

    # Record failed attempt after authentication failure
    await account_lockout.record_failed_attempt(email)

    # Clear attempts after successful login
    await account_lockout.clear_failed_attempts(email)
"""

import logging

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


class AccountLockoutService:
    """
    Redis-backed account lockout service for brute-force protection.

    Tracks failed login attempts per email address and locks accounts
    after exceeding the maximum allowed attempts within the lockout window.
    """

    REDIS_KEY_PREFIX = "login_attempts:"

    def __init__(self) -> None:
        """Initialize the account lockout service."""
        self._redis: redis.Redis | None = None

    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _get_key(self, email: str) -> str:
        """
        Generate Redis key for tracking login attempts.

        Args:
            email: User email address (normalized to lowercase)

        Returns:
            Redis key string
        """
        normalized_email = email.lower().strip()
        return f"{self.REDIS_KEY_PREFIX}{normalized_email}"

    async def is_locked(self, email: str) -> bool:
        """
        Check if an account is currently locked due to too many failed attempts.

        Args:
            email: User email address

        Returns:
            True if account is locked, False otherwise
        """
        try:
            r = await self._get_redis()
            key = self._get_key(email)
            attempts = await r.get(key)

            if attempts is None:
                return False

            attempt_count = int(attempts)
            is_locked = attempt_count >= settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS

            if is_locked:
                logger.warning(
                    f"Account locked due to {attempt_count} failed attempts: {email}"
                )

            return is_locked

        except Exception as e:
            logger.error(f"Error checking account lockout for {email}: {e}")
            return False

    async def record_failed_attempt(self, email: str) -> int:
        """
        Record a failed login attempt for an account.

        Increments the failure counter and sets/refreshes the TTL.
        The counter will automatically expire after the lockout duration.

        Args:
            email: User email address

        Returns:
            Current number of failed attempts
        """
        try:
            r = await self._get_redis()
            key = self._get_key(email)

            pipe = r.pipeline()
            pipe.incr(key)
            pipe.expire(key, settings.ACCOUNT_LOCKOUT_DURATION_SECONDS)
            results = await pipe.execute()

            attempt_count = results[0]

            logger.info(
                f"Failed login attempt recorded for {email}: "
                f"{attempt_count}/{settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS}"
            )

            if attempt_count >= settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
                logger.warning(
                    f"Account locked after {attempt_count} failed attempts: {email}"
                )

            return attempt_count

        except Exception as e:
            logger.error(f"Error recording failed attempt for {email}: {e}")
            return 0

    async def clear_failed_attempts(self, email: str) -> bool:
        """
        Clear failed login attempts after successful authentication.

        Args:
            email: User email address

        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            r = await self._get_redis()
            key = self._get_key(email)
            result = await r.delete(key)

            if result > 0:
                logger.debug(f"Cleared failed login attempts for {email}")

            return result > 0

        except Exception as e:
            logger.error(f"Error clearing failed attempts for {email}: {e}")
            return False

    async def get_remaining_attempts(self, email: str) -> int:
        """
        Get the number of remaining login attempts before lockout.

        Args:
            email: User email address

        Returns:
            Number of remaining attempts (0 if locked)
        """
        try:
            r = await self._get_redis()
            key = self._get_key(email)
            attempts = await r.get(key)

            if attempts is None:
                return settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS

            attempt_count = int(attempts)
            remaining = max(0, settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS - attempt_count)

            return remaining

        except Exception as e:
            logger.error(f"Error getting remaining attempts for {email}: {e}")
            return settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS

    async def get_lockout_ttl(self, email: str) -> int:
        """
        Get the remaining time in seconds until the lockout expires.

        Args:
            email: User email address

        Returns:
            Remaining seconds until lockout expires, or -1 if not locked
        """
        try:
            r = await self._get_redis()
            key = self._get_key(email)
            ttl = await r.ttl(key)

            return max(0, ttl) if ttl > 0 else -1

        except Exception as e:
            logger.error(f"Error getting lockout TTL for {email}: {e}")
            return -1

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
account_lockout = AccountLockoutService()
