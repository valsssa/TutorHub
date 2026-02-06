"""
Fake Email - In-memory implementation of EmailPort for testing.

Logs all email calls and stores sent emails for test assertions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from core.ports.email import (
    BookingEmailContext,
    EmailResult,
    EmailStatus,
)


@dataclass
class SentEmail:
    """Record of a sent email."""

    id: str
    to_email: str
    to_name: str
    subject: str
    html_content: str | None = None
    text_content: str | None = None
    template_type: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class FakeEmail:
    """
    In-memory fake implementation of EmailPort for testing.

    Features:
    - Stores all sent emails for assertions
    - Configurable success/failure modes
    - Tracks delivery status
    """

    sent_emails: list[SentEmail] = field(default_factory=list)
    should_fail: bool = False
    failure_status: EmailStatus = EmailStatus.FAILED_PERMANENT
    failure_message: str = "Simulated email failure"

    def _record_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        template_type: str,
        html_content: str | None = None,
        context: dict | None = None,
    ) -> EmailResult:
        """Record a sent email."""
        if self.should_fail:
            return EmailResult(
                success=False,
                status=self.failure_status,
                error_message=self.failure_message,
            )

        email_id = f"msg_test_{uuid.uuid4().hex[:16]}"
        self.sent_emails.append(
            SentEmail(
                id=email_id,
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                template_type=template_type,
                context=context or {},
            )
        )

        return EmailResult(
            success=True,
            status=EmailStatus.SUCCESS,
            message_id=email_id,
        )

    def send_booking_confirmed(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """Send fake booking confirmation."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"Booking Confirmed: {context.subject_name or 'Session'}",
            template_type="booking_confirmed",
            context={
                "booking_id": context.booking_id,
                "tutor_name": context.tutor_name,
                "student_name": context.student_name,
            },
        )

    def send_booking_cancelled(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        cancelled_by: str,
    ) -> EmailResult:
        """Send fake booking cancellation."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"Booking Cancelled: {context.subject_name or 'Session'}",
            template_type="booking_cancelled",
            context={
                "booking_id": context.booking_id,
                "cancelled_by": cancelled_by,
            },
        )

    def send_booking_reminder(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        hours_until: int,
    ) -> EmailResult:
        """Send fake booking reminder."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"Reminder: Your session is in {hours_until} hours",
            template_type="booking_reminder",
            context={
                "booking_id": context.booking_id,
                "hours_until": hours_until,
            },
        )

    def send_booking_request(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """Send fake booking request notification."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"New Booking Request: {context.subject_name or 'Session'}",
            template_type="booking_request",
            context={
                "booking_id": context.booking_id,
                "student_name": context.student_name,
            },
        )

    def send_verification_email(
        self,
        *,
        to_email: str,
        to_name: str,
        verification_url: str,
        expires_in_hours: int = 24,
    ) -> EmailResult:
        """Send fake verification email."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject="Verify Your Email",
            template_type="verification",
            context={
                "verification_url": verification_url,
                "expires_in_hours": expires_in_hours,
            },
        )

    def send_password_reset(
        self,
        *,
        to_email: str,
        to_name: str,
        reset_url: str,
        expires_in_hours: int = 1,
    ) -> EmailResult:
        """Send fake password reset email."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject="Reset Your Password",
            template_type="password_reset",
            context={
                "reset_url": reset_url,
                "expires_in_hours": expires_in_hours,
            },
        )

    def send_welcome_email(
        self,
        *,
        to_email: str,
        to_name: str,
        role: str,
        login_url: str | None = None,
    ) -> EmailResult:
        """Send fake welcome email."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject="Welcome to EduStream!",
            template_type="welcome",
            context={
                "role": role,
                "login_url": login_url,
            },
        )

    def send_tutor_approved(
        self,
        *,
        to_email: str,
        to_name: str,
        dashboard_url: str | None = None,
    ) -> EmailResult:
        """Send fake tutor approval notification."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject="Your Tutor Application Has Been Approved!",
            template_type="tutor_approved",
            context={
                "dashboard_url": dashboard_url,
            },
        )

    def send_review_request(
        self,
        *,
        to_email: str,
        to_name: str,
        tutor_name: str,
        booking_id: int,
        review_url: str,
    ) -> EmailResult:
        """Send fake review request."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=f"How was your session with {tutor_name}?",
            template_type="review_request",
            context={
                "tutor_name": tutor_name,
                "booking_id": booking_id,
                "review_url": review_url,
            },
        )

    def send_custom_email(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> EmailResult:
        """Send fake custom email."""
        return self._record_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            template_type="custom",
            html_content=html_content,
        )

    # =========================================================================
    # Test Helpers
    # =========================================================================

    def get_emails_to(self, email: str) -> list[SentEmail]:
        """Get all emails sent to a specific address."""
        return [e for e in self.sent_emails if e.to_email == email]

    def get_emails_by_type(self, template_type: str) -> list[SentEmail]:
        """Get all emails of a specific template type."""
        return [e for e in self.sent_emails if e.template_type == template_type]

    def get_last_email(self) -> SentEmail | None:
        """Get the most recently sent email."""
        return self.sent_emails[-1] if self.sent_emails else None

    def clear(self) -> None:
        """Clear all sent emails."""
        self.sent_emails.clear()

    def reset(self) -> None:
        """Reset all state."""
        self.sent_emails.clear()
        self.should_fail = False
