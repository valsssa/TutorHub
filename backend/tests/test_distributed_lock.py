"""Tests for the distributed locking service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.distributed_lock import DistributedLockService, distributed_lock


class TestDistributedLockService:
    """Tests for DistributedLockService class."""

    @pytest.fixture
    def lock_service(self):
        """Create a fresh lock service for testing."""
        service = DistributedLockService()
        return service

    def test_init(self, lock_service):
        """Test service initialization."""
        assert lock_service._redis is None
        assert lock_service._instance_id is not None
        assert len(lock_service._instance_id) == 32

    def test_get_key(self, lock_service):
        """Test Redis key generation."""
        key = lock_service._get_key("my_lock")
        assert key == "distributed_lock:my_lock"

    def test_get_key_with_special_chars(self, lock_service):
        """Test key generation with special characters."""
        key = lock_service._get_key("job:expire_requests")
        assert key == "distributed_lock:job:expire_requests"

    def test_get_lock_value(self, lock_service):
        """Test lock value generation."""
        value = lock_service._get_lock_value()
        assert lock_service._instance_id in value
        assert len(value) > len(lock_service._instance_id)

    def test_get_lock_value_unique(self, lock_service):
        """Test lock values are unique."""
        values = [lock_service._get_lock_value() for _ in range(100)]
        assert len(set(values)) == 100

    @pytest.mark.asyncio
    async def test_try_acquire_success(self, lock_service):
        """Test successful lock acquisition."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            acquired, token = await lock_service.try_acquire("test_lock")

            assert acquired is True
            assert token is not None
            mock_redis.set.assert_called_once()
            call_kwargs = mock_redis.set.call_args.kwargs
            assert call_kwargs["nx"] is True
            assert call_kwargs["ex"] == 60

    @pytest.mark.asyncio
    async def test_try_acquire_with_custom_timeout(self, lock_service):
        """Test lock acquisition with custom timeout."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            acquired, token = await lock_service.try_acquire("test_lock", timeout=300)

            assert acquired is True
            call_kwargs = mock_redis.set.call_args.kwargs
            assert call_kwargs["ex"] == 300

    @pytest.mark.asyncio
    async def test_try_acquire_already_held(self, lock_service):
        """Test acquisition when lock is already held."""
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            acquired, token = await lock_service.try_acquire("test_lock")

            assert acquired is False
            assert token is None

    @pytest.mark.asyncio
    async def test_try_acquire_redis_error(self, lock_service):
        """Test acquisition fails open on Redis error."""
        mock_redis = AsyncMock()
        mock_redis.set.side_effect = Exception("Connection error")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            acquired, token = await lock_service.try_acquire("test_lock")

            assert acquired is True
            assert token is None

    @pytest.mark.asyncio
    async def test_release_success(self, lock_service):
        """Test successful lock release."""
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.release("test_lock", "token123")

            assert result is True
            mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_release_token_mismatch(self, lock_service):
        """Test release with wrong token."""
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 0

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.release("test_lock", "wrong_token")

            assert result is False

    @pytest.mark.asyncio
    async def test_release_null_token(self, lock_service):
        """Test release with null token (fail-open mode)."""
        result = await lock_service.release("test_lock", None)
        assert result is True

    @pytest.mark.asyncio
    async def test_release_redis_error(self, lock_service):
        """Test release handles Redis error."""
        mock_redis = AsyncMock()
        mock_redis.eval.side_effect = Exception("Connection error")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.release("test_lock", "token123")

            assert result is False

    @pytest.mark.asyncio
    async def test_is_locked_true(self, lock_service):
        """Test checking if lock is held."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 1

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.is_locked("test_lock")

            assert result is True
            mock_redis.exists.assert_called_with("distributed_lock:test_lock")

    @pytest.mark.asyncio
    async def test_is_locked_false(self, lock_service):
        """Test checking lock when not held."""
        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.is_locked("test_lock")

            assert result is False

    @pytest.mark.asyncio
    async def test_is_locked_redis_error(self, lock_service):
        """Test is_locked handles Redis error."""
        mock_redis = AsyncMock()
        mock_redis.exists.side_effect = Exception("Connection error")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.is_locked("test_lock")

            assert result is False

    @pytest.mark.asyncio
    async def test_get_lock_ttl(self, lock_service):
        """Test getting lock TTL."""
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = 45

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.get_lock_ttl("test_lock")

            assert result == 45
            mock_redis.ttl.assert_called_with("distributed_lock:test_lock")

    @pytest.mark.asyncio
    async def test_get_lock_ttl_no_lock(self, lock_service):
        """Test TTL for non-existent lock."""
        mock_redis = AsyncMock()
        mock_redis.ttl.return_value = -1

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.get_lock_ttl("nonexistent")

            assert result == -1

    @pytest.mark.asyncio
    async def test_get_lock_ttl_redis_error(self, lock_service):
        """Test TTL handles Redis error."""
        mock_redis = AsyncMock()
        mock_redis.ttl.side_effect = Exception("Connection error")

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            result = await lock_service.get_lock_ttl("test_lock")

            assert result == -1


class TestDistributedLockContextManager:
    """Tests for the acquire context manager."""

    @pytest.fixture
    def lock_service(self):
        """Create a fresh lock service for testing."""
        return DistributedLockService()

    @pytest.mark.asyncio
    async def test_acquire_context_manager_success(self, lock_service):
        """Test context manager acquires and releases lock."""
        with patch.object(
            lock_service, "try_acquire", return_value=(True, "token123")
        ) as mock_acquire, patch.object(lock_service, "release") as mock_release:
            async with lock_service.acquire("test_lock") as acquired:
                assert acquired is True

            mock_acquire.assert_called_once_with("test_lock", 60)
            mock_release.assert_called_once_with("test_lock", "token123")

    @pytest.mark.asyncio
    async def test_acquire_context_manager_not_acquired(self, lock_service):
        """Test context manager when lock not acquired."""
        with patch.object(
            lock_service, "try_acquire", return_value=(False, None)
        ) as mock_acquire, patch.object(lock_service, "release") as mock_release:
            async with lock_service.acquire("test_lock") as acquired:
                assert acquired is False

            mock_acquire.assert_called_once()
            mock_release.assert_not_called()

    @pytest.mark.asyncio
    async def test_acquire_context_manager_with_timeout(self, lock_service):
        """Test context manager with custom timeout."""
        with patch.object(
            lock_service, "try_acquire", return_value=(True, "token")
        ) as mock_acquire, patch.object(lock_service, "release"):
            async with lock_service.acquire("test_lock", timeout=300) as acquired:
                assert acquired is True

            mock_acquire.assert_called_once_with("test_lock", 300)

    @pytest.mark.asyncio
    async def test_acquire_releases_on_exception(self, lock_service):
        """Test context manager releases lock even on exception."""
        with patch.object(
            lock_service, "try_acquire", return_value=(True, "token123")
        ), patch.object(lock_service, "release") as mock_release:
            try:
                async with lock_service.acquire("test_lock"):
                    raise ValueError("Test exception")
            except ValueError:
                pass

            mock_release.assert_called_once_with("test_lock", "token123")

    @pytest.mark.asyncio
    async def test_close(self, lock_service):
        """Test closing Redis connection."""
        mock_redis = AsyncMock()
        lock_service._redis = mock_redis

        await lock_service.close()

        mock_redis.close.assert_called_once()
        assert lock_service._redis is None


class TestGlobalLockInstance:
    """Tests for the global distributed_lock instance."""

    def test_singleton_exists(self):
        """Test global instance exists."""
        assert distributed_lock is not None
        assert isinstance(distributed_lock, DistributedLockService)

    def test_singleton_has_instance_id(self):
        """Test global instance has unique ID."""
        assert distributed_lock._instance_id is not None
        assert len(distributed_lock._instance_id) == 32


class TestLuaScript:
    """Tests for the Lua release script logic."""

    @pytest.mark.asyncio
    async def test_lua_script_in_release(self):
        """Test that release uses atomic Lua script."""
        lock_service = DistributedLockService()
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            await lock_service.release("test_lock", "token")

            call_args = mock_redis.eval.call_args
            script = call_args[0][0]

            assert "redis.call" in script
            assert "get" in script.lower()
            assert "del" in script.lower()


class TestConcurrencyScenarios:
    """Tests for concurrency scenarios."""

    @pytest.mark.asyncio
    async def test_two_instances_different_ids(self):
        """Test two service instances have different IDs."""
        service1 = DistributedLockService()
        service2 = DistributedLockService()

        assert service1._instance_id != service2._instance_id

    @pytest.mark.asyncio
    async def test_lock_values_include_instance_id(self):
        """Test lock values contain instance ID for ownership."""
        service = DistributedLockService()
        value = service._get_lock_value()

        assert service._instance_id in value

    @pytest.mark.asyncio
    async def test_typical_job_usage_pattern(self):
        """Test typical background job usage pattern."""
        lock_service = DistributedLockService()

        with patch.object(
            lock_service, "try_acquire", return_value=(True, "token")
        ) as mock_acquire, patch.object(lock_service, "release") as mock_release:
            async with lock_service.acquire(
                "job:expire_requests", timeout=300
            ) as acquired:
                if acquired:
                    pass

            mock_acquire.assert_called_once_with("job:expire_requests", 300)
            mock_release.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_execution_when_locked(self):
        """Test job skips execution when lock is held."""
        lock_service = DistributedLockService()
        executed = False

        with patch.object(lock_service, "try_acquire", return_value=(False, None)):
            with patch.object(lock_service, "release"):
                async with lock_service.acquire("job:test") as acquired:
                    if acquired:
                        executed = True

        assert executed is False
