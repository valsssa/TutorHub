"""Sentry error monitoring configuration."""

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from core.config import settings

logger = logging.getLogger(__name__)


def _is_valid_sentry_dsn(dsn: str | None) -> bool:
    """
    Validate that a Sentry DSN has proper format.

    Valid DSN format: https://<key>@<host>/<project_id>
    """
    if not dsn:
        return False

    dsn = dsn.strip()

    # Check for placeholder values
    if dsn.lower() in ("your_sentry_dsn", "your-sentry-dsn", "placeholder", "none", "null", ""):
        return False

    # Must start with https:// and contain @ and a numeric project ID
    if not dsn.startswith("https://"):
        return False

    if "@" not in dsn:
        return False

    # Check for sentry.io or custom sentry hostname
    if ".sentry.io/" not in dsn and ".ingest.sentry.io/" not in dsn:
        # Could be self-hosted Sentry, still check basic format
        parts = dsn.split("@")
        if len(parts) != 2:
            return False

    return True


def init_sentry() -> bool:
    """
    Initialize Sentry error tracking.

    Returns True if Sentry was initialized, False if skipped (no DSN configured or invalid).
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return False

    if not _is_valid_sentry_dsn(settings.SENTRY_DSN):
        logger.warning(
            "Invalid Sentry DSN format detected: '%s'. Error tracking disabled. "
            "Set a valid DSN (https://<key>@<host>/<project_id>) or remove SENTRY_DSN to disable.",
            settings.SENTRY_DSN[:20] + "..." if len(settings.SENTRY_DSN) > 20 else settings.SENTRY_DSN,
        )
        return False

    # Configure Sentry logging integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors and above as events
    )

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            sentry_logging,
        ],
        # Performance monitoring
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        # Environment
        environment=settings.ENVIRONMENT,
        release=f"edustream-backend@{settings.APP_VERSION}",
        # Additional options
        send_default_pii=False,  # Don't send PII by default
        attach_stacktrace=True,
        # Filter out sensitive data
        before_send=_before_send,
        before_send_transaction=_before_send_transaction,
    )

    logger.info(
        "Sentry initialized for environment: %s (traces: %.0f%%, profiles: %.0f%%)",
        settings.ENVIRONMENT,
        settings.SENTRY_TRACES_SAMPLE_RATE * 100,
        settings.SENTRY_PROFILES_SAMPLE_RATE * 100,
    )
    return True


def _before_send(event: dict, hint: dict) -> dict | None:
    """
    Filter or modify events before sending to Sentry.

    - Remove sensitive data
    - Filter out expected errors
    """
    # Filter out 401/403 errors (expected authentication failures)
    if "exception" in event:
        for exception in event.get("exception", {}).get("values", []):
            if exception.get("type") == "HTTPException":
                # Check if it's a 401 or 403 - these are expected
                exc_value = hint.get("exc_info", [None, None, None])[1]
                if exc_value and hasattr(exc_value, "status_code"):
                    if exc_value.status_code in (401, 403, 404, 422):
                        return None  # Don't send these to Sentry

    # Remove sensitive headers
    if "request" in event:
        headers = event["request"].get("headers", {})
        sensitive_headers = ["authorization", "cookie", "x-api-key"]
        for header in sensitive_headers:
            if header in headers:
                headers[header] = "[Filtered]"

    # Remove sensitive body fields
    if "request" in event and "data" in event["request"]:
        data = event["request"]["data"]
        if isinstance(data, dict):
            sensitive_fields = ["password", "token", "secret", "api_key", "credit_card"]
            for field in sensitive_fields:
                if field in data:
                    data[field] = "[Filtered]"

    return event


def _before_send_transaction(event: dict, hint: dict) -> dict | None:
    """
    Filter transactions before sending to Sentry.

    - Skip health check transactions
    - Skip high-volume, low-value transactions
    """
    transaction_name = event.get("transaction", "")

    # Skip health checks
    if transaction_name in ("/health", "/api/health/integrity"):
        return None

    # Skip static file requests
    if transaction_name.startswith("/static/") or transaction_name.startswith("/_next/"):
        return None

    return event


def capture_exception(exception: Exception, **extra_context) -> str | None:
    """
    Capture an exception to Sentry with optional extra context.

    Returns the Sentry event ID if captured, None otherwise.
    """
    if not settings.SENTRY_DSN:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra_context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_exception(exception)


def capture_message(message: str, level: str = "info", **extra_context) -> str | None:
    """
    Capture a message to Sentry with optional extra context.

    Returns the Sentry event ID if captured, None otherwise.
    """
    if not settings.SENTRY_DSN:
        return None

    with sentry_sdk.push_scope() as scope:
        for key, value in extra_context.items():
            scope.set_extra(key, value)
        return sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: int, email: str | None = None, role: str | None = None) -> None:
    """Set user context for Sentry events."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.set_user({
        "id": str(user_id),
        "email": email,
        "role": role,
    })


def clear_user_context() -> None:
    """Clear user context from Sentry."""
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.set_user(None)
