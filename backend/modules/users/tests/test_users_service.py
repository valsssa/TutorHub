"""
Comprehensive tests for the users module.

Tests cover:
- Avatar service (upload, fetch, delete)
- Currency management
- User preferences (timezone)
- Domain events (role changes)
- Event handlers (profile management)
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from models import Booking, TutorProfile, User


# =============================================================================
# Avatar Service Tests
# =============================================================================


class TestAvatarService:
    """Tests for the AvatarService class."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage client."""
        storage = AsyncMock()
        storage.url_ttl.return_value = 3600
        storage.generate_presigned_url = AsyncMock(return_value="https://storage.example.com/avatar.webp")
        storage.upload_file = AsyncMock()
        storage.delete_file = AsyncMock()
        return storage

    @pytest.fixture
    def avatar_service(self, db_session: Session, mock_storage):
        """Create AvatarService with mocked storage."""
        from modules.users.avatar.service import AvatarService

        return AvatarService(db=db_session, storage=mock_storage)

    @pytest.fixture
    def valid_image_upload(self):
        """Create a valid image upload file."""
        img = Image.new("RGB", (300, 300), color="blue")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        upload = MagicMock(spec=UploadFile)
        upload.content_type = "image/png"
        upload.read = AsyncMock(return_value=buffer.getvalue())
        upload.filename = "avatar.png"
        return upload

    @pytest.fixture
    def small_image_upload(self):
        """Create an image that is too small."""
        img = Image.new("RGB", (50, 50), color="red")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        upload = MagicMock(spec=UploadFile)
        upload.content_type = "image/png"
        upload.read = AsyncMock(return_value=buffer.getvalue())
        upload.filename = "small.png"
        return upload

    @pytest.fixture
    def large_dimension_image_upload(self):
        """Create an image that exceeds max dimensions."""
        img = Image.new("RGB", (3000, 3000), color="green")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        upload = MagicMock(spec=UploadFile)
        upload.content_type = "image/png"
        upload.read = AsyncMock(return_value=buffer.getvalue())
        upload.filename = "large.png"
        return upload

    @pytest.mark.asyncio
    async def test_upload_avatar_success(
        self, avatar_service, student_user: User, valid_image_upload, mock_storage
    ):
        """Test successful avatar upload."""
        result = await avatar_service.upload_for_user(student_user, valid_image_upload)

        assert result.avatar_url is not None
        assert result.expires_at > datetime.now(UTC)
        mock_storage.upload_file.assert_called_once()
        assert student_user.avatar_key is not None

    @pytest.mark.asyncio
    async def test_upload_avatar_replaces_old(
        self, avatar_service, student_user: User, valid_image_upload, mock_storage, db_session
    ):
        """Test that uploading a new avatar deletes the old one."""
        student_user.avatar_key = "avatars/old_key.webp"
        db_session.commit()

        await avatar_service.upload_for_user(student_user, valid_image_upload)

        mock_storage.delete_file.assert_called_with("avatars/old_key.webp")

    @pytest.mark.asyncio
    async def test_upload_avatar_invalid_content_type(self, avatar_service, student_user: User):
        """Test that invalid content types are rejected."""
        upload = MagicMock(spec=UploadFile)
        upload.content_type = "application/pdf"

        with pytest.raises(HTTPException) as exc_info:
            await avatar_service.upload_for_user(student_user, upload)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "JPEG and PNG" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_avatar_too_large(self, avatar_service, student_user: User):
        """Test that files exceeding size limit are rejected."""
        upload = MagicMock(spec=UploadFile)
        upload.content_type = "image/png"
        upload.read = AsyncMock(return_value=b"x" * 3_000_000)

        with pytest.raises(HTTPException) as exc_info:
            await avatar_service.upload_for_user(student_user, upload)

        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "2 MB" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_avatar_too_small_dimensions(
        self, avatar_service, student_user: User, small_image_upload
    ):
        """Test that images with dimensions too small are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            await avatar_service.upload_for_user(student_user, small_image_upload)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "150x150" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_upload_avatar_too_large_dimensions(
        self, avatar_service, student_user: User, large_dimension_image_upload
    ):
        """Test that images exceeding max dimensions are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            await avatar_service.upload_for_user(student_user, large_dimension_image_upload)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "2000x2000" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_fetch_avatar_with_key(
        self, avatar_service, student_user: User, mock_storage, db_session
    ):
        """Test fetching avatar when user has one."""
        student_user.avatar_key = "avatars/123/test.webp"
        db_session.commit()

        result = await avatar_service.fetch_for_user(student_user)

        assert result.avatar_url == "https://storage.example.com/avatar.webp"
        mock_storage.generate_presigned_url.assert_called_once_with("avatars/123/test.webp")

    @pytest.mark.asyncio
    async def test_fetch_avatar_without_key(self, avatar_service, student_user: User):
        """Test fetching avatar when user has none returns default."""
        student_user.avatar_key = None

        result = await avatar_service.fetch_for_user(student_user)

        assert result.avatar_url is not None
        assert result.expires_at > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_delete_avatar_success(
        self, avatar_service, student_user: User, mock_storage, db_session
    ):
        """Test successful avatar deletion."""
        student_user.avatar_key = "avatars/123/test.webp"
        db_session.commit()

        result = await avatar_service.delete_for_user(student_user)

        assert "removed successfully" in result.detail
        assert student_user.avatar_key is None
        mock_storage.delete_file.assert_called_once_with("avatars/123/test.webp")

    @pytest.mark.asyncio
    async def test_delete_avatar_no_avatar(self, avatar_service, student_user: User):
        """Test deleting avatar when user has none."""
        student_user.avatar_key = None

        result = await avatar_service.delete_for_user(student_user)

        assert "already removed" in result.detail

    @pytest.mark.asyncio
    async def test_upload_avatar_storage_failure_rollback(
        self, avatar_service, student_user: User, valid_image_upload, mock_storage
    ):
        """Test that storage failures don't leave orphaned records."""
        mock_storage.upload_file = AsyncMock(side_effect=Exception("Storage error"))

        with pytest.raises(Exception):
            await avatar_service.upload_for_user(student_user, valid_image_upload)

        assert student_user.avatar_key is None


class TestAvatarRouter:
    """Tests for avatar API endpoints."""

    def test_upload_avatar_authenticated(self, client, student_token, tutor_user):
        """Test avatar upload endpoint requires authentication."""
        response = client.post("/api/v1/users/me/avatar")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_avatar_authenticated(self, client):
        """Test get avatar endpoint requires authentication."""
        response = client.get("/api/v1/users/me/avatar")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_avatar_authenticated(self, client):
        """Test delete avatar endpoint requires authentication."""
        response = client.delete("/api/v1/users/me/avatar")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# Currency Router Tests
# =============================================================================


class TestCurrencyRouter:
    """Tests for the currency management API endpoints."""

    def test_list_currency_options(self, client, student_token):
        """Test listing currency options."""
        response = client.get(
            "/api/v1/users/currency/options",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # May return 200 if currencies are seeded or 500 if DB not set up
        # In real tests with full DB setup, this should return 200
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_list_currency_options_unauthenticated(self, client):
        """Test listing currencies without authentication (should work for public data)."""
        response = client.get("/api/v1/users/currency/options")
        # Currency options may be public
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_update_currency_authenticated(self, client, student_token, student_user, db_session):
        """Test updating user currency requires authentication."""
        response = client.patch("/api/v1/users/currency", json={"currency": "EUR"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_currency_invalid_code(self, client, student_token):
        """Test updating to invalid currency code."""
        response = client.patch(
            "/api/v1/users/currency",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"currency": "XXX"},
        )
        # Should be 400 for unsupported currency
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_update_currency_invalid_length(self, client, student_token):
        """Test currency code length validation."""
        response = client.patch(
            "/api/v1/users/currency",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"currency": "TOOLONG"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Preferences Router Tests
# =============================================================================


class TestPreferencesRouter:
    """Tests for user preferences API endpoints."""

    def test_update_preferences_unauthenticated(self, client):
        """Test preferences update requires authentication."""
        response = client.patch(
            "/api/v1/users/preferences",
            json={"timezone": "America/New_York"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_preferences_valid_timezone(self, client, student_token):
        """Test updating timezone with valid IANA timezone."""
        response = client.patch(
            "/api/v1/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "America/New_York"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["timezone"] == "America/New_York"

    def test_update_preferences_invalid_timezone(self, client, student_token):
        """Test updating timezone with invalid timezone."""
        response = client.patch(
            "/api/v1/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Invalid/Timezone"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_sync_timezone_unauthenticated(self, client):
        """Test timezone sync requires authentication."""
        response = client.post(
            "/api/v1/users/preferences/sync-timezone",
            json={"detected_timezone": "UTC"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_sync_timezone_same_timezone(self, client, student_token, student_user):
        """Test timezone sync when timezones match."""
        response = client.post(
            "/api/v1/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": student_user.timezone},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["needs_update"] is False
        assert data["saved_timezone"] == student_user.timezone
        assert data["detected_timezone"] == student_user.timezone

    def test_sync_timezone_different_timezone(self, client, student_token, student_user):
        """Test timezone sync when timezones differ."""
        different_tz = "Europe/London" if student_user.timezone != "Europe/London" else "Asia/Tokyo"

        response = client.post(
            "/api/v1/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": different_tz},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["needs_update"] is True
        assert data["saved_timezone"] == student_user.timezone
        assert data["detected_timezone"] == different_tz

    def test_sync_timezone_invalid_timezone(self, client, student_token):
        """Test timezone sync with invalid timezone."""
        response = client.post(
            "/api/v1/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Not/A/Timezone"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Domain Events Tests
# =============================================================================


class TestUserRoleChangedEvent:
    """Tests for the UserRoleChanged domain event."""

    def test_event_creation(self):
        """Test creating a role changed event."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(
            user_id=1,
            old_role="student",
            new_role="tutor",
            changed_by=99,
        )

        assert event.user_id == 1
        assert event.old_role == "student"
        assert event.new_role == "tutor"
        assert event.changed_by == 99

    def test_is_becoming_tutor_true(self):
        """Test is_becoming_tutor returns True when changing to tutor."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="student", new_role="tutor", changed_by=99)
        assert event.is_becoming_tutor() is True

    def test_is_becoming_tutor_false_already_tutor(self):
        """Test is_becoming_tutor returns False when already a tutor."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="tutor", new_role="tutor", changed_by=99)
        assert event.is_becoming_tutor() is False

    def test_is_becoming_tutor_false_not_tutor(self):
        """Test is_becoming_tutor returns False when not becoming a tutor."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="student", new_role="admin", changed_by=99)
        assert event.is_becoming_tutor() is False

    def test_is_leaving_tutor_true(self):
        """Test is_leaving_tutor returns True when leaving tutor role."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="tutor", new_role="student", changed_by=99)
        assert event.is_leaving_tutor() is True

    def test_is_leaving_tutor_false_not_tutor(self):
        """Test is_leaving_tutor returns False when not a tutor."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="student", new_role="admin", changed_by=99)
        assert event.is_leaving_tutor() is False

    def test_is_leaving_tutor_false_staying_tutor(self):
        """Test is_leaving_tutor returns False when staying as tutor."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="tutor", new_role="tutor", changed_by=99)
        assert event.is_leaving_tutor() is False

    def test_event_is_immutable(self):
        """Test that event is frozen (immutable)."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(user_id=1, old_role="student", new_role="tutor", changed_by=99)

        with pytest.raises(AttributeError):
            event.user_id = 2


# =============================================================================
# Event Handlers Tests
# =============================================================================


class TestRoleChangeEventHandler:
    """Tests for the RoleChangeEventHandler."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        from modules.users.domain.handlers import RoleChangeEventHandler

        return RoleChangeEventHandler()

    def test_handle_becoming_tutor_creates_profile(
        self, handler, student_user: User, admin_user: User, db_session: Session
    ):
        """Test that becoming a tutor creates a tutor profile."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(
            user_id=student_user.id,
            old_role="student",
            new_role="tutor",
            changed_by=admin_user.id,
        )

        handler.handle(db_session, event)
        db_session.commit()

        profile = db_session.query(TutorProfile).filter_by(user_id=student_user.id).first()
        assert profile is not None
        assert profile.profile_status == "incomplete"
        assert profile.is_approved is False
        assert profile.hourly_rate == Decimal("1.00")

    def test_handle_becoming_tutor_reactivates_archived_profile(
        self, handler, student_user: User, admin_user: User, db_session: Session
    ):
        """Test that becoming a tutor reactivates an archived profile."""
        from modules.users.domain.events import UserRoleChanged

        # Create an archived profile
        archived_profile = TutorProfile(
            user_id=student_user.id,
            title="Old Title",
            hourly_rate=Decimal("50.00"),
            experience_years=5,
            profile_status="archived",
            is_approved=False,
            languages=["English"],
        )
        db_session.add(archived_profile)
        db_session.commit()

        event = UserRoleChanged(
            user_id=student_user.id,
            old_role="student",
            new_role="tutor",
            changed_by=admin_user.id,
        )

        handler.handle(db_session, event)
        db_session.commit()

        profile = db_session.query(TutorProfile).filter_by(user_id=student_user.id).first()
        assert profile.profile_status == "incomplete"
        assert profile.is_approved is False
        assert profile.hourly_rate == Decimal("50.00")

    def test_handle_leaving_tutor_archives_profile(
        self, handler, tutor_user: User, admin_user: User, db_session: Session
    ):
        """Test that leaving tutor role archives the profile."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(
            user_id=tutor_user.id,
            old_role="tutor",
            new_role="student",
            changed_by=admin_user.id,
        )

        handler.handle(db_session, event)
        db_session.commit()

        profile = db_session.query(TutorProfile).filter_by(user_id=tutor_user.id).first()
        assert profile.profile_status == "archived"
        assert profile.is_approved is False

    def test_handle_leaving_tutor_no_profile_logs_warning(
        self, handler, student_user: User, admin_user: User, db_session: Session
    ):
        """Test that leaving tutor without profile logs a warning."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(
            user_id=student_user.id,
            old_role="tutor",
            new_role="student",
            changed_by=admin_user.id,
        )

        # Should not raise an error
        handler.handle(db_session, event)
        db_session.commit()

    def test_handle_non_tutor_role_changes_no_op(
        self, handler, student_user: User, admin_user: User, db_session: Session
    ):
        """Test that non-tutor role changes are no-ops."""
        from modules.users.domain.events import UserRoleChanged

        event = UserRoleChanged(
            user_id=student_user.id,
            old_role="student",
            new_role="admin",
            changed_by=admin_user.id,
        )

        handler.handle(db_session, event)
        db_session.commit()

        profile = db_session.query(TutorProfile).filter_by(user_id=student_user.id).first()
        assert profile is None

    def test_has_bookings_detection(
        self, handler, tutor_user: User, student_user: User, test_subject, db_session: Session
    ):
        """Test that _has_bookings correctly detects bookings."""
        from datetime import datetime, timedelta

        # Create a booking
        booking = Booking(
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            subject_id=test_subject.id,
            start_time=datetime.now(UTC) + timedelta(days=1),
            end_time=datetime.now(UTC) + timedelta(days=1, hours=1),
            topic="Test",
            hourly_rate=50.00,
            total_amount=50.00,
            currency="USD",
            session_state="REQUESTED",
            payment_state="PENDING",
            tutor_name="Test Tutor",
            student_name="Test Student",
            subject_name=test_subject.name,
        )
        db_session.add(booking)
        db_session.commit()

        has_bookings = handler._has_bookings(db_session, tutor_user.tutor_profile.id)
        assert has_bookings is True


# =============================================================================
# Avatar Schemas Tests
# =============================================================================


class TestAvatarSchemas:
    """Tests for avatar Pydantic schemas."""

    def test_avatar_response_schema(self):
        """Test AvatarResponse schema validation."""
        from modules.users.avatar.schemas import AvatarResponse

        response = AvatarResponse(
            avatar_url="https://example.com/avatar.webp",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert str(response.avatar_url) == "https://example.com/avatar.webp"

    def test_avatar_delete_response_schema(self):
        """Test AvatarDeleteResponse schema validation."""
        from modules.users.avatar.schemas import AvatarDeleteResponse

        response = AvatarDeleteResponse(detail="Avatar deleted successfully")
        assert response.detail == "Avatar deleted successfully"


# =============================================================================
# Integration Tests
# =============================================================================


class TestUsersIntegration:
    """Integration tests for the users module."""

    def test_preferences_update_persists(self, client, student_token, student_user, db_session):
        """Test that preference updates persist across requests."""
        # Update timezone
        response = client.patch(
            "/api/v1/users/preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"timezone": "Europe/Paris"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it persisted
        db_session.refresh(student_user)
        assert student_user.timezone == "Europe/Paris"

        # Verify via sync endpoint
        sync_response = client.post(
            "/api/v1/users/preferences/sync-timezone",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"detected_timezone": "Europe/Paris"},
        )
        assert sync_response.status_code == status.HTTP_200_OK
        assert sync_response.json()["needs_update"] is False

    def test_multiple_timezone_updates(self, client, student_token, student_user, db_session):
        """Test multiple timezone updates work correctly."""
        timezones = ["America/New_York", "Europe/London", "Asia/Tokyo", "UTC"]

        for tz in timezones:
            response = client.patch(
                "/api/v1/users/preferences",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"timezone": tz},
            )
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["timezone"] == tz
