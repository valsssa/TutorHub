"""Data integrity validation and repair utilities."""

import logging
from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models import TutorProfile, User

logger = logging.getLogger(__name__)


class DataIntegrityChecker:
    """
    Validates and reports data consistency issues.

    This utility helps identify and optionally repair inconsistencies
    between users.role and related profile tables (especially tutor_profiles).
    """

    @staticmethod
    def check_role_profile_consistency(db: Session) -> dict:
        """
        Check for role-profile mismatches.

        Identifies two types of inconsistencies:
        1. Users with role='tutor' but no tutor_profiles record
        2. Users with role!='tutor' but active (non-archived) tutor_profiles record

        Args:
            db: Database session

        Returns:
            Dictionary with findings:
            {
                'tutors_without_profiles': [user_ids],
                'profiles_without_tutor_role': [user_ids],
                'is_consistent': bool,
                'total_issues': int
            }
        """
        # Find tutors without profiles
        tutors_no_profile = (
            db.query(User.id)
            .filter(
                and_(
                    User.role == "tutor",
                    ~User.id.in_(db.query(TutorProfile.user_id)),
                )
            )
            .all()
        )

        # Find active profiles for non-tutors (archived profiles are OK)
        profiles_no_role = (
            db.query(User.id)
            .join(TutorProfile, User.id == TutorProfile.user_id)
            .filter(and_(User.role != "tutor", TutorProfile.profile_status != "archived"))
            .all()
        )

        tutors_missing = [row[0] for row in tutors_no_profile]
        profiles_orphaned = [row[0] for row in profiles_no_role]

        is_consistent = not tutors_missing and not profiles_orphaned
        total_issues = len(tutors_missing) + len(profiles_orphaned)

        if not is_consistent:
            logger.warning(
                "Role-profile inconsistency detected: "
                "%d tutors without profiles, "
                "%d active profiles without tutor role",
                len(tutors_missing),
                len(profiles_orphaned),
            )

        return {
            "tutors_without_profiles": tutors_missing,
            "profiles_without_tutor_role": profiles_orphaned,
            "is_consistent": is_consistent,
            "total_issues": total_issues,
        }

    @staticmethod
    def auto_repair_consistency(db: Session) -> dict:
        """
        Automatically fix consistency issues.

        Repairs:
        - Creates missing tutor_profiles for users with role='tutor'
        - Archives active tutor_profiles for users with role!='tutor'

        Args:
            db: Database session (changes will be committed)

        Returns:
            Dictionary with repair summary:
            {
                'profiles_created': int,
                'profiles_archived': int,
                'total_fixed': int,
                'details': {...}
            }
        """
        issues = DataIntegrityChecker.check_role_profile_consistency(db)

        profiles_created = 0
        profiles_archived = 0

        # Create missing profiles
        for user_id in issues["tutors_without_profiles"]:
            try:
                profile = TutorProfile(
                    user_id=user_id,
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
                db.add(profile)
                profiles_created += 1
                logger.info("Auto-created tutor_profiles for user %s", user_id)
            except Exception as exc:
                logger.error("Failed to create tutor_profiles for user %s: %s", user_id, exc)

        # Archive orphaned profiles
        for user_id in issues["profiles_without_tutor_role"]:
            try:
                updated = (
                    db.query(TutorProfile)
                    .filter(TutorProfile.user_id == user_id)
                    .update(
                        {
                            "is_approved": False,
                            "profile_status": "archived",
                        },
                        synchronize_session="fetch",
                    )
                )
                if updated > 0:
                    profiles_archived += 1
                    logger.info("Archived orphaned tutor_profiles for user %s", user_id)
            except Exception as exc:
                logger.error("Failed to archive tutor_profiles for user %s: %s", user_id, exc)

        if profiles_created > 0 or profiles_archived > 0:
            db.commit()
            logger.info(
                "Auto-repair completed: %d profiles created, %d profiles archived",
                profiles_created,
                profiles_archived,
            )
        else:
            logger.info("No repairs needed - database is consistent")

        return {
            "profiles_created": profiles_created,
            "profiles_archived": profiles_archived,
            "total_fixed": profiles_created + profiles_archived,
            "details": issues,
        }

    @staticmethod
    def get_consistency_report(db: Session) -> dict:
        """
        Generate a comprehensive consistency report.

        Args:
            db: Database session

        Returns:
            Dictionary with detailed statistics:
            {
                'total_users': int,
                'tutor_users': int,
                'tutor_profiles': int,
                'active_profiles': int,
                'archived_profiles': int,
                'issues': {...},
                'health_status': 'healthy' | 'warning' | 'critical'
            }
        """
        total_users = db.query(User).count()
        tutor_users = db.query(User).filter(User.role == "tutor").count()
        tutor_profiles = db.query(TutorProfile).count()
        active_profiles = db.query(TutorProfile).filter(TutorProfile.profile_status != "archived").count()
        archived_profiles = db.query(TutorProfile).filter(TutorProfile.profile_status == "archived").count()

        issues = DataIntegrityChecker.check_role_profile_consistency(db)

        # Determine health status
        if issues["is_consistent"]:
            health_status = "healthy"
        elif issues["total_issues"] <= 5:
            health_status = "warning"
        else:
            health_status = "critical"

        return {
            "total_users": total_users,
            "tutor_users": tutor_users,
            "tutor_profiles": tutor_profiles,
            "active_profiles": active_profiles,
            "archived_profiles": archived_profiles,
            "issues": issues,
            "health_status": health_status,
        }
