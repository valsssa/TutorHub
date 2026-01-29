"""
Brevo (Sendinblue) Email Service

Handles all transactional email sending including:
- Booking confirmations
- Booking reminders
- Cancellation notifications
- Password reset
- Welcome emails

Features:
- Delivery tracking and logging
- Retry logic for transient failures
- Detailed error categorization
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryStatus(str, Enum):
    """Status of email delivery attempt."""

    SUCCESS = "success"
    FAILED_TRANSIENT = "failed_transient"  # Temporary failure, can retry
    FAILED_PERMANENT = "failed_permanent"  # Permanent failure, do not retry
    DISABLED = "disabled"  # Email disabled in config
    NOT_CONFIGURED = "not_configured"  # API key not set


@dataclass
class EmailDeliveryResult:
    """Result of an email delivery attempt."""

    success: bool
    status: EmailDeliveryStatus
    message_id: str | None = None
    error_message: str | None = None
    attempts: int = 1
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


# ============================================================================
# Email Service Class
# ============================================================================


class EmailService:
    """Brevo transactional email service with delivery tracking and retry logic."""

    # Transient error codes/messages that warrant retry
    TRANSIENT_ERROR_KEYWORDS = [
        "timeout",
        "connection",
        "temporary",
        "rate limit",
        "too many requests",
        "503",
        "502",
        "504",
        "unavailable",
    ]

    def __init__(self) -> None:
        self._client = None
        self._api = None

    def _get_client(self):
        """Lazy initialization of Brevo client."""
        if self._client is None:
            if not settings.BREVO_API_KEY:
                logger.warning("Brevo API key not configured - emails disabled")
                return None

            import sib_api_v3_sdk

            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key["api-key"] = settings.BREVO_API_KEY
            self._client = sib_api_v3_sdk.ApiClient(configuration)
            self._api = sib_api_v3_sdk.TransactionalEmailsApi(self._client)

        return self._api

    def _is_transient_error(self, error: Exception) -> bool:
        """Determine if an error is transient and worth retrying."""
        error_str = str(error).lower()
        return any(keyword in error_str for keyword in self.TRANSIENT_ERROR_KEYWORDS)

    def _send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        template_id: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send a transactional email via Brevo.

        Returns True if sent successfully, False otherwise.
        """
        result = self._send_email_with_tracking(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            template_id=template_id,
            params=params,
        )
        return result.success

    def _send_email_with_tracking(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        template_id: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> EmailDeliveryResult:
        """
        Send a transactional email via Brevo with detailed tracking.

        Returns EmailDeliveryResult with status and metadata.
        """
        # Check if email is enabled
        if not settings.EMAIL_ENABLED:
            logger.info(
                "Email delivery skipped (disabled)",
                extra={
                    "email_to": to_email,
                    "email_subject": subject[:50],
                    "status": EmailDeliveryStatus.DISABLED.value,
                },
            )
            return EmailDeliveryResult(
                success=True,
                status=EmailDeliveryStatus.DISABLED,
                error_message="Email sending is disabled in configuration",
            )

        # Check if API is configured
        api = self._get_client()
        if not api:
            logger.warning(
                "Email delivery failed (not configured)",
                extra={
                    "email_to": to_email,
                    "email_subject": subject[:50],
                    "status": EmailDeliveryStatus.NOT_CONFIGURED.value,
                },
            )
            return EmailDeliveryResult(
                success=False,
                status=EmailDeliveryStatus.NOT_CONFIGURED,
                error_message="Email service not configured - missing API key",
            )

        try:
            import sib_api_v3_sdk

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    email=settings.BREVO_SENDER_EMAIL,
                    name=settings.BREVO_SENDER_NAME,
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(email=to_email, name=to_name)],
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

            if template_id:
                send_smtp_email.template_id = template_id
                send_smtp_email.params = params or {}

            response = api.send_transac_email(send_smtp_email)
            message_id = getattr(response, "message_id", None)

            logger.info(
                "Email sent successfully",
                extra={
                    "email_to": to_email,
                    "email_subject": subject[:50],
                    "message_id": message_id,
                    "status": EmailDeliveryStatus.SUCCESS.value,
                },
            )

            return EmailDeliveryResult(
                success=True,
                status=EmailDeliveryStatus.SUCCESS,
                message_id=message_id,
            )

        except Exception as e:
            is_transient = self._is_transient_error(e)
            status = (
                EmailDeliveryStatus.FAILED_TRANSIENT
                if is_transient
                else EmailDeliveryStatus.FAILED_PERMANENT
            )
            error_msg = str(e)

            logger.error(
                "Email delivery failed",
                extra={
                    "email_to": to_email,
                    "email_subject": subject[:50],
                    "status": status.value,
                    "error": error_msg,
                    "is_transient": is_transient,
                },
                exc_info=True,
            )

            return EmailDeliveryResult(
                success=False,
                status=status,
                error_message=error_msg,
            )

    async def send_with_retry(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
        template_id: int | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> EmailDeliveryResult:
        """
        Send email with exponential backoff retry for transient failures.

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            subject: Email subject
            html_content: HTML email body
            text_content: Optional plain text body
            template_id: Optional Brevo template ID
            params: Optional template parameters
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)

        Returns:
            EmailDeliveryResult with final status and attempt count
        """
        last_result: EmailDeliveryResult | None = None

        for attempt in range(1, max_retries + 1):
            result = self._send_email_with_tracking(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_id=template_id,
                params=params,
            )
            result.attempts = attempt
            last_result = result

            if result.success:
                if attempt > 1:
                    logger.info(
                        f"Email sent successfully after {attempt} attempts",
                        extra={
                            "email_to": to_email,
                            "email_subject": subject[:50],
                            "attempts": attempt,
                        },
                    )
                return result

            # Only retry transient failures
            if result.status != EmailDeliveryStatus.FAILED_TRANSIENT:
                logger.warning(
                    "Email delivery failed permanently, not retrying",
                    extra={
                        "email_to": to_email,
                        "email_subject": subject[:50],
                        "status": result.status.value,
                        "error": result.error_message,
                    },
                )
                return result

            # Calculate delay with exponential backoff
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(
                    f"Email delivery failed (transient), retrying in {delay}s",
                    extra={
                        "email_to": to_email,
                        "email_subject": subject[:50],
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "next_delay": delay,
                    },
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            f"Email delivery failed after {max_retries} attempts",
            extra={
                "email_to": to_email,
                "email_subject": subject[:50],
                "attempts": max_retries,
                "final_error": last_result.error_message if last_result else "Unknown",
            },
        )

        return last_result if last_result else EmailDeliveryResult(
            success=False,
            status=EmailDeliveryStatus.FAILED_PERMANENT,
            error_message="Max retries exhausted",
            attempts=max_retries,
        )

    # ========================================================================
    # Booking Emails
    # ========================================================================

    def send_booking_confirmation_student(
        self,
        student_email: str,
        student_name: str,
        tutor_name: str,
        subject_name: str,
        session_date: str,
        session_time: str,
        booking_id: int,
        join_url: str | None = None,
    ) -> bool:
        """Send booking confirmation to student."""

        subject = f"Booking Confirmed: {subject_name} with {tutor_name}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Booking Confirmed!</h1>

                <p>Hi {student_name},</p>

                <p>Your tutoring session has been confirmed. Here are the details:</p>

                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Subject:</strong> {subject_name}</p>
                    <p><strong>Tutor:</strong> {tutor_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time}</p>
                    <p><strong>Booking ID:</strong> #{booking_id}</p>
                </div>

                {f'<p><a href="{join_url}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Join Session</a></p>' if join_url else ''}

                <p>You can view and manage your booking in your <a href="{settings.FRONTEND_URL}/bookings/{booking_id}">dashboard</a>.</p>

                <p style="color: #6b7280; font-size: 14px;">
                    Need to reschedule? You can do so up to 24 hours before your session.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream - Your Learning Partner<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=student_email,
            to_name=student_name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_confirmation_tutor(
        self,
        tutor_email: str,
        tutor_name: str,
        student_name: str,
        subject_name: str,
        session_date: str,
        session_time: str,
        booking_id: int,
    ) -> bool:
        """Send booking notification to tutor."""

        subject = f"New Booking: {subject_name} with {student_name}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">New Booking!</h1>

                <p>Hi {tutor_name},</p>

                <p>You have a new confirmed booking:</p>

                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Subject:</strong> {subject_name}</p>
                    <p><strong>Student:</strong> {student_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time}</p>
                    <p><strong>Booking ID:</strong> #{booking_id}</p>
                </div>

                <p><a href="{settings.FRONTEND_URL}/tutor/bookings/{booking_id}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Booking</a></p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream - Your Teaching Partner<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=tutor_email,
            to_name=tutor_name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_reminder(
        self,
        email: str,
        name: str,
        role: str,  # "student" or "tutor"
        other_party_name: str,
        subject_name: str,
        session_date: str,
        session_time: str,
        booking_id: int,
        join_url: str | None = None,
        hours_until: int = 24,
    ) -> bool:
        """Send booking reminder email."""

        subject = f"Reminder: Your session is in {hours_until} hours"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f59e0b;">Session Reminder</h1>

                <p>Hi {name},</p>

                <p>This is a reminder that your tutoring session is coming up in <strong>{hours_until} hours</strong>.</p>

                <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <p><strong>Subject:</strong> {subject_name}</p>
                    <p><strong>{'Tutor' if role == 'student' else 'Student'}:</strong> {other_party_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time}</p>
                </div>

                {f'<p><a href="{join_url}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Join Session</a></p>' if join_url else ''}

                <p style="color: #6b7280; font-size: 14px;">
                    Please be ready a few minutes before the scheduled time.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_cancelled(
        self,
        email: str,
        name: str,
        cancelled_by: str,  # "student" or "tutor"
        other_party_name: str,
        subject_name: str,
        session_date: str,
        reason: str | None = None,
        refund_details: str | None = None,
    ) -> bool:
        """Send booking cancellation notification."""

        subject = f"Booking Cancelled: {subject_name} on {session_date}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ef4444;">Booking Cancelled</h1>

                <p>Hi {name},</p>

                <p>Your tutoring session has been cancelled by the {cancelled_by}.</p>

                <div style="background: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
                    <p><strong>Subject:</strong> {subject_name}</p>
                    <p><strong>With:</strong> {other_party_name}</p>
                    <p><strong>Original Date:</strong> {session_date}</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                </div>

                {f'<div style="background: #ecfdf5; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Refund:</strong> {refund_details}</p></div>' if refund_details else ''}

                <p><a href="{settings.FRONTEND_URL}/tutors" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Find Another Tutor</a></p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
        )

    # ========================================================================
    # Authentication Emails
    # ========================================================================

    def send_password_reset(
        self,
        email: str,
        name: str,
        reset_token: str,
        expires_in_hours: int = 1,
    ) -> bool:
        """Send password reset email."""

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset Your Password"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Password Reset</h1>

                <p>Hi {name},</p>

                <p>We received a request to reset your password. Click the button below to set a new password:</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px;">Reset Password</a>
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    This link will expire in {expires_in_hours} hour(s). If you didn't request a password reset, you can safely ignore this email.
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    If the button doesn't work, copy and paste this URL into your browser:<br>
                    <a href="{reset_url}" style="color: #10b981; word-break: break-all;">{reset_url}</a>
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
        )

    def send_welcome_email(
        self,
        email: str,
        name: str,
        role: str,
    ) -> bool:
        """Send welcome email to new user."""

        subject = "Welcome to EduStream!"

        if role == "tutor":
            cta_text = "Complete Your Profile"
            cta_url = f"{settings.FRONTEND_URL}/tutor/onboarding"
            intro = "Thank you for joining EduStream as a tutor! Complete your profile to start receiving bookings."
        else:
            cta_text = "Find a Tutor"
            cta_url = f"{settings.FRONTEND_URL}/tutors"
            intro = "Thank you for joining EduStream! Browse our tutors to find the perfect match for your learning goals."

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Welcome to EduStream! 🎉</h1>

                <p>Hi {name},</p>

                <p>{intro}</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{cta_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px;">{cta_text}</a>
                </p>

                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Quick Start:</h3>
                    <ul style="padding-left: 20px;">
                        <li>Complete your profile</li>
                        <li>{'Set your availability and rates' if role == 'tutor' else 'Browse tutors by subject'}</li>
                        <li>{'Start receiving booking requests' if role == 'tutor' else 'Book your first session'}</li>
                    </ul>
                </div>

                <p>If you have any questions, our support team is here to help!</p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream - Your Learning Partner<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
        )

    def send_email_verification(
        self,
        email: str,
        name: str,
        verification_token: str,
    ) -> bool:
        """Send email verification link."""

        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        subject = "Verify Your Email"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Verify Your Email</h1>

                <p>Hi {name},</p>

                <p>Please verify your email address to complete your registration:</p>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block; font-size: 16px;">Verify Email</a>
                </p>

                <p style="color: #6b7280; font-size: 14px;">
                    This link will expire in 24 hours.
                </p>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #9ca3af; font-size: 12px;">
                    EduStream<br>
                    <a href="{settings.FRONTEND_URL}">edustream.valsa.solutions</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
        )


# Singleton instance
email_service = EmailService()
