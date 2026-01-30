"""Tests for the feature flags system."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.feature_flags import (
    DEFAULT_FLAGS,
    FeatureFlag,
    FeatureFlags,
    FeatureState,
    feature_flags,
    init_default_flags,
)


class TestFeatureState:
    """Tests for FeatureState enum."""

    def test_feature_states_exist(self):
        """Test all expected feature states exist."""
        assert FeatureState.DISABLED == "disabled"
        assert FeatureState.ENABLED == "enabled"
        assert FeatureState.PERCENTAGE == "percentage"
        assert FeatureState.ALLOWLIST == "allowlist"
        assert FeatureState.DENYLIST == "denylist"

    def test_feature_state_is_string_enum(self):
        """Test FeatureState values are strings."""
        for state in FeatureState:
            assert isinstance(state.value, str)


class TestFeatureFlag:
    """Tests for FeatureFlag dataclass."""

    def test_create_basic_flag(self):
        """Test creating a basic feature flag."""
        flag = FeatureFlag(name="test_feature")
        assert flag.name == "test_feature"
        assert flag.state == FeatureState.DISABLED
        assert flag.percentage == 0
        assert flag.allowlist == []
        assert flag.denylist == []
        assert flag.description == ""
        assert flag.metadata == {}

    def test_create_flag_with_all_fields(self):
        """Test creating a feature flag with all fields."""
        now = datetime.utcnow()
        flag = FeatureFlag(
            name="full_feature",
            state=FeatureState.PERCENTAGE,
            percentage=50,
            allowlist=["user1", "user2"],
            denylist=["user3"],
            description="A test feature",
            created_at=now,
            updated_at=now,
            metadata={"team": "backend"},
        )
        assert flag.name == "full_feature"
        assert flag.state == FeatureState.PERCENTAGE
        assert flag.percentage == 50
        assert flag.allowlist == ["user1", "user2"]
        assert flag.denylist == ["user3"]
        assert flag.description == "A test feature"
        assert flag.metadata == {"team": "backend"}

    def test_to_dict(self):
        """Test converting feature flag to dictionary."""
        now = datetime.utcnow()
        flag = FeatureFlag(
            name="test",
            state=FeatureState.ENABLED,
            description="Test flag",
            created_at=now,
            updated_at=now,
        )
        data = flag.to_dict()

        assert data["name"] == "test"
        assert data["state"] == "enabled"
        assert data["description"] == "Test flag"
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        assert data["percentage"] == 0
        assert data["allowlist"] == []
        assert data["denylist"] == []

    def test_to_dict_without_timestamps(self):
        """Test to_dict with None timestamps."""
        flag = FeatureFlag(name="test")
        data = flag.to_dict()
        assert data["created_at"] is None
        assert data["updated_at"] is None

    def test_from_dict(self):
        """Test creating feature flag from dictionary."""
        now = datetime.utcnow()
        data = {
            "name": "from_dict_feature",
            "state": "percentage",
            "percentage": 75,
            "allowlist": ["user1"],
            "denylist": ["user2"],
            "description": "From dict",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "metadata": {"key": "value"},
        }
        flag = FeatureFlag.from_dict(data)

        assert flag.name == "from_dict_feature"
        assert flag.state == FeatureState.PERCENTAGE
        assert flag.percentage == 75
        assert flag.allowlist == ["user1"]
        assert flag.denylist == ["user2"]
        assert flag.description == "From dict"
        assert flag.metadata == {"key": "value"}

    def test_from_dict_minimal(self):
        """Test from_dict with minimal data."""
        data = {"name": "minimal"}
        flag = FeatureFlag.from_dict(data)

        assert flag.name == "minimal"
        assert flag.state == FeatureState.DISABLED
        assert flag.percentage == 0
        assert flag.allowlist == []
        assert flag.denylist == []

    def test_roundtrip_conversion(self):
        """Test converting to dict and back preserves data."""
        now = datetime.utcnow()
        original = FeatureFlag(
            name="roundtrip",
            state=FeatureState.ALLOWLIST,
            allowlist=["user1", "user2"],
            description="Roundtrip test",
            created_at=now,
            updated_at=now,
        )

        data = original.to_dict()
        restored = FeatureFlag.from_dict(data)

        assert restored.name == original.name
        assert restored.state == original.state
        assert restored.allowlist == original.allowlist
        assert restored.description == original.description


class TestFeatureFlags:
    """Tests for FeatureFlags manager class."""

    @pytest.fixture
    def ff_manager(self):
        """Create a fresh FeatureFlags instance for testing."""
        manager = FeatureFlags()
        manager._local_cache.clear()
        return manager

    def test_get_key(self, ff_manager):
        """Test Redis key generation."""
        key = ff_manager._get_key("my_feature")
        assert key == "feature_flags:my_feature"

    def test_user_in_percentage_zero(self, ff_manager):
        """Test percentage check with 0%."""
        assert ff_manager._user_in_percentage("user1", 0) is False
        assert ff_manager._user_in_percentage("any_user", 0) is False

    def test_user_in_percentage_hundred(self, ff_manager):
        """Test percentage check with 100%."""
        assert ff_manager._user_in_percentage("user1", 100) is True
        assert ff_manager._user_in_percentage("any_user", 100) is True

    def test_user_in_percentage_consistent(self, ff_manager):
        """Test percentage rollout is consistent for same user."""
        user_id = "consistent_user_123"
        results = [ff_manager._user_in_percentage(user_id, 50) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_user_in_percentage_distribution(self, ff_manager):
        """Test percentage rollout roughly matches expected distribution."""
        in_rollout = sum(
            1 for i in range(1000) if ff_manager._user_in_percentage(f"user_{i}", 50)
        )
        assert 400 < in_rollout < 600

    @pytest.mark.asyncio
    async def test_get_flag_not_found(self, ff_manager):
        """Test getting a non-existent flag."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            result = await ff_manager.get_flag("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_flag_from_redis(self, ff_manager):
        """Test getting a flag from Redis."""
        flag_data = {
            "name": "redis_flag",
            "state": "enabled",
            "percentage": 0,
            "allowlist": [],
            "denylist": [],
            "description": "From Redis",
            "created_at": None,
            "updated_at": None,
            "metadata": {},
        }
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(flag_data)

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            result = await ff_manager.get_flag("redis_flag")
            assert result is not None
            assert result.name == "redis_flag"
            assert result.state == FeatureState.ENABLED

    @pytest.mark.asyncio
    async def test_get_flag_uses_cache(self, ff_manager):
        """Test that cache is used for subsequent calls."""
        flag = FeatureFlag(name="cached_flag", state=FeatureState.ENABLED)
        ff_manager._local_cache["cached_flag"] = (flag, datetime.utcnow())

        mock_redis = AsyncMock()
        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            result = await ff_manager.get_flag("cached_flag")
            assert result.name == "cached_flag"
            mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_flag(self, ff_manager):
        """Test setting a flag."""
        mock_redis = AsyncMock()

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            flag = FeatureFlag(name="new_flag", state=FeatureState.ENABLED)
            await ff_manager.set_flag(flag)

            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert "feature_flags:new_flag" in call_args[0]

    @pytest.mark.asyncio
    async def test_set_flag_invalidates_cache(self, ff_manager):
        """Test that setting a flag invalidates the cache."""
        ff_manager._local_cache["cached"] = (
            FeatureFlag(name="cached"),
            datetime.utcnow(),
        )
        mock_redis = AsyncMock()

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            flag = FeatureFlag(name="cached", state=FeatureState.ENABLED)
            await ff_manager.set_flag(flag)

            assert "cached" not in ff_manager._local_cache

    @pytest.mark.asyncio
    async def test_delete_flag(self, ff_manager):
        """Test deleting a flag."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 1

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            result = await ff_manager.delete_flag("delete_me")
            assert result is True
            mock_redis.delete.assert_called_with("feature_flags:delete_me")

    @pytest.mark.asyncio
    async def test_delete_flag_not_found(self, ff_manager):
        """Test deleting a non-existent flag."""
        mock_redis = AsyncMock()
        mock_redis.delete.return_value = 0

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            result = await ff_manager.delete_flag("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_list_flags(self, ff_manager):
        """Test listing all flags."""
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["feature_flags:flag1", "feature_flags:flag2"]
        mock_redis.get.side_effect = [
            json.dumps({"name": "flag1", "state": "enabled"}),
            json.dumps({"name": "flag2", "state": "disabled"}),
        ]

        with patch.object(ff_manager, "_get_redis", return_value=mock_redis):
            flags = await ff_manager.list_flags()
            assert len(flags) == 2
            assert flags[0].name == "flag1"
            assert flags[1].name == "flag2"

    @pytest.mark.asyncio
    async def test_is_enabled_true(self, ff_manager):
        """Test is_enabled returns True for enabled flag."""
        flag = FeatureFlag(name="enabled_flag", state=FeatureState.ENABLED)
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled("enabled_flag") is True

    @pytest.mark.asyncio
    async def test_is_enabled_false_for_disabled(self, ff_manager):
        """Test is_enabled returns False for disabled flag."""
        flag = FeatureFlag(name="disabled_flag", state=FeatureState.DISABLED)
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled("disabled_flag") is False

    @pytest.mark.asyncio
    async def test_is_enabled_false_for_percentage(self, ff_manager):
        """Test is_enabled returns False for percentage flag."""
        flag = FeatureFlag(name="percentage_flag", state=FeatureState.PERCENTAGE)
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled("percentage_flag") is False

    @pytest.mark.asyncio
    async def test_is_enabled_false_for_nonexistent(self, ff_manager):
        """Test is_enabled returns False for non-existent flag."""
        with patch.object(ff_manager, "get_flag", return_value=None):
            assert await ff_manager.is_enabled("nonexistent") is False

    @pytest.mark.asyncio
    async def test_is_enabled_for_user_disabled(self, ff_manager):
        """Test is_enabled_for_user with disabled flag."""
        flag = FeatureFlag(name="disabled", state=FeatureState.DISABLED)
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled_for_user("disabled", "user1") is False

    @pytest.mark.asyncio
    async def test_is_enabled_for_user_enabled(self, ff_manager):
        """Test is_enabled_for_user with enabled flag."""
        flag = FeatureFlag(name="enabled", state=FeatureState.ENABLED)
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled_for_user("enabled", "user1") is True

    @pytest.mark.asyncio
    async def test_is_enabled_for_user_allowlist_included(self, ff_manager):
        """Test is_enabled_for_user with user in allowlist."""
        flag = FeatureFlag(
            name="allowlist", state=FeatureState.ALLOWLIST, allowlist=["user1", "user2"]
        )
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled_for_user("allowlist", "user1") is True
            assert await ff_manager.is_enabled_for_user("allowlist", "user3") is False

    @pytest.mark.asyncio
    async def test_is_enabled_for_user_denylist(self, ff_manager):
        """Test is_enabled_for_user with denylist."""
        flag = FeatureFlag(
            name="denylist", state=FeatureState.DENYLIST, denylist=["user1"]
        )
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled_for_user("denylist", "user1") is False
            assert await ff_manager.is_enabled_for_user("denylist", "user2") is True

    @pytest.mark.asyncio
    async def test_is_enabled_for_user_percentage_no_user(self, ff_manager):
        """Test is_enabled_for_user with percentage and no user."""
        flag = FeatureFlag(
            name="percentage", state=FeatureState.PERCENTAGE, percentage=50
        )
        with patch.object(ff_manager, "get_flag", return_value=flag):
            assert await ff_manager.is_enabled_for_user("percentage", None) is False
            assert await ff_manager.is_enabled_for_user("percentage", "") is False

    @pytest.mark.asyncio
    async def test_enable_feature(self, ff_manager):
        """Test enabling a feature."""
        with patch.object(ff_manager, "get_flag", return_value=None):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.enable("new_feature", "Test description")
                assert result.state == FeatureState.ENABLED
                assert result.description == "Test description"
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_disable_feature(self, ff_manager):
        """Test disabling a feature."""
        existing = FeatureFlag(name="existing", state=FeatureState.ENABLED)
        with patch.object(ff_manager, "get_flag", return_value=existing):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.disable("existing")
                assert result.state == FeatureState.DISABLED
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_percentage(self, ff_manager):
        """Test setting percentage rollout."""
        with patch.object(ff_manager, "get_flag", return_value=None):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.set_percentage("feature", 25)
                assert result.state == FeatureState.PERCENTAGE
                assert result.percentage == 25
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_percentage_invalid(self, ff_manager):
        """Test setting invalid percentage."""
        with pytest.raises(ValueError, match="Percentage must be between"):
            await ff_manager.set_percentage("feature", -1)

        with pytest.raises(ValueError, match="Percentage must be between"):
            await ff_manager.set_percentage("feature", 101)

    @pytest.mark.asyncio
    async def test_add_to_allowlist(self, ff_manager):
        """Test adding users to allowlist."""
        existing = FeatureFlag(
            name="allowlist", state=FeatureState.ALLOWLIST, allowlist=["user1"]
        )
        with patch.object(ff_manager, "get_flag", return_value=existing):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.add_to_allowlist("allowlist", ["user2"])
                assert "user1" in result.allowlist
                assert "user2" in result.allowlist
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_from_allowlist(self, ff_manager):
        """Test removing users from allowlist."""
        existing = FeatureFlag(
            name="allowlist",
            state=FeatureState.ALLOWLIST,
            allowlist=["user1", "user2"],
        )
        with patch.object(ff_manager, "get_flag", return_value=existing):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.remove_from_allowlist("allowlist", ["user1"])
                assert "user1" not in result.allowlist
                assert "user2" in result.allowlist
                mock_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_from_allowlist_not_found(self, ff_manager):
        """Test removing from non-existent flag."""
        with patch.object(ff_manager, "get_flag", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await ff_manager.remove_from_allowlist("nonexistent", ["user1"])

    @pytest.mark.asyncio
    async def test_add_to_denylist(self, ff_manager):
        """Test adding users to denylist."""
        with patch.object(ff_manager, "get_flag", return_value=None):
            with patch.object(ff_manager, "set_flag") as mock_set:
                result = await ff_manager.add_to_denylist("denylist", ["user1"])
                assert result.state == FeatureState.DENYLIST
                assert "user1" in result.denylist
                mock_set.assert_called_once()

    def test_invalidate_cache_specific(self, ff_manager):
        """Test invalidating specific cache entry."""
        ff_manager._local_cache["flag1"] = (
            FeatureFlag(name="flag1"),
            datetime.utcnow(),
        )
        ff_manager._local_cache["flag2"] = (
            FeatureFlag(name="flag2"),
            datetime.utcnow(),
        )

        ff_manager.invalidate_cache("flag1")

        assert "flag1" not in ff_manager._local_cache
        assert "flag2" in ff_manager._local_cache

    def test_invalidate_cache_all(self, ff_manager):
        """Test invalidating all cache entries."""
        ff_manager._local_cache["flag1"] = (
            FeatureFlag(name="flag1"),
            datetime.utcnow(),
        )
        ff_manager._local_cache["flag2"] = (
            FeatureFlag(name="flag2"),
            datetime.utcnow(),
        )

        ff_manager.invalidate_cache()

        assert len(ff_manager._local_cache) == 0

    @pytest.mark.asyncio
    async def test_close(self, ff_manager):
        """Test closing Redis connection."""
        mock_redis = AsyncMock()
        ff_manager._redis = mock_redis

        await ff_manager.close()

        mock_redis.close.assert_called_once()
        assert ff_manager._redis is None


class TestDefaultFlags:
    """Tests for default feature flags."""

    def test_default_flags_exist(self):
        """Test default flags are defined."""
        assert len(DEFAULT_FLAGS) > 0

    def test_default_flags_are_disabled(self):
        """Test default flags start disabled."""
        for flag in DEFAULT_FLAGS:
            assert flag.state == FeatureState.DISABLED

    def test_default_flags_have_descriptions(self):
        """Test default flags have descriptions."""
        for flag in DEFAULT_FLAGS:
            assert flag.description, f"Flag {flag.name} missing description"

    def test_expected_default_flags(self):
        """Test expected default flags are present."""
        flag_names = [f.name for f in DEFAULT_FLAGS]
        expected = [
            "new_booking_flow",
            "ai_tutor_matching",
            "instant_booking",
            "video_sessions",
            "group_sessions",
        ]
        for name in expected:
            assert name in flag_names, f"Expected default flag '{name}' not found"


class TestInitDefaultFlags:
    """Tests for init_default_flags function."""

    @pytest.mark.asyncio
    async def test_init_creates_missing_flags(self):
        """Test init creates flags that don't exist."""
        with patch.object(feature_flags, "get_flag", return_value=None):
            with patch.object(feature_flags, "set_flag") as mock_set:
                await init_default_flags()
                assert mock_set.call_count == len(DEFAULT_FLAGS)

    @pytest.mark.asyncio
    async def test_init_skips_existing_flags(self):
        """Test init doesn't overwrite existing flags."""
        existing = FeatureFlag(name="existing", state=FeatureState.ENABLED)
        with patch.object(feature_flags, "get_flag", return_value=existing):
            with patch.object(feature_flags, "set_flag") as mock_set:
                await init_default_flags()
                mock_set.assert_not_called()
