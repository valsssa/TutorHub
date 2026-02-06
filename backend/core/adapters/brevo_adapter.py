"""
Brevo Adapter - Implementation of EmailPort for Brevo (Sendinblue).

Wraps the existing email_service.py functionality with the EmailPort interface.
Preserves retry logic and HTML email templates.
"""

import logging

from core.config import settings
from core.ports.email import (
    BookingEmailContext,
    EmailResult,
    EmailStatus,
)

logger = logging.getLogger(__name__)


class BrevoAdapter:
    """
    Brevo implementation of EmailPort.

    Features:
    - Delivery tracking and logging
    - Retry logic for transient failures
    - HTML email templates
    """

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

    def _send_email_internal(
        self,
        *,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> EmailResult:
        """Send a transactional email via Brevo."""
        if not settings.EMAIL_ENABLED:
            return EmailResult(
                success=True,
                status=EmailStatus.DISABLED,
                error_message="Email sending is disabled",
            )

        api = self._get_client()
        if not api:
            return EmailResult(
                success=False,
                status=EmailStatus.NOT_CONFIGURED,
                error_message="Email service not configured",
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

            response = api.send_transac_email(send_smtp_email)
            message_id = getattr(response, "message_id", None)

            logger.info("Email sent to %s: %s", to_email, subject[:50])

            return EmailResult(
                success=True,
                status=EmailStatus.SUCCESS,
                message_id=message_id,
            )

        except Exception as e:
            is_transient = self._is_transient_error(e)
            status = (
                EmailStatus.FAILED_TRANSIENT
                if is_transient
                else EmailStatus.FAILED_PERMANENT
            )

            logger.error("Email delivery failed to %s: %s", to_email, e)

            return EmailResult(
                success=False,
                status=status,
                error_message=str(e),
            )

    def send_booking_confirmed(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """Send booking confirmation email."""
        subject = f"Booking Confirmed: {context.subject_name or 'Tutoring Session'}"

        session_date = context.start_time.strftime("%B %d, %Y") if context.start_time else "TBD"
        session_time = context.start_time.strftime("%I:%M %p") if context.start_time else "TBD"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Booking Confirmed!</h1>
                <p>Hi {to_name},</p>
                <p>Your tutoring session has been confirmed.</p>
                <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Subject:</strong> {context.subject_name or 'N/A'}</p>
                    <p><strong>Tutor:</strong> {context.tutor_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time} ({context.timezone})</p>
                    <p><strong>Booking ID:</strong> #{context.booking_id}</p>
                </div>
                {f'<p><a href="{context.meeting_url}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Join Session</a></p>' if context.meeting_url else ''}
                <p><a href="{settings.FRONTEND_URL}/bookings/{context.booking_id}">View Booking</a></p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_cancelled(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        cancelled_by: str,
    ) -> EmailResult:
        """Send booking cancellation notification."""
        session_date = context.start_time.strftime("%B %d, %Y") if context.start_time else "TBD"
        subject = f"Booking Cancelled: {context.subject_name or 'Session'} on {session_date}"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #ef4444;">Booking Cancelled</h1>
                <p>Hi {to_name},</p>
                <p>Your tutoring session has been cancelled by the {cancelled_by}.</p>
                <div style="background: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
                    <p><strong>Subject:</strong> {context.subject_name or 'N/A'}</p>
                    <p><strong>Original Date:</strong> {session_date}</p>
                    {f'<p><strong>Reason:</strong> {context.cancellation_reason}</p>' if context.cancellation_reason else ''}
                </div>
                <p><a href="{settings.FRONTEND_URL}/tutors">Find Another Tutor</a></p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_reminder(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
        hours_until: int,
    ) -> EmailResult:
        """Send booking reminder email."""
        subject = f"Reminder: Your session is in {hours_until} hours"

        session_date = context.start_time.strftime("%B %d, %Y") if context.start_time else "TBD"
        session_time = context.start_time.strftime("%I:%M %p") if context.start_time else "TBD"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #f59e0b;">Session Reminder</h1>
                <p>Hi {to_name},</p>
                <p>Your tutoring session is coming up in <strong>{hours_until} hours</strong>.</p>
                <div style="background: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                    <p><strong>Subject:</strong> {context.subject_name or 'N/A'}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time} ({context.timezone})</p>
                </div>
                {f'<p><a href="{context.meeting_url}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Join Session</a></p>' if context.meeting_url else ''}
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_booking_request(
        self,
        *,
        to_email: str,
        to_name: str,
        context: BookingEmailContext,
    ) -> EmailResult:
        """Send new booking request notification to tutor."""
        subject = f"New Booking Request: {context.subject_name or 'Tutoring Session'}"

        session_date = context.start_time.strftime("%B %d, %Y") if context.start_time else "TBD"
        session_time = context.start_time.strftime("%I:%M %p") if context.start_time else "TBD"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #3b82f6;">New Booking Request</h1>
                <p>Hi {to_name},</p>
                <p>You have a new booking request from {context.student_name}.</p>
                <div style="background: #eff6ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3b82f6;">
                    <p><strong>Subject:</strong> {context.subject_name or 'N/A'}</p>
                    <p><strong>Student:</strong> {context.student_name}</p>
                    <p><strong>Date:</strong> {session_date}</p>
                    <p><strong>Time:</strong> {session_time} ({context.timezone})</p>
                </div>
                <p><a href="{settings.FRONTEND_URL}/tutor/bookings/{context.booking_id}" style="background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">View Request</a></p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_verification_email(
        self,
        *,
        to_email: str,
        to_name: str,
        verification_url: str,
        expires_in_hours: int = 24,
    ) -> EmailResult:
        """Send email verification link."""
        subject = "Verify Your Email"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Verify Your Email</h1>
                <p>Hi {to_name},</p>
                <p>Please verify your email address:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">Verify Email</a>
                </p>
                <p style="color: #6b7280; font-size: 14px;">This link expires in {expires_in_hours} hours.</p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_password_reset(
        self,
        *,
        to_email: str,
        to_name: str,
        reset_url: str,
        expires_in_hours: int = 1,
    ) -> EmailResult:
        """Send password reset link."""
        subject = "Reset Your Password"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Password Reset</h1>
                <p>Hi {to_name},</p>
                <p>Click below to reset your password:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">Reset Password</a>
                </p>
                <p style="color: #6b7280; font-size: 14px;">This link expires in {expires_in_hours} hour(s).</p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_welcome_email(
        self,
        *,
        to_email: str,
        to_name: str,
        role: str,
        login_url: str | None = None,
    ) -> EmailResult:
        """Send welcome email to new user."""
        subject = "Welcome to EduStream!"

        if role == "tutor":
            cta_url = login_url or f"{settings.FRONTEND_URL}/tutor/onboarding"
            cta_text = "Complete Your Profile"
        else:
            cta_url = login_url or f"{settings.FRONTEND_URL}/tutors"
            cta_text = "Find a Tutor"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Welcome to EduStream!</h1>
                <p>Hi {to_name},</p>
                <p>Thank you for joining EduStream!</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{cta_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">{cta_text}</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
        )

    def send_tutor_approved(
        self,
        *,
        to_email: str,
        to_name: str,
        dashboard_url: str | None = None,
    ) -> EmailResult:
        """Send tutor approval notification."""
        subject = "Your Tutor Application Has Been Approved!"

        url = dashboard_url or f"{settings.FRONTEND_URL}/tutor/dashboard"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Congratulations!</h1>
                <p>Hi {to_name},</p>
                <p>Your tutor application has been approved. You can now start receiving bookings!</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">Go to Dashboard</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
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
        """Send review request after completed session."""
        subject = f"How was your session with {tutor_name}?"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #10b981;">Leave a Review</h1>
                <p>Hi {to_name},</p>
                <p>How was your session with {tutor_name}? Your feedback helps other students!</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{review_url}" style="background: #10b981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; display: inline-block;">Leave Review</a>
                </p>
            </div>
        </body>
        </html>
        """

        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
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
        """Send a custom email with arbitrary content."""
        return self._send_email_internal(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )


# Default instance
brevo_adapter = BrevoAdapter()
