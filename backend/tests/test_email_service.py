"""
Comprehensive tests for the Brevo Email Service module.

Tests cover:
- Email delivery status enum
- Email delivery result dataclass
- Email service initialization and client management
- Transient error detection
- Email sending with tracking
- Retry logic with exponential backoff
- Booking email templates
- Authentication email templates (password reset, welcome, verification)
- Error handling and edge cases
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

import pytest

from core.email_service import (
    EmailDeliveryStatus,
    EmailDeliveryResult,
    EmailService,
    email_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def email_svc() -> EmailService:
    """Fresh EmailService instance for each test."""
    return EmailService()


@pytest.fixture
def mock_settings():
    """Mock settings with Brevo configured."""
    with patch("core.email_service.settings") as mock:
        mock.BREVO_API_KEY = "test-api-key"
        mock.BREVO_SENDER_EMAIL = "noreply@example.com"
        mock.BREVO_SENDER_NAME = "EduStream"
        mock.EMAIL_ENABLED = True
        mock.FRONTEND_URL = "https://example.com"
        yield mock


@pytest.fixture
def mock_brevo_api():
    """Mock Brevo SDK API."""
    with patch("core.email_service.sib_api_v3_sdk") as mock_sdk:
        mock_api = MagicMock()
        mock_sdk.ApiClient.return_value = MagicMock()
        mock_sdk.TransactionalEmailsApi.return_value = mock_api
        mock_sdk.Configuration.return_value = MagicMock()
        mock_sdk.SendSmtpEmail.return_value = MagicMock()
        mock_sdk.SendSmtpEmailSender.return_value = MagicMock()
        mock_sdk.SendSmtpEmailTo.return_value = MagicMock()
        yield mock_sdk, mock_api


# =============================================================================
# Test EmailDeliveryStatus Enum
# =============================================================================


class TestEmailDeliveryStatus:
    """Tests for EmailDeliveryStatus enum."""

    def test_success_status(self):
        """Test SUCCESS status value."""
        assert EmailDeliveryStatus.SUCCESS.value == "success"

    def test_failed_transient_status(self):
        """Test FAILED_TRANSIENT status value."""
        assert EmailDeliveryStatus.FAILED_TRANSIENT.value == "failed_transient"

    def test_failed_permanent_status(self):
        """Test FAILED_PERMANENT status value."""
        assert EmailDeliveryStatus.FAILED_PERMANENT.value == "failed_permanent"

    def test_disabled_status(self):
        """Test DISABLED status value."""
        assert EmailDeliveryStatus.DISABLED.value == "disabled"

    def test_not_configured_status(self):
        """Test NOT_CONFIGURED status value."""
        assert EmailDeliveryStatus.NOT_CONFIGURED.value == "not_configured"

    def test_status_is_string_enum(self):
        """Test that status values are strings."""
        for status in EmailDeliveryStatus:
            assert isinstance(status.value, str)


# =============================================================================
# Test EmailDeliveryResult Dataclass
# =============================================================================


class TestEmailDeliveryResult:
    """Tests for EmailDeliveryResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = EmailDeliveryResult(
            success=True,
            status=EmailDeliveryStatus.SUCCESS,
            message_id="msg-123",
        )

        assert result.success is True
        assert result.status == EmailDeliveryStatus.SUCCESS
        assert result.message_id == "msg-123"
        assert result.error_message is None
        assert result.attempts == 1

    def test_create_failure_result(self):
        """Test creating a failure result."""
        result = EmailDeliveryResult(
            success=False,
            status=EmailDeliveryStatus.FAILED_PERMANENT,
            error_message="Invalid recipient",
        )

        assert result.success is False
        assert result.status == EmailDeliveryStatus.FAILED_PERMANENT
        assert result.error_message == "Invalid recipient"
        assert result.message_id is None

    def test_result_has_timestamp(self):
        """Test that result has automatic timestamp."""
        result = EmailDeliveryResult(
            success=True,
            status=EmailDeliveryStatus.SUCCESS,
        )

        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_result_with_custom_timestamp(self):
        """Test result with custom timestamp."""
        custom_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        result = EmailDeliveryResult(
            success=True,
            status=EmailDeliveryStatus.SUCCESS,
            timestamp=custom_time,
        )

        assert result.timestamp == custom_time

    def test_result_with_multiple_attempts(self):
        """Test result with multiple attempts."""
        result = EmailDeliveryResult(
            success=True,
            status=EmailDeliveryStatus.SUCCESS,
            attempts=3,
        )

        assert result.attempts == 3

    def test_disabled_result(self):
        """Test creating a disabled result."""
        result = EmailDeliveryResult(
            success=True,
            status=EmailDeliveryStatus.DISABLED,
            error_message="Email sending is disabled",
        )

        assert result.success is True
        assert result.status == EmailDeliveryStatus.DISABLED


# =============================================================================
# Test EmailService Initialization
# =============================================================================


class TestEmailServiceInitialization:
    """Tests for EmailService initialization."""

    def test_service_initialized_without_client(self):
        """Test service initializes with None client."""
        service = EmailService()

        assert service._client is None
        assert service._api is None

    def test_get_client_creates_client_when_configured(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test lazy client initialization."""
        mock_sdk, mock_api = mock_brevo_api

        client = email_svc._get_client()

        assert client is not None
        mock_sdk.Configuration.assert_called_once()

    def test_get_client_returns_none_when_not_configured(
        self, email_svc: EmailService
    ):
        """Test client returns None when API key not set."""
        with patch("core.email_service.settings") as mock:
            mock.BREVO_API_KEY = None

            client = email_svc._get_client()

            assert client is None

    def test_get_client_caches_client(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test client is cached after first call."""
        mock_sdk, mock_api = mock_brevo_api

        client1 = email_svc._get_client()
        client2 = email_svc._get_client()

        assert client1 is client2
        # Configuration should only be called once
        assert mock_sdk.Configuration.call_count == 1


# =============================================================================
# Test Transient Error Detection
# =============================================================================


class TestTransientErrorDetection:
    """Tests for transient error detection."""

    def test_timeout_is_transient(self, email_svc: EmailService):
        """Test that timeout errors are transient."""
        error = Exception("Connection timeout after 30s")
        assert email_svc._is_transient_error(error) is True

    def test_connection_error_is_transient(self, email_svc: EmailService):
        """Test that connection errors are transient."""
        error = Exception("Connection refused")
        assert email_svc._is_transient_error(error) is True

    def test_rate_limit_is_transient(self, email_svc: EmailService):
        """Test that rate limit errors are transient."""
        error = Exception("Rate limit exceeded")
        assert email_svc._is_transient_error(error) is True

    def test_503_is_transient(self, email_svc: EmailService):
        """Test that 503 errors are transient."""
        error = Exception("HTTP 503 Service Unavailable")
        assert email_svc._is_transient_error(error) is True

    def test_502_is_transient(self, email_svc: EmailService):
        """Test that 502 errors are transient."""
        error = Exception("502 Bad Gateway")
        assert email_svc._is_transient_error(error) is True

    def test_504_is_transient(self, email_svc: EmailService):
        """Test that 504 errors are transient."""
        error = Exception("504 Gateway Timeout")
        assert email_svc._is_transient_error(error) is True

    def test_too_many_requests_is_transient(self, email_svc: EmailService):
        """Test that too many requests errors are transient."""
        error = Exception("Too many requests - please slow down")
        assert email_svc._is_transient_error(error) is True

    def test_unavailable_is_transient(self, email_svc: EmailService):
        """Test that unavailable errors are transient."""
        error = Exception("Service temporarily unavailable")
        assert email_svc._is_transient_error(error) is True

    def test_temporary_is_transient(self, email_svc: EmailService):
        """Test that temporary errors are transient."""
        error = Exception("Temporary failure, try again later")
        assert email_svc._is_transient_error(error) is True

    def test_invalid_email_is_permanent(self, email_svc: EmailService):
        """Test that invalid email errors are permanent."""
        error = Exception("Invalid email address format")
        assert email_svc._is_transient_error(error) is False

    def test_authentication_error_is_permanent(self, email_svc: EmailService):
        """Test that authentication errors are permanent."""
        error = Exception("Invalid API key")
        assert email_svc._is_transient_error(error) is False

    def test_404_is_permanent(self, email_svc: EmailService):
        """Test that 404 errors are permanent."""
        error = Exception("HTTP 404 Not Found")
        assert email_svc._is_transient_error(error) is False


# =============================================================================
# Test Email Sending with Tracking
# =============================================================================


class TestSendEmailWithTracking:
    """Tests for email sending with delivery tracking."""

    def test_send_email_success(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test successful email sending."""
        mock_sdk, mock_api = mock_brevo_api
        mock_response = MagicMock()
        mock_response.message_id = "msg-123"
        mock_api.send_transac_email.return_value = mock_response

        result = email_svc._send_email_with_tracking(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result.success is True
        assert result.status == EmailDeliveryStatus.SUCCESS
        assert result.message_id == "msg-123"

    def test_send_email_disabled(self, email_svc: EmailService):
        """Test email sending when disabled."""
        with patch("core.email_service.settings") as mock:
            mock.EMAIL_ENABLED = False

            result = email_svc._send_email_with_tracking(
                to_email="user@example.com",
                to_name="Test User",
                subject="Test",
                html_content="<p>Content</p>",
            )

            assert result.success is True
            assert result.status == EmailDeliveryStatus.DISABLED

    def test_send_email_not_configured(self, email_svc: EmailService):
        """Test email sending when not configured."""
        with patch("core.email_service.settings") as mock:
            mock.EMAIL_ENABLED = True
            mock.BREVO_API_KEY = None

            result = email_svc._send_email_with_tracking(
                to_email="user@example.com",
                to_name="Test User",
                subject="Test",
                html_content="<p>Content</p>",
            )

            assert result.success is False
            assert result.status == EmailDeliveryStatus.NOT_CONFIGURED

    def test_send_email_transient_failure(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test email sending with transient failure."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Connection timeout")

        result = email_svc._send_email_with_tracking(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test",
            html_content="<p>Content</p>",
        )

        assert result.success is False
        assert result.status == EmailDeliveryStatus.FAILED_TRANSIENT

    def test_send_email_permanent_failure(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test email sending with permanent failure."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Invalid recipient")

        result = email_svc._send_email_with_tracking(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test",
            html_content="<p>Content</p>",
        )

        assert result.success is False
        assert result.status == EmailDeliveryStatus.FAILED_PERMANENT

    def test_send_email_with_text_content(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with plain text content."""
        mock_sdk, mock_api = mock_brevo_api
        mock_response = MagicMock()
        mock_response.message_id = "msg-456"
        mock_api.send_transac_email.return_value = mock_response

        result = email_svc._send_email_with_tracking(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test",
            html_content="<p>HTML content</p>",
            text_content="Plain text content",
        )

        assert result.success is True

    def test_send_email_with_template(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with template ID."""
        mock_sdk, mock_api = mock_brevo_api
        mock_response = MagicMock()
        mock_response.message_id = "msg-789"
        mock_api.send_transac_email.return_value = mock_response

        result = email_svc._send_email_with_tracking(
            to_email="user@example.com",
            to_name="Test User",
            subject="Test",
            html_content="<p>Content</p>",
            template_id=123,
            params={"name": "Test", "booking_id": 456},
        )

        assert result.success is True


# =============================================================================
# Test Simple Send Email
# =============================================================================


class TestSendEmail:
    """Tests for simple email sending (returns boolean)."""

    def test_send_email_returns_true_on_success(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test _send_email returns True on success."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is True

    def test_send_email_returns_false_on_failure(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test _send_email returns False on failure."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Error")

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is False

    def test_send_email_returns_true_when_disabled(self, email_svc: EmailService):
        """Test _send_email returns True when email is disabled."""
        with patch("core.email_service.settings") as mock:
            mock.EMAIL_ENABLED = False

            result = email_svc._send_email(
                to_email="user@example.com",
                to_name="User",
                subject="Test",
                html_content="<p>Test</p>",
            )

            assert result is True


# =============================================================================
# Test Retry Logic
# =============================================================================


class TestSendWithRetry:
    """Tests for email sending with retry logic."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_attempt(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test successful send on first attempt."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3,
        )

        assert result.success is True
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_transient_failure(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test successful send after transient failure."""
        mock_sdk, mock_api = mock_brevo_api

        # First call fails with transient error, second succeeds
        mock_api.send_transac_email.side_effect = [
            Exception("Connection timeout"),
            MagicMock(message_id="msg-123"),
        ]

        result = await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3,
            base_delay=0.01,  # Short delay for testing
        )

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test failure after exhausting all retry attempts."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Connection timeout")

        result = await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3,
            base_delay=0.01,
        )

        assert result.success is False
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_retry_stops_on_permanent_failure(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test retry stops immediately on permanent failure."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Invalid API key")

        result = await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3,
            base_delay=0.01,
        )

        assert result.success is False
        assert result.status == EmailDeliveryStatus.FAILED_PERMANENT
        assert result.attempts == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_retry_with_disabled_email(self, email_svc: EmailService):
        """Test retry when email is disabled."""
        with patch("core.email_service.settings") as mock:
            mock.EMAIL_ENABLED = False

            result = await email_svc.send_with_retry(
                to_email="user@example.com",
                to_name="User",
                subject="Test",
                html_content="<p>Test</p>",
            )

            assert result.success is True
            assert result.status == EmailDeliveryStatus.DISABLED
            assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_with_template(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test retry with template parameters."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            template_id=100,
            params={"key": "value"},
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test that exponential backoff uses correct delays."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.side_effect = Exception("Connection timeout")

        base_delay = 0.1
        start_time = asyncio.get_event_loop().time()

        await email_svc.send_with_retry(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3,
            base_delay=base_delay,
        )

        elapsed = asyncio.get_event_loop().time() - start_time

        # Expected delays: 0.1s (first retry) + 0.2s (second retry) = 0.3s minimum
        # Add small buffer for execution time
        assert elapsed >= 0.3


# =============================================================================
# Test Booking Email Templates
# =============================================================================


class TestBookingEmailTemplates:
    """Tests for booking-related email templates."""

    def test_send_booking_confirmation_student(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending booking confirmation to student."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_confirmation_student(
            student_email="student@example.com",
            student_name="Jane Student",
            tutor_name="John Tutor",
            subject_name="Mathematics",
            session_date="January 15, 2024",
            session_time="10:00 AM",
            booking_id=123,
            join_url="https://zoom.us/j/123456",
        )

        assert result is True
        mock_api.send_transac_email.assert_called_once()

    def test_send_booking_confirmation_student_without_join_url(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test booking confirmation without join URL."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_confirmation_student(
            student_email="student@example.com",
            student_name="Jane",
            tutor_name="John",
            subject_name="Physics",
            session_date="January 20, 2024",
            session_time="2:00 PM",
            booking_id=456,
            join_url=None,
        )

        assert result is True

    def test_send_booking_confirmation_tutor(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending booking notification to tutor."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_confirmation_tutor(
            tutor_email="tutor@example.com",
            tutor_name="John Tutor",
            student_name="Jane Student",
            subject_name="Chemistry",
            session_date="January 16, 2024",
            session_time="11:00 AM",
            booking_id=789,
        )

        assert result is True

    def test_send_booking_reminder(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending booking reminder."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_reminder(
            email="user@example.com",
            name="Test User",
            role="student",
            other_party_name="John Tutor",
            subject_name="Biology",
            session_date="January 17, 2024",
            session_time="3:00 PM",
            booking_id=101,
            join_url="https://zoom.us/j/789",
            hours_until=24,
        )

        assert result is True

    def test_send_booking_reminder_to_tutor(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending booking reminder to tutor."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_reminder(
            email="tutor@example.com",
            name="John Tutor",
            role="tutor",
            other_party_name="Jane Student",
            subject_name="History",
            session_date="January 18, 2024",
            session_time="4:00 PM",
            booking_id=102,
            hours_until=1,
        )

        assert result is True

    def test_send_booking_cancelled(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending booking cancellation notification."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_cancelled(
            email="student@example.com",
            name="Jane Student",
            cancelled_by="tutor",
            other_party_name="John Tutor",
            subject_name="English",
            session_date="January 19, 2024",
            reason="Schedule conflict",
            refund_details="Full refund of $50.00 will be processed within 5-7 business days",
        )

        assert result is True

    def test_send_booking_cancelled_without_reason(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test cancellation notification without reason."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_booking_cancelled(
            email="student@example.com",
            name="Jane Student",
            cancelled_by="student",
            other_party_name="John Tutor",
            subject_name="Art",
            session_date="January 20, 2024",
            reason=None,
            refund_details=None,
        )

        assert result is True


# =============================================================================
# Test Authentication Email Templates
# =============================================================================


class TestAuthenticationEmailTemplates:
    """Tests for authentication-related email templates."""

    def test_send_password_reset(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending password reset email."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_password_reset(
            email="user@example.com",
            name="Test User",
            reset_token="abc123xyz789",
            expires_in_hours=1,
        )

        assert result is True

    def test_send_password_reset_custom_expiry(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test password reset with custom expiry."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_password_reset(
            email="user@example.com",
            name="Test User",
            reset_token="token123",
            expires_in_hours=24,
        )

        assert result is True

    def test_send_welcome_email_student(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending welcome email to student."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_welcome_email(
            email="student@example.com",
            name="New Student",
            role="student",
        )

        assert result is True

    def test_send_welcome_email_tutor(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending welcome email to tutor."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_welcome_email(
            email="tutor@example.com",
            name="New Tutor",
            role="tutor",
        )

        assert result is True

    def test_send_email_verification(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email verification."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc.send_email_verification(
            email="user@example.com",
            name="New User",
            verification_token="verify123token",
        )

        assert result is True


# =============================================================================
# Test Error Handling and Edge Cases
# =============================================================================


class TestErrorHandlingAndEdgeCases:
    """Tests for error handling and edge cases."""

    def test_send_email_with_special_characters_in_name(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with special characters in name."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="John O'Brien",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is True

    def test_send_email_with_unicode_content(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with unicode content."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test Subject",
            html_content="<p>Hello</p>",
        )

        assert result is True

    def test_send_email_with_long_subject(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with very long subject."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        long_subject = "A" * 500

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="User",
            subject=long_subject,
            html_content="<p>Test</p>",
        )

        assert result is True

    def test_send_email_with_empty_html_content(
        self, email_svc: EmailService, mock_settings, mock_brevo_api
    ):
        """Test sending email with empty HTML content."""
        mock_sdk, mock_api = mock_brevo_api
        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_svc._send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="",
        )

        assert result is True

    def test_transient_error_keywords_list(self, email_svc: EmailService):
        """Test that transient error keywords list is comprehensive."""
        keywords = email_svc.TRANSIENT_ERROR_KEYWORDS

        assert "timeout" in keywords
        assert "connection" in keywords
        assert "temporary" in keywords
        assert "rate limit" in keywords
        assert "too many requests" in keywords
        assert "503" in keywords
        assert "502" in keywords
        assert "504" in keywords
        assert "unavailable" in keywords


# =============================================================================
# Test Singleton Instance
# =============================================================================


class TestSingletonInstance:
    """Tests for the singleton email_service instance."""

    def test_singleton_instance_exists(self):
        """Test that singleton instance is available."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    def test_singleton_has_client_attribute(self):
        """Test that singleton has _client attribute."""
        assert hasattr(email_service, "_client")

    def test_singleton_has_api_attribute(self):
        """Test that singleton has _api attribute."""
        assert hasattr(email_service, "_api")

    def test_singleton_can_send_email(self, mock_settings, mock_brevo_api):
        """Test that singleton can be used to send email."""
        mock_sdk, mock_api = mock_brevo_api

        # Reset singleton state for clean test
        email_service._client = None
        email_service._api = None

        mock_api.send_transac_email.return_value = MagicMock(message_id="msg-123")

        result = email_service._send_email(
            to_email="user@example.com",
            to_name="User",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result is True
