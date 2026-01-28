"""Package expiration service - Mark expired packages automatically."""

import logging
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models import StudentPackage

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
            # Find active packages that have passed their expiration date
            expired_packages = (
                db.query(StudentPackage)
                .filter(
                    and_(
                        StudentPackage.status == "active",
                        StudentPackage.expires_at.isnot(None),
                        StudentPackage.expires_at < datetime.utcnow(),
                    )
                )
                .all()
            )

            count = len(expired_packages)

            if count > 0:
                for package in expired_packages:
                    package.status = "expired"
                    package.updated_at = datetime.utcnow()

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
        if package.expires_at and package.expires_at < datetime.utcnow():
            return False, "Package has expired"

        return True, None

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
                        | (StudentPackage.expires_at > datetime.utcnow())
                    ),
                )
            )
            .order_by(StudentPackage.expires_at.asc().nullslast())  # Expiring first
            .all()
        )
