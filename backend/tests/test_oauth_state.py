"""Tests for the OAuth state storage."""

import json
from datetime import datetime, timedelta

from core.datetime_utils import utc_now
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.oauth_state import (
    OAUTH_STATE_TTL_SECONDS,
    OAuthStateStore,
    oauth_state_store,
)


class TestOAuthStateStore:
    """Tests for OAuthStateStore class."""

    @pytest.fixture
    def store(self):
        """Create a fresh OAuthStateStore for testing."""
        store = OAuthStateStore()
        store._fallback_states.clear()
        return store

    def test_init(self, store):
        """Test store initialization."""
        assert store._redis is None
        assert store._redis_available is None
        assert store._fallback_states == {}

    def test_get_key(self, store):
        """Test Redis key generation."""
        key = store._get_key("test_state_123")
        assert key == "oauth_state:test_state_123"

    @pytest.mark.asyncio
    async def test_generate_state_with_redis(self, store):
        """Test state generation with Redis."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            state = await store.generate_state(action="login")

            assert len(state) > 0
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args[0]
            assert call_args[1] == OAUTH_STATE_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_generate_state_with_user_id(self, store):
        """Test state generation with user ID."""
        mock_redis = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            await store.generate_state(action="link", user_id=123)

            call_args = mock_redis.setex.call_args[0]
            stored_data = json.loads(call_args[2])
            assert stored_data["action"] == "link"
            assert stored_data["user_id"] == 123

    @pytest.mark.asyncio
    async def test_generate_state_with_extra_data(self, store):
        """Test state generation with extra data."""
        mock_redis = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            await store.generate_state(
                action="login", extra_data={"redirect_uri": "/dashboard"}
            )

            call_args = mock_redis.setex.call_args[0]
            stored_data = json.loads(call_args[2])
            assert stored_data["redirect_uri"] == "/dashboard"

    @pytest.mark.asyncio
    async def test_generate_state_fallback_to_memory(self, store):
        """Test state generation falls back to memory when Redis unavailable."""
        with patch.object(store, "_get_redis", return_value=None):
            state = await store.generate_state(action="login")

            assert state in store._fallback_states
            assert store._fallback_states[state]["action"] == "login"

    @pytest.mark.asyncio
    async def test_generate_state_fallback_on_redis_error(self, store):
        """Test state generation falls back on Redis error."""
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis error")

        with patch.object(store, "_get_redis", return_value=mock_redis):
            state = await store.generate_state(action="login")

            assert state in store._fallback_states

    @pytest.mark.asyncio
    async def test_validate_state_with_redis(self, store):
        """Test state validation with Redis."""
        stored_data = {
            "action": "login",
            "user_id": None,
            "created_at": utc_now().isoformat(),
        }
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(stored_data)
        mock_redis.delete = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            result = await store.validate_state("test_state")

            assert result["action"] == "login"
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_state_not_found(self, store):
        """Test state validation when state not found."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch.object(store, "_get_redis", return_value=mock_redis):
            result = await store.validate_state("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_validate_state_empty_input(self, store):
        """Test state validation with empty input."""
        result = await store.validate_state("")
        assert result is None

        result = await store.validate_state(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_state_fallback_valid(self, store):
        """Test state validation from fallback storage."""
        store._fallback_states["test_state"] = {
            "action": "login",
            "created_at": utc_now().isoformat(),
        }

        with patch.object(store, "_get_redis", return_value=None):
            result = await store.validate_state("test_state")

            assert result["action"] == "login"
            assert "test_state" not in store._fallback_states

    @pytest.mark.asyncio
    async def test_validate_state_fallback_expired(self, store):
        """Test state validation when fallback state is expired."""
        expired_time = utc_now() - timedelta(
            seconds=OAUTH_STATE_TTL_SECONDS + 100
        )
        store._fallback_states["test_state"] = {
            "action": "login",
            "created_at": expired_time.isoformat(),
        }

        with patch.object(store, "_get_redis", return_value=None):
            result = await store.validate_state("test_state")

            assert result is None
            assert "test_state" not in store._fallback_states

    @pytest.mark.asyncio
    async def test_validate_state_one_time_use(self, store):
        """Test state can only be used once."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps(
            {
                "action": "login",
                "created_at": utc_now().isoformat(),
            }
        )
        mock_redis.delete = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            result1 = await store.validate_state("test_state")
            assert result1 is not None
            mock_redis.delete.assert_called_once()

    def test_cleanup_expired_fallback_states(self, store):
        """Test cleanup of expired fallback states."""
        now = utc_now()
        expired_time = now - timedelta(seconds=OAUTH_STATE_TTL_SECONDS + 100)

        store._fallback_states["expired1"] = {
            "action": "login",
            "created_at": expired_time.isoformat(),
        }
        store._fallback_states["expired2"] = {
            "action": "login",
            "created_at": expired_time.isoformat(),
        }
        store._fallback_states["valid"] = {
            "action": "login",
            "created_at": now.isoformat(),
        }

        store._cleanup_expired_fallback_states()

        assert "expired1" not in store._fallback_states
        assert "expired2" not in store._fallback_states
        assert "valid" in store._fallback_states

    @pytest.mark.asyncio
    async def test_close(self, store):
        """Test closing Redis connection."""
        mock_redis = AsyncMock()
        store._redis = mock_redis

        await store.close()

        mock_redis.close.assert_called_once()
        assert store._redis is None


class TestGetRedis:
    """Tests for Redis connection handling."""

    @pytest.fixture
    def store(self):
        """Create a fresh store."""
        return OAuthStateStore()

    @pytest.mark.asyncio
    async def test_get_redis_creates_connection(self, store):
        """Test Redis connection is created."""
        with patch("core.oauth_state.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis

            result = await store._get_redis()

            assert result == mock_redis
            assert store._redis_available is True

    @pytest.mark.asyncio
    async def test_get_redis_returns_cached(self, store):
        """Test cached Redis connection is returned."""
        mock_redis = AsyncMock()
        store._redis = mock_redis
        store._redis_available = True

        result = await store._get_redis()

        assert result == mock_redis

    @pytest.mark.asyncio
    async def test_get_redis_returns_none_when_unavailable(self, store):
        """Test None is returned when Redis unavailable."""
        store._redis_available = False

        result = await store._get_redis()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_handles_connection_error(self, store):
        """Test connection error is handled gracefully."""
        with patch("core.oauth_state.redis.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Connection refused")
            mock_from_url.return_value = mock_redis

            result = await store._get_redis()

            assert result is None
            assert store._redis_available is False


class TestStateTokenGeneration:
    """Tests for state token generation."""

    @pytest.fixture
    def store(self):
        """Create a fresh store."""
        return OAuthStateStore()

    @pytest.mark.asyncio
    async def test_state_tokens_are_url_safe(self, store):
        """Test generated state tokens are URL-safe."""
        with patch.object(store, "_get_redis", return_value=None):
            state = await store.generate_state(action="login")

            # URL-safe base64 characters
            valid_chars = set(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            )
            assert all(c in valid_chars for c in state)

    @pytest.mark.asyncio
    async def test_state_tokens_are_unique(self, store):
        """Test generated state tokens are unique."""
        with patch.object(store, "_get_redis", return_value=None):
            states = [await store.generate_state(action="login") for _ in range(100)]
            assert len(set(states)) == 100

    @pytest.mark.asyncio
    async def test_state_includes_timestamp(self, store):
        """Test generated state includes creation timestamp."""
        mock_redis = AsyncMock()

        with patch.object(store, "_get_redis", return_value=mock_redis):
            await store.generate_state(action="login")

            call_args = mock_redis.setex.call_args[0]
            stored_data = json.loads(call_args[2])
            assert "created_at" in stored_data


class TestOAuthStateConstants:
    """Tests for module constants."""

    def test_state_ttl(self):
        """Test state TTL is 10 minutes."""
        assert OAUTH_STATE_TTL_SECONDS == 600


class TestGlobalInstance:
    """Tests for global oauth_state_store instance."""

    def test_singleton_exists(self):
        """Test global instance exists."""
        assert oauth_state_store is not None
        assert isinstance(oauth_state_store, OAuthStateStore)


class TestIntegration:
    """Integration tests for OAuth state flow."""

    @pytest.fixture
    def store(self):
        """Create a fresh store."""
        store = OAuthStateStore()
        store._fallback_states.clear()
        return store

    @pytest.mark.asyncio
    async def test_full_oauth_flow_with_fallback(self, store):
        """Test complete OAuth flow using fallback storage."""
        with patch.object(store, "_get_redis", return_value=None):
            state = await store.generate_state(
                action="calendar_connect",
                user_id=123,
                extra_data={"redirect_uri": "/settings"},
            )

            result = await store.validate_state(state)

            assert result["action"] == "calendar_connect"
            assert result["user_id"] == 123
            assert result["redirect_uri"] == "/settings"

            result2 = await store.validate_state(state)
            assert result2 is None

    @pytest.mark.asyncio
    async def test_multiple_states_independent(self, store):
        """Test multiple states are independent."""
        with patch.object(store, "_get_redis", return_value=None):
            state1 = await store.generate_state(action="login")
            state2 = await store.generate_state(action="link", user_id=456)

            result1 = await store.validate_state(state1)
            result2 = await store.validate_state(state2)

            assert result1["action"] == "login"
            assert result2["action"] == "link"
            assert result2["user_id"] == 456
