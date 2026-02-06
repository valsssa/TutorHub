"""
Email Port - Interface for email sending.

This port defines the contract for transactional email operations,
abstracting away the specific email provider (Brevo, SendGrid, etc.).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

from core.datetime_utils import utc_now


class EmailStatus(str, Enum):
    """Status of email delivery."""

    SUCCESS = "success"
    FAILED_TRANSIENT = "failed_transient"  # Temporary failure, can retry
    FAILED_PERMANENT = "failed_permanent"  # Permanent failure, don't retry
    DISABLED = "disabled"  # Email disabled in config
    NOT_CONFIGURED = "not_configured"  # Provider not configured


@dataclass(frozen=True)
class EmailResult:
    """Result of an email operation."""

    success: bool
    status: EmailStatus = EmailStatus.SUCCESS
    message_id: str | None = None
    error_message: str | None = None
    attempts: int = 1
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        # Set timestamp if not provided (workaround for frozen dataclass)
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", utc_now())


@dataclass(frozen=True)
class EmailRecipient:
    """Email recipient information."""

    email: str
    name: str | None = None


@dataclass
class BookingEmailContext:
    """Context for booking-related emails."""

    booking_id: int
    student_name: str
    student_email: str
    tutor_name: str
    tutor_email: str
    subject_name: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    amount_display: str | None = None
    meeting_url: str | None = None
    cancellation_reason: str | None = None
    timezone: str = "UTC"


class EmailPort(Protocol):
    """
    Protocol for email sending operations.

    Implementations should handle:
    - Delivery tracking and logging
    - Retry logic for transient failures
    - Rate limiting
    - Template rendering
    """

    def send_booking_confirmed(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """
        Send booking confirmation email.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            context: Booking details

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_booking_cancelled(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        cancelled_by: str,
    ) -> EmailResult:
        """
        Send booking cancellation notification.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            context: Booking details
            cancelled_by: Who cancelled ("student" or "tutor")

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_booking_reminder(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        hours_until: int,
    ) -> EmailResult:
        """
        Send booking reminder email.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            context: Booking details
            hours_until: Hours until session starts

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_booking_request(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """
        Send new booking request notification to tutor.

        Args:
            to_email: Tutor email
            to_name: Tutor name
            context: Booking details

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_verification_email(
        self,
        *,
        to_email: str,
        to_name: str,
        verification_url: str,
        expires_in_hours: int = 24,
    ) -> EmailResult:
        """
        Send email verification link.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            verification_url: URL to verify email
            expires_in_hours: Link expiration time

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_password_reset(
        self,
        *,
        to_email: str,
        to_name: str,
        reset_url: str,
        expires_in_hours: int = 1,
    ) -> EmailResult:
        """
        Send password reset link.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            reset_url: URL to reset password
            expires_in_hours: Link expiration time

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_welcome_email(
        self,
        *,
        to_email: str,
        to_name: str,
        role: str,
        login_url: str | None = None,
    ) -> EmailResult:
        """
        Send welcome email to new user.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            role: User role ("student" or "tutor")
            login_url: URL to login

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_tutor_approved(
        self,
        *,
        to_email: str,
        to_name: str,
        dashboard_url: str | None = None,
    ) -> EmailResult:
        """
        Send tutor approval notification.

        Args:
            to_email: Tutor email
            to_name: Tutor name
            dashboard_url: URL to tutor dashboard

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_review_request(
        self,
        *,
        to_email: str,
        to_name: str,
        tutor_name: str,
        booking_id: int,
        review_url: str,
    ) -> EmailResult:
        """
        Send review request after completed session.

        Args:
            to_email: Student email
            to_name: Student name
            tutor_name: Tutor's name
            booking_id: Booking ID
            review_url: URL to leave review

        Returns:
            EmailResult with delivery status
        """
        ...

    def send_custom_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> EmailResult:
        """
        Send a custom email with arbitrary content.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)

        Returns:
            EmailResult with delivery status
        """
        ...
