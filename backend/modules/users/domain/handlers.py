"""Event handlers for user domain events."""

import logging
from decimal import Decimal

from sqlalchemy.orm import Session

from models import Booking, TutorProfile
from modules.users.domain.events import UserRoleChanged

logger = logging.getLogger(__name__)


class RoleChangeEventHandler:
    """
    Handles side effects of role changes to maintain data consistency.

    This handler ensures that:
    - Users with role='tutor' always have a tutor_profiles record
    - Users without role='tutor' don't have active tutor_profiles records
    - Historical data (bookings, reviews) is preserved during role changes
    """

    def handle(self, db: Session, event: UserRoleChanged) -> None:
        """
        Process a role change event and apply necessary side effects.

        Args:
            db: Database session (must be within an active transaction)
            event: The role change event to process
        """
        if event.is_becoming_tutor():
            self._handle_role_to_tutor(db, event)

        if event.is_leaving_tutor():
            self._handle_role_from_tutor(db, event)

    def _handle_role_to_tutor(self, db: Session, event: UserRoleChanged) -> None:
        """
        Ensure tutor profile exists when role changes to tutor.

        Creates a new incomplete tutor profile if one doesn't exist.
        If an archived profile exists, it will be reactivated.
        """
        existing = (
            db.query(TutorProfile).filter(TutorProfile.user_id == event.user_id).first()
        )

        from datetime import datetime, timezone
        
        if existing:
            # Reactivate archived profile
            if existing.profile_status == "archived":
                existing.profile_status = "incomplete"
                existing.is_approved = False
                existing.updated_at = datetime.now(timezone.utc)  # Update timestamp in code
                db.flush()
                logger.info(
                    "Reactivated archived tutor_profiles for user %s "
                    "(role change by admin %s)",
                    event.user_id,
                    event.changed_by,
                )
            else:
                logger.debug("Tutor profile already exists for user %s", event.user_id)
        else:
            # Create new tutor profile
            profile = TutorProfile(
                user_id=event.user_id,
                title="",
                headline=None,
                bio=None,
                description=None,
                hourly_rate=Decimal("1.00"),
                experience_years=0,
                languages=[],
                profile_status="incomplete",
                is_approved=False,
            )
            # Note: created_at and updated_at will be set by server_default
            db.add(profile)
            db.flush()
            logger.info(
                "Auto-created tutor_profiles for user %s " "(role change by admin %s)",
                event.user_id,
                event.changed_by,
            )

    def _handle_role_from_tutor(self, db: Session, event: UserRoleChanged) -> None:
        """
        Archive tutor profile when role changes away from tutor.

        The profile is archived (soft-deleted) rather than deleted to:
        - Preserve historical booking and review data
        - Allow potential role reversion without data loss
        - Maintain referential integrity

        The profile becomes invisible in public listings and cannot be edited.
        """
        profile = (
            db.query(TutorProfile).filter(TutorProfile.user_id == event.user_id).first()
        )

        if not profile:
            logger.warning(
                "No tutor_profiles found to archive for user %s "
                "(role changed from tutor to %s)",
                event.user_id,
                event.new_role,
            )
            return

        # Check if profile has historical data
        has_bookings = self._has_bookings(db, profile.id)

        if profile.profile_status == "archived":
            logger.debug("Tutor profile already archived for user %s", event.user_id)
            return

        # Always soft-delete to preserve relationships
        from datetime import datetime, timezone
        old_status = profile.profile_status
        profile.is_approved = False
        profile.profile_status = "archived"
        profile.updated_at = datetime.now(timezone.utc)  # Update timestamp in code
        db.flush()

        logger.info(
            "Archived tutor_profiles for user %s "
            "(role changed from tutor to %s, had bookings: %s, old status: %s) "
            "by admin %s",
            event.user_id,
            event.new_role,
            has_bookings,
            old_status,
            event.changed_by,
        )

    @staticmethod
    def _has_bookings(db: Session, tutor_profile_id: int) -> bool:
        """Check if a tutor profile has any associated bookings."""
        return (
            db.query(Booking)
            .filter(Booking.tutor_profile_id == tutor_profile_id)
            .limit(1)
            .first()
            is not None
        )
