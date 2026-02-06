"""
Background jobs for package management.

Jobs run on schedule to:
- Send expiry warning notifications for packages expiring soon
- Mark expired packages as expired (already handled in expiration_service)

Multi-Instance Safety:
- Uses Redis distributed locks to prevent job overlap across server instances
- Locks auto-expire to prevent deadlocks if a pod crashes during execution
"""

import logging

from core.distributed_lock import distributed_lock
from core.tracing import trace_background_job
from database import SessionLocal
from modules.packages.services.expiration_service import PackageExpirationService

logger = logging.getLogger(__name__)

# Configuration
EXPIRY_WARNING_DAYS = 7  # Send warning when package expires within 7 days
EXPIRY_WARNING_LOCK_TIMEOUT = 300  # 5 minutes


async def send_package_expiry_warnings() -> None:
    """
    Send warning notifications for packages expiring soon.

    Runs daily (configured in scheduler).
    Sends notifications for packages expiring within EXPIRY_WARNING_DAYS days
    that haven't already received a warning.

    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:send_package_expiry_warnings", timeout=EXPIRY_WARNING_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "send_package_expiry_warnings job already running on another instance, skipping"
            )
            return

        with trace_background_job("send_package_expiry_warnings", interval="daily"):
            logger.debug("Running send_package_expiry_warnings job")

            db = SessionLocal()
            try:
                warnings_sent = PackageExpirationService.send_expiry_warnings(
                    db, days_until_expiry=EXPIRY_WARNING_DAYS
                )

                if warnings_sent > 0:
                    logger.info(f"Package expiry warnings job: sent {warnings_sent} warnings")
                else:
                    logger.debug("No package expiry warnings to send")

            except Exception as e:
                logger.error(f"Error in send_package_expiry_warnings job: {e}")
                db.rollback()
            finally:
                db.close()


async def mark_expired_packages() -> None:
    """
    Mark expired packages as expired status.

    Runs hourly (configured in scheduler).
    Finds active packages past their expiration date and marks them expired.

    Uses distributed locking to prevent overlap across server instances.
    """
    async with distributed_lock.acquire(
        "job:mark_expired_packages", timeout=EXPIRY_WARNING_LOCK_TIMEOUT
    ) as acquired:
        if not acquired:
            logger.info(
                "mark_expired_packages job already running on another instance, skipping"
            )
            return

        with trace_background_job("mark_expired_packages", interval="hourly"):
            logger.debug("Running mark_expired_packages job")

            db = SessionLocal()
            try:
                count = PackageExpirationService.mark_expired_packages(db)

                if count > 0:
                    logger.info(f"Mark expired packages job: marked {count} packages as expired")
                else:
                    logger.debug("No packages to mark as expired")

            except Exception as e:
                logger.error(f"Error in mark_expired_packages job: {e}")
                db.rollback()
            finally:
                db.close()
