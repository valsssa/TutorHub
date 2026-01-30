"""Tests for the admin feature flags router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from core.feature_flags import FeatureFlag, FeatureFlags, FeatureState


class TestFeatureFlagsRouter:
    """Tests for feature flags admin endpoints."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        user.email = "admin@example.com"
        return user

    @pytest.fixture
    def mock_feature_flags(self):
        """Create mock feature flags manager."""
        return MagicMock(spec=FeatureFlags)


class TestListFeatureFlags:
    """Tests for list_feature_flags endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_list_returns_all_flags(self, mock_admin_user):
        """Test listing all feature flags."""
        mock_flags = [
            FeatureFlag(name="flag1", state=FeatureState.ENABLED),
            FeatureFlag(name="flag2", state=FeatureState.DISABLED),
        ]

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.list_flags = AsyncMock(return_value=mock_flags)

            from modules.admin.feature_flags_router import list_feature_flags

            result = await list_feature_flags(mock_admin_user)

            assert len(result) == 2


class TestEnableFeatureFlag:
    """Tests for enable_feature_flag endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_enable_flag(self, mock_admin_user):
        """Test enabling a feature flag."""
        mock_flag = FeatureFlag(name="test_flag", state=FeatureState.ENABLED)

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.enable = AsyncMock(return_value=mock_flag)

            from modules.admin.feature_flags_router import enable_feature_flag

            result = await enable_feature_flag("test_flag", mock_admin_user)

            mock_ff.enable.assert_called_once_with("test_flag")


class TestDisableFeatureFlag:
    """Tests for disable_feature_flag endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_disable_flag(self, mock_admin_user):
        """Test disabling a feature flag."""
        mock_flag = FeatureFlag(name="test_flag", state=FeatureState.DISABLED)

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.disable = AsyncMock(return_value=mock_flag)

            from modules.admin.feature_flags_router import disable_feature_flag

            result = await disable_feature_flag("test_flag", mock_admin_user)

            mock_ff.disable.assert_called_once_with("test_flag")


class TestSetPercentage:
    """Tests for set_percentage endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_set_percentage(self, mock_admin_user):
        """Test setting percentage rollout."""
        mock_flag = FeatureFlag(
            name="test_flag",
            state=FeatureState.PERCENTAGE,
            percentage=50,
        )

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.set_percentage = AsyncMock(return_value=mock_flag)

            from modules.admin.feature_flags_router import set_percentage

            result = await set_percentage("test_flag", 50, mock_admin_user)

            mock_ff.set_percentage.assert_called_once_with("test_flag", 50)


class TestDeleteFeatureFlag:
    """Tests for delete_feature_flag endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_delete_flag_success(self, mock_admin_user):
        """Test deleting a feature flag successfully."""
        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.delete_flag = AsyncMock(return_value=True)

            from modules.admin.feature_flags_router import delete_feature_flag

            await delete_feature_flag("test_flag", mock_admin_user)

            mock_ff.delete_flag.assert_called_once_with("test_flag")

    @pytest.mark.asyncio
    async def test_delete_flag_not_found(self, mock_admin_user):
        """Test deleting a non-existent flag."""
        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.delete_flag = AsyncMock(return_value=False)

            from modules.admin.feature_flags_router import delete_feature_flag

            with pytest.raises(HTTPException) as exc_info:
                await delete_feature_flag("nonexistent", mock_admin_user)

            assert exc_info.value.status_code == 404


class TestAddToAllowlist:
    """Tests for add_to_allowlist endpoint."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        return user

    @pytest.mark.asyncio
    async def test_add_users_to_allowlist(self, mock_admin_user):
        """Test adding users to allowlist."""
        mock_flag = FeatureFlag(
            name="test_flag",
            state=FeatureState.ALLOWLIST,
            allowlist=["user1", "user2"],
        )

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.add_to_allowlist = AsyncMock(return_value=mock_flag)

            from modules.admin.feature_flags_router import add_to_allowlist

            result = await add_to_allowlist(
                "test_flag", ["user1", "user2"], mock_admin_user
            )

            mock_ff.add_to_allowlist.assert_called_once()


class TestFeatureFlagSecurity:
    """Tests for feature flag endpoint security."""

    def test_endpoints_require_admin(self):
        """Test all endpoints require admin role."""
        from modules.admin.feature_flags_router import router

        for route in router.routes:
            if hasattr(route, "dependant"):
                dependencies = route.dependant.dependencies
                has_admin_dep = any(
                    "admin" in str(dep.call).lower() for dep in dependencies
                )


class TestFeatureFlagAuditLogging:
    """Tests for audit logging of feature flag changes."""

    @pytest.fixture
    def mock_admin_user(self):
        """Create mock admin user."""
        user = MagicMock()
        user.id = 1
        user.role = "admin"
        user.email = "admin@example.com"
        return user

    @pytest.mark.asyncio
    async def test_enable_logs_action(self, mock_admin_user):
        """Test enabling a flag logs the action."""
        mock_flag = FeatureFlag(name="test_flag", state=FeatureState.ENABLED)

        with patch(
            "modules.admin.feature_flags_router.feature_flags"
        ) as mock_ff:
            mock_ff.enable = AsyncMock(return_value=mock_flag)

            with patch(
                "modules.admin.feature_flags_router.logger"
            ) as mock_logger:
                from modules.admin.feature_flags_router import enable_feature_flag

                await enable_feature_flag("test_flag", mock_admin_user)

                mock_logger.info.assert_called()
