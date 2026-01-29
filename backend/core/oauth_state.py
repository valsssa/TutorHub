"""
OAuth State Storage

Redis-backed storage for OAuth state tokens with automatic expiration.
Provides CSRF protection for OAuth flows and works across multiple backend instances.

Usage:
    from core.oauth_state import oauth_state_store

    # Generate state token for OAuth flow
    state = await oauth_state_store.generate_state(
        action="login",
        user_id=123,  # optional
        extra_data={"redirect_uri": "/dashboard"}  # optional
    )

    # Validate and consume state token (one-time use)
    data = await oauth_state_store.validate_state(state)
    if data:
        action = data["action"]
        user_id = data.get("user_id")
"""

import json
import logging
import secrets
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

from core.config import settings

logger = logging.getLogger(__name__)


# OAuth state TTL in seconds (10 minutes)
OAUTH_STATE_TTL_SECONDS = 600


class OAuthStateStore:
    """
    Redis-backed OAuth state storage with TTL and one-time use.

    Features:
    - Distributed storage works with multiple backend instances
    - Automatic expiration via Redis TTL (10 minutes)
    - One-time use (state deleted after validation)
    - Graceful degradation to in-memory storage if Redis unavailable
    """

    REDIS_PREFIX = "oauth_state:"

    def __init__(self) -> None:
        """Initialize OAuth state store."""
        self._redis: redis.Redis | None = None
        self._redis_available: bool | None = None
        # Fallback in-memory storage (only used if Redis is unavailable)
        self._fallback_states: dict[str, dict[str, Any]] = {}

    async def _get_redis(self) -> redis.Redis | None:
        """Get Redis connection, or None if unavailable."""
        if self._redis_available is False:
            return None

        if self._redis is None:
            try:
                self._redis = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self._redis.ping()
                self._redis_available = True
                logger.info("OAuth state store connected to Redis")
            except Exception as e:
                logger.warning(
                    f"Redis unavailable for OAuth state storage, using in-memory fallback: {e}"
                )
                self._redis_available = False
                self._redis = None
                return None

        return self._redis

    def _get_key(self, state: str) -> str:
        """Get Redis key for OAuth state token."""
        return f"{self.REDIS_PREFIX}{state}"

    async def generate_state(
        self,
        action: str,
        user_id: int | None = None,
        extra_data: dict[str, Any] | None = None,
    ) -> str:
        """
        Generate a new OAuth state token.

        Args:
            action: The OAuth action (e.g., "login", "link", "calendar_connect")
            user_id: Optional user ID for account linking operations
            extra_data: Optional additional data to store with the state

        Returns:
            The generated state token (URL-safe, 32 bytes)
        """
        state = secrets.token_urlsafe(32)

        data: dict[str, Any] = {
            "action": action,
            "user_id": user_id,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if extra_data:
            data.update(extra_data)

        r = await self._get_redis()
        if r:
            try:
                await r.setex(
                    self._get_key(state),
                    OAUTH_STATE_TTL_SECONDS,
                    json.dumps(data),
                )
                logger.debug(f"OAuth state stored in Redis: action={action}")
                return state
            except Exception as e:
                logger.error(f"Failed to store OAuth state in Redis: {e}")
                # Fall through to in-memory fallback

        # In-memory fallback
        self._fallback_states[state] = data
        self._cleanup_expired_fallback_states()
        logger.debug(f"OAuth state stored in memory (fallback): action={action}")
        return state

    async def validate_state(self, state: str) -> dict[str, Any] | None:
        """
        Validate and consume an OAuth state token.

        The state is deleted after successful validation (one-time use).

        Args:
            state: The state token to validate

        Returns:
            The stored state data, or None if invalid/expired
        """
        if not state:
            return None

        r = await self._get_redis()
        if r:
            try:
                key = self._get_key(state)
                data = await r.get(key)
                if data:
                    # Delete immediately (one-time use)
                    await r.delete(key)
                    logger.debug("OAuth state validated and consumed from Redis")
                    return json.loads(data)
                logger.warning("OAuth state not found in Redis (expired or invalid)")
                return None
            except Exception as e:
                logger.error(f"Failed to validate OAuth state from Redis: {e}")
                # Fall through to in-memory fallback

        # In-memory fallback
        if state in self._fallback_states:
            data = self._fallback_states.pop(state)
            # Check expiration
            created_at = datetime.fromisoformat(data["created_at"])
            age_seconds = (datetime.now(UTC) - created_at).total_seconds()
            if age_seconds > OAUTH_STATE_TTL_SECONDS:
                logger.warning("OAuth state expired (in-memory fallback)")
                return None
            logger.debug("OAuth state validated and consumed from memory (fallback)")
            return data

        logger.warning("OAuth state not found (expired or invalid)")
        return None

    def _cleanup_expired_fallback_states(self) -> None:
        """Clean up expired states from in-memory fallback storage."""
        now = datetime.now(UTC)
        expired = []
        for state, data in self._fallback_states.items():
            created_at = datetime.fromisoformat(data["created_at"])
            age_seconds = (now - created_at).total_seconds()
            if age_seconds > OAUTH_STATE_TTL_SECONDS:
                expired.append(state)

        for state in expired:
            del self._fallback_states[state]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired OAuth states (fallback)")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
oauth_state_store = OAuthStateStore()
