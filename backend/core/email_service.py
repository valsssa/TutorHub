"""
Brevo (Sendinblue) Email Service

Handles all transactional email sending including:
- Booking confirmations
- Booking reminders
- Cancellation notifications
- Password reset
- Welcome emails
"""

import logging
from datetime import datetime
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Email Service Class
# ============================================================================


class EmailService:
    """Brevo transactional email service."""

    def __init__(self):
        self._client = None
        self._api = None

    def _get_client(self):
        """Lazy initialization of Brevo client."""
        if self._client is None:
            if not settings.BREVO_API_KEY:
                logger.warning("Brevo API key not configured - emails disabled")
                return None

            import sib_api_v3_sdk
            from sib_api_v3_sdk.rest import ApiException

            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key["api-key"] = settings.BREVO_API_KEY
            self._client = sib_api_v3_sdk.ApiClient(configuration)
            self._api = sib_api_v3_sdk.TransactionalEmailsApi(self._client)

        return self._api

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
        if not settings.EMAIL_ENABLED:
            logger.info(f"Email disabled - would send to {to_email}: {subject}")
            return True

        api = self._get_client()
        if not api:
            logger.warning(f"Email service not configured - skipping email to {to_email}")
            return False

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

            api.send_transac_email(send_smtp_email)
            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

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
        refund_info: str | None = None,
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

                {f'<div style="background: #ecfdf5; padding: 15px; border-radius: 8px; margin: 20px 0;"><p style="margin: 0;"><strong>Refund:</strong> {refund_info}</p></div>' if refund_info else ''}

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
