"""Package expiration service - Mark expired packages automatically."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from models import StudentPackage, TutorSubject

logger = logging.getLogger(__name__)


class PackageExpirationService:
    """Service to handle package expiration logic."""

    @staticmethod
    def mark_expired_packages(db: Session) -> int:
        """
        Mark all expired packages as 'expired' status.

        Returns:
            int: Number of packages marked as expired
        """
        try:
            now = datetime.now(UTC)
            # Find active packages that have passed their expiration date
            expired_packages = (
                db.query(StudentPackage)
                .filter(
                    and_(
                        StudentPackage.status == "active",
                        StudentPackage.expires_at.isnot(None),
                        StudentPackage.expires_at < now,
                    )
                )
                .all()
            )

            count = len(expired_packages)

            if count > 0:
                for package in expired_packages:
                    package.status = "expired"
                    package.updated_at = datetime.now(UTC)

                db.commit()

                logger.info(f"Marked {count} packages as expired")
            else:
                logger.debug("No expired packages found")

            return count

        except Exception as e:
            db.rollback()
            logger.error(f"Error marking expired packages: {e}")
            raise

    @staticmethod
    def check_package_validity(package: StudentPackage) -> tuple[bool, str | None]:
        """
        Check if a package is valid for use.

        Args:
            package: StudentPackage to check

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check status
        if package.status != "active":
            return False, f"Package is {package.status}, cannot use credits"

        # Check sessions remaining
        if package.sessions_remaining <= 0:
            return False, "No credits remaining in package"

        # Check expiration
        if package.expires_at and package.expires_at < datetime.now(UTC):
            return False, "Package has expired"

        return True, None

    @staticmethod
    def check_package_validity_for_checkout(
        package: StudentPackage,
    ) -> tuple[bool, bool, str | None]:
        """
        Check if a package is valid specifically for checkout completion.

        This method is used during webhook processing to detect if a package
        expired during the checkout process. Unlike check_package_validity(),
        this returns additional information about whether the package expired
        during checkout (as opposed to being invalid from the start).

        Args:
            package: StudentPackage to check

        Returns:
            tuple: (is_valid, expired_during_checkout, error_message)
                - is_valid: Whether the package can be used
                - expired_during_checkout: True if package was likely valid when
                  checkout started but expired since then
                - error_message: Description of the issue if not valid
        """
        now = datetime.now(UTC)

        # Check sessions remaining - this wouldn't change during checkout
        if package.sessions_remaining <= 0:
            return False, False, "No credits remaining in package"

        # Check expiration - could have expired during checkout
        if package.expires_at and package.expires_at < now:
            return False, True, f"Package expired at {package.expires_at.isoformat()}"

        # Check status - could have been marked expired by scheduler during checkout
        if package.status != "active":
            # If status is 'expired', it likely expired during checkout
            expired_during = package.status == "expired"
            return False, expired_during, f"Package status is {package.status}"

        return True, False, None

    @staticmethod
    def get_active_packages_for_student(db: Session, student_id: int) -> list[StudentPackage]:
        """
        Get all active, non-expired packages for a student.

        Args:
            db: Database session
            student_id: Student user ID

        Returns:
            list: Active StudentPackage instances
        """
        return (
            db.query(StudentPackage)
            .filter(
                and_(
                    StudentPackage.student_id == student_id,
                    StudentPackage.status == "active",
                    StudentPackage.sessions_remaining > 0,
                    (
                        StudentPackage.expires_at.is_(None)
                        | (StudentPackage.expires_at > datetime.now(UTC))
                    ),
                )
            )
            .order_by(StudentPackage.expires_at.asc().nullslast())  # Expiring first
            .all()
        )

    @staticmethod
    def get_expiring_packages(db: Session, days_until_expiry: int = 7) -> list[StudentPackage]:
        """
        Get packages that will expire within the specified number of days.

        This is used to send warning notifications to students about their
        expiring packages so they can use remaining credits before expiration.

        Args:
            db: Database session
            days_until_expiry: Number of days to look ahead (default 7)

        Returns:
            list: StudentPackage instances expiring soon that haven't had
                  a warning notification sent yet
        """
        now = datetime.now(UTC)
        cutoff = now + timedelta(days=days_until_expiry)

        return (
            db.query(StudentPackage)
            .options(joinedload(StudentPackage.tutor_profile))
            .filter(
                and_(
                    StudentPackage.status == "active",
                    StudentPackage.sessions_remaining > 0,
                    StudentPackage.expires_at.isnot(None),
                    StudentPackage.expires_at <= cutoff,
                    StudentPackage.expires_at > now,
                    StudentPackage.expiry_warning_sent.is_(False),
                )
            )
            .all()
        )

    @staticmethod
    def send_expiry_warnings(db: Session, days_until_expiry: int = 7) -> int:
        """
        Send expiration warning notifications for packages expiring soon.

        This method finds packages expiring within the specified number of days
        that haven't had a warning sent yet, sends notifications, and marks
        them as warned to avoid duplicate notifications.

        Args:
            db: Database session
            days_until_expiry: Number of days to look ahead (default 7)

        Returns:
            int: Number of warnings sent
        """
        from modules.notifications.service import notification_service

        try:
            expiring_packages = PackageExpirationService.get_expiring_packages(
                db, days_until_expiry
            )

            if not expiring_packages:
                logger.debug("No expiring packages found to warn about")
                return 0

            warnings_sent = 0
            now = datetime.now(UTC)

            for package in expiring_packages:
                try:
                    # Calculate days until expiry
                    if package.expires_at:
                        days_left = (package.expires_at - now).days
                        if days_left < 0:
                            days_left = 0
                    else:
                        continue

                    # Get subject name from tutor profile if available
                    subject_name = "tutoring"
                    if package.tutor_profile:
                        # Try to get a subject name from tutor's subjects
                        tutor_subject = (
                            db.query(TutorSubject)
                            .filter(TutorSubject.tutor_profile_id == package.tutor_profile_id)
                            .first()
                        )
                        if tutor_subject and tutor_subject.subject:
                            subject_name = tutor_subject.subject.name

                    # Send notification
                    notification_service.notify_package_expiring(
                        db=db,
                        user_id=package.student_id,
                        package_id=package.id,
                        subject_name=subject_name,
                        remaining_sessions=package.sessions_remaining,
                        expires_in_days=days_left,
                    )

                    # Mark warning as sent
                    package.expiry_warning_sent = True
                    package.updated_at = datetime.now(UTC)
                    warnings_sent += 1

                    logger.info(
                        f"Sent expiry warning for package {package.id} to student "
                        f"{package.student_id} - expires in {days_left} days, "
                        f"{package.sessions_remaining} sessions remaining"
                    )

                except Exception as e:
                    logger.error(
                        f"Error sending expiry warning for package {package.id}: {e}"
                    )
                    continue

            db.commit()
            logger.info(f"Sent {warnings_sent} package expiry warnings")
            return warnings_sent

        except Exception as e:
            db.rollback()
            logger.error(f"Error in send_expiry_warnings: {e}")
            raise
