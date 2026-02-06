"""
Feature Flags System

Simple Redis-backed feature flags for gradual rollouts and feature toggles.

Usage:
    from core.feature_flags import feature_flags

    # Check if feature is enabled globally
    if await feature_flags.is_enabled("new_booking_flow"):
        # New code path
        pass

    # Check for specific user (percentage rollout)
    if await feature_flags.is_enabled_for_user("new_booking_flow", user_id):
        # New code path for this user
        pass

Admin API:
    POST /api/v1/admin/features/{name}/enable
    POST /api/v1/admin/features/{name}/disable
    GET /api/v1/admin/features
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import redis.asyncio as redis

from core.config import settings
from core.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class FeatureState(str, Enum):
    """Feature flag states."""

    DISABLED = "disabled"  # Off for everyone
    ENABLED = "enabled"  # On for everyone
    PERCENTAGE = "percentage"  # On for X% of users
    ALLOWLIST = "allowlist"  # On for specific users only
    DENYLIST = "denylist"  # On for everyone except specific users


@dataclass
class FeatureFlag:
    """Feature flag configuration."""

    name: str
    state: FeatureState = FeatureState.DISABLED
    percentage: int = 0  # 0-100, used when state is PERCENTAGE
    allowlist: list[str] = field(default_factory=list)  # User IDs when ALLOWLIST
    denylist: list[str] = field(default_factory=list)  # User IDs when DENYLIST
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "state": self.state.value,
            "percentage": self.percentage,
            "allowlist": self.allowlist,
            "denylist": self.denylist,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureFlag":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            state=FeatureState(data.get("state", "disabled")),
            percentage=data.get("percentage", 0),
            allowlist=data.get("allowlist", []),
            denylist=data.get("denylist", []),
            description=data.get("description", ""),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
            metadata=data.get("metadata", {}),
        )


class FeatureFlags:
    """Feature flag manager with Redis backend."""

    REDIS_PREFIX = "feature_flags:"
    CACHE_TTL = 60  # Cache flags for 60 seconds

    def __init__(self):
        """Initialize feature flags manager."""
        self._redis: redis.Redis | None = None
        self._local_cache: dict[str, tuple[FeatureFlag, datetime]] = {}

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    def _get_key(self, name: str) -> str:
        """Get Redis key for feature flag."""
        return f"{self.REDIS_PREFIX}{name}"

    def _user_in_percentage(self, user_id: str, percentage: int) -> bool:
        """
        Determine if user falls within percentage rollout.

        Uses consistent hashing so the same user always gets
        the same result for the same feature.
        """
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Create consistent hash from user_id
        hash_input = f"{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        user_percentage = hash_value % 100

        return user_percentage < percentage

    async def get_flag(self, name: str) -> FeatureFlag | None:
        """
        Get feature flag by name.

        Uses local cache to reduce Redis calls.
        """
        # Check local cache
        if name in self._local_cache:
            flag, cached_at = self._local_cache[name]
            age = (utc_now() - cached_at).total_seconds()
            if age < self.CACHE_TTL:
                return flag

        # Fetch from Redis
        try:
            r = await self._get_redis()
            data = await r.get(self._get_key(name))
            if data:
                flag = FeatureFlag.from_dict(json.loads(data))
                self._local_cache[name] = (flag, utc_now())
                return flag
        except Exception as e:
            logger.error(f"Error fetching feature flag {name}: {e}")

        return None

    async def set_flag(self, flag: FeatureFlag) -> None:
        """Save feature flag to Redis."""
        try:
            flag.updated_at = utc_now()
            if flag.created_at is None:
                flag.created_at = flag.updated_at

            r = await self._get_redis()
            await r.set(self._get_key(flag.name), json.dumps(flag.to_dict()))

            # Invalidate local cache
            self._local_cache.pop(flag.name, None)

            logger.info(f"Feature flag '{flag.name}' set to {flag.state.value}")
        except Exception as e:
            logger.error(f"Error saving feature flag {flag.name}: {e}")
            raise

    async def delete_flag(self, name: str) -> bool:
        """Delete feature flag."""
        try:
            r = await self._get_redis()
            result = await r.delete(self._get_key(name))
            self._local_cache.pop(name, None)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting feature flag {name}: {e}")
            return False

    async def list_flags(self) -> list[FeatureFlag]:
        """List all feature flags."""
        try:
            r = await self._get_redis()
            keys = await r.keys(f"{self.REDIS_PREFIX}*")
            flags = []
            for key in keys:
                data = await r.get(key)
                if data:
                    flags.append(FeatureFlag.from_dict(json.loads(data)))
            return sorted(flags, key=lambda f: f.name)
        except Exception as e:
            logger.error(f"Error listing feature flags: {e}")
            return []

    async def is_enabled(self, name: str) -> bool:
        """
        Check if feature is globally enabled.

        Returns False for PERCENTAGE, ALLOWLIST, or DENYLIST states
        since those require user context.
        """
        flag = await self.get_flag(name)
        if flag is None:
            return False

        return flag.state == FeatureState.ENABLED

    async def is_enabled_for_user(
        self, name: str, user_id: str | int | None
    ) -> bool:
        """
        Check if feature is enabled for specific user.

        Handles all feature states including percentage rollouts
        and allow/deny lists.
        """
        flag = await self.get_flag(name)
        if flag is None:
            return False

        user_id_str = str(user_id) if user_id else ""

        match flag.state:
            case FeatureState.DISABLED:
                return False

            case FeatureState.ENABLED:
                return True

            case FeatureState.PERCENTAGE:
                if not user_id_str:
                    return False
                return self._user_in_percentage(user_id_str, flag.percentage)

            case FeatureState.ALLOWLIST:
                return user_id_str in flag.allowlist

            case FeatureState.DENYLIST:
                return user_id_str not in flag.denylist

        return False

    # Convenience methods for common operations

    async def enable(self, name: str, description: str = "") -> FeatureFlag:
        """Enable a feature for everyone."""
        existing = await self.get_flag(name)
        flag = existing or FeatureFlag(name=name)
        flag.state = FeatureState.ENABLED
        if description:
            flag.description = description
        await self.set_flag(flag)
        return flag

    async def disable(self, name: str) -> FeatureFlag:
        """Disable a feature for everyone."""
        existing = await self.get_flag(name)
        flag = existing or FeatureFlag(name=name)
        flag.state = FeatureState.DISABLED
        await self.set_flag(flag)
        return flag

    async def set_percentage(
        self, name: str, percentage: int, description: str = ""
    ) -> FeatureFlag:
        """Set feature to percentage rollout."""
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")

        existing = await self.get_flag(name)
        flag = existing or FeatureFlag(name=name)
        flag.state = FeatureState.PERCENTAGE
        flag.percentage = percentage
        if description:
            flag.description = description
        await self.set_flag(flag)
        return flag

    async def add_to_allowlist(
        self, name: str, user_ids: list[str]
    ) -> FeatureFlag:
        """Add users to allowlist."""
        existing = await self.get_flag(name)
        flag = existing or FeatureFlag(name=name)
        flag.state = FeatureState.ALLOWLIST
        flag.allowlist = list(set(flag.allowlist + user_ids))
        await self.set_flag(flag)
        return flag

    async def remove_from_allowlist(
        self, name: str, user_ids: list[str]
    ) -> FeatureFlag:
        """Remove users from allowlist."""
        flag = await self.get_flag(name)
        if flag:
            flag.allowlist = [u for u in flag.allowlist if u not in user_ids]
            await self.set_flag(flag)
            return flag
        raise ValueError(f"Feature flag '{name}' not found")

    async def add_to_denylist(
        self, name: str, user_ids: list[str]
    ) -> FeatureFlag:
        """Add users to denylist."""
        existing = await self.get_flag(name)
        flag = existing or FeatureFlag(name=name)
        flag.state = FeatureState.DENYLIST
        flag.denylist = list(set(flag.denylist + user_ids))
        await self.set_flag(flag)
        return flag

    def invalidate_cache(self, name: str | None = None) -> None:
        """
        Invalidate local cache.

        Args:
            name: Specific flag to invalidate, or None for all
        """
        if name:
            self._local_cache.pop(name, None)
        else:
            self._local_cache.clear()

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton instance
feature_flags = FeatureFlags()


# Default flags to initialize on startup
DEFAULT_FLAGS: list[FeatureFlag] = [
    FeatureFlag(
        name="new_booking_flow",
        state=FeatureState.DISABLED,
        description="New booking UI and flow",
    ),
    FeatureFlag(
        name="ai_tutor_matching",
        state=FeatureState.DISABLED,
        description="AI-powered tutor recommendations",
    ),
    FeatureFlag(
        name="instant_booking",
        state=FeatureState.DISABLED,
        description="Skip tutor confirmation for instant bookings",
    ),
    FeatureFlag(
        name="video_sessions",
        state=FeatureState.DISABLED,
        description="In-app video sessions (vs Zoom)",
    ),
    FeatureFlag(
        name="group_sessions",
        state=FeatureState.DISABLED,
        description="Multi-student group sessions",
    ),
]


async def init_default_flags() -> None:
    """Initialize default feature flags if they don't exist."""
    for default_flag in DEFAULT_FLAGS:
        existing = await feature_flags.get_flag(default_flag.name)
        if existing is None:
            await feature_flags.set_flag(default_flag)
            logger.info(f"Initialized default feature flag: {default_flag.name}")
