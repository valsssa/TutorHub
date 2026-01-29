"""Application configuration and constants."""

import json
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _safe_json_loads(value):
    """Allow plain strings for env values that are expected to be JSON."""
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return stripped
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return stripped


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "TutorConnect API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", os.urandom(32).hex() if os.getenv("DEBUG") == "true" else None),
        min_length=32,
        description="Secret key for JWT signing (minimum 32 characters)",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure SECRET_KEY is properly set in production."""
        if v is None:
            raise ValueError(
                "SECRET_KEY must be set in environment variables for production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v == "your-secret-key-min-32-characters-long-change-in-production":
            raise ValueError("Default SECRET_KEY detected! You must set a custom SECRET_KEY in production.")
        return v

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/authapp"

    # CORS
    CORS_ORIGINS: list[str] | str = [
        "https://edustream.valsa.solutions",
        "http://edustream.valsa.solutions",
        "https://api.valsa.solutions",
        "http://api.valsa.solutions",
    ]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REGISTRATION: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "20/minute"

    # Default Users - SECURITY: Passwords must be set via environment variables
    # If not set, secure random passwords will be generated and logged ONCE on first startup
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str | None = None  # Must be set via env or will be auto-generated
    DEFAULT_TUTOR_EMAIL: str = "tutor@example.com"
    DEFAULT_TUTOR_PASSWORD: str | None = None  # Must be set via env or will be auto-generated
    DEFAULT_STUDENT_EMAIL: str = "student@example.com"
    DEFAULT_STUDENT_PASSWORD: str | None = None  # Must be set via env or will be auto-generated

    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production

    # Validation
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_MAX_LENGTH: int = 128
    EMAIL_MAX_LENGTH: int = 254
    MAX_BOOKING_HOURS: int = 8

    # Pagination
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 100

    # Avatar Storage (MinIO / S3-compatible)
    AVATAR_STORAGE_ENDPOINT: str = "http://minio:9000"
    AVATAR_STORAGE_ACCESS_KEY: str = "minioadmin"
    AVATAR_STORAGE_SECRET_KEY: str = "minioadmin123"
    AVATAR_STORAGE_BUCKET: str = "user-avatars"
    AVATAR_STORAGE_REGION: str | None = None
    AVATAR_STORAGE_USE_SSL: bool = True
    AVATAR_STORAGE_PUBLIC_ENDPOINT: str | None = "https://minio.valsa.solutions"
    AVATAR_STORAGE_URL_TTL_SECONDS: int = 300
    AVATAR_STORAGE_DEFAULT_URL: str = "https://placehold.co/300x300?text=Avatar"

    # Message Attachment Storage (MinIO / S3-compatible) - Separate bucket for security
    MESSAGE_ATTACHMENT_STORAGE_ENDPOINT: str = "http://minio:9000"
    MESSAGE_ATTACHMENT_STORAGE_ACCESS_KEY: str = "minioadmin"
    MESSAGE_ATTACHMENT_STORAGE_SECRET_KEY: str = "minioadmin123"
    MESSAGE_ATTACHMENT_STORAGE_BUCKET: str = "message-attachments"
    MESSAGE_ATTACHMENT_STORAGE_REGION: str | None = None
    MESSAGE_ATTACHMENT_STORAGE_USE_SSL: bool = True
    MESSAGE_ATTACHMENT_STORAGE_PUBLIC_ENDPOINT: str | None = "https://minio.valsa.solutions"
    MESSAGE_ATTACHMENT_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MESSAGE_ATTACHMENT_MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5 MB
    MESSAGE_ATTACHMENT_URL_TTL_SECONDS: int = 3600  # 1 hour

    # Stripe Payment Configuration
    STRIPE_SECRET_KEY: str | None = None  # sk_test_... or sk_live_...
    STRIPE_PUBLISHABLE_KEY: str | None = None  # pk_test_... or pk_live_...
    STRIPE_WEBHOOK_SECRET: str | None = None  # whsec_...
    STRIPE_CONNECT_CLIENT_ID: str | None = None  # ca_... for Connect OAuth
    STRIPE_CURRENCY: str = "usd"  # Default currency for payments
    STRIPE_SUCCESS_URL: str = "https://edustream.valsa.solutions/bookings/{booking_id}?payment=success"
    STRIPE_CANCEL_URL: str = "https://edustream.valsa.solutions/bookings/{booking_id}?payment=cancelled"
    STRIPE_CONNECT_REFRESH_URL: str = "https://edustream.valsa.solutions/tutor/earnings?connect=refresh"
    STRIPE_CONNECT_RETURN_URL: str = "https://edustream.valsa.solutions/tutor/earnings?connect=success"

    # Google OAuth/OIDC Configuration
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str = "https://edustream.valsa.solutions/api/auth/google/callback"
    GOOGLE_CALENDAR_REDIRECT_URI: str = "https://api.valsa.solutions/api/integrations/calendar/callback"
    OAUTH_STATE_SECRET: str | None = None  # For CSRF protection

    # Brevo (Sendinblue) Email Configuration
    BREVO_API_KEY: str | None = None
    BREVO_SENDER_EMAIL: str = "noreply@edustream.valsa.solutions"
    BREVO_SENDER_NAME: str = "EduStream"
    EMAIL_ENABLED: bool = True

    # Zoom Video Integration
    ZOOM_CLIENT_ID: str | None = None
    ZOOM_CLIENT_SECRET: str | None = None
    ZOOM_ACCOUNT_ID: str | None = None  # For Server-to-Server OAuth
    ZOOM_REDIRECT_URI: str = "https://edustream.valsa.solutions/api/integrations/zoom/callback"

    # Sentry Error Monitoring
    SENTRY_DSN: str | None = None  # Sentry DSN for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions sampled
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% of transactions profiled

    # Frontend URLs for OAuth redirects
    FRONTEND_URL: str = "https://edustream.valsa.solutions"
    FRONTEND_LOGIN_SUCCESS_URL: str = "https://edustream.valsa.solutions/dashboard"
    FRONTEND_LOGIN_ERROR_URL: str = "https://edustream.valsa.solutions/login?error=oauth_failed"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return []
            if cleaned.startswith("[") and cleaned.endswith("]"):
                parsed = _safe_json_loads(cleaned)
                if isinstance(parsed, str):
                    raise ValueError("Invalid JSON for CORS_ORIGINS")
                return [item.strip().rstrip("/") for item in parsed if isinstance(item, str) and item.strip()]
            return [item.strip().rstrip("/") for item in cleaned.split(",") if item.strip()]

        if isinstance(value, list):
            return [item.strip().rstrip("/") for item in value if isinstance(item, str)]

        raise ValueError("CORS_ORIGINS must be a string or list of strings")


# Global settings instance
settings = Settings()


# API Constants
class APIConfig:
    """API-related constants."""

    PREFIX = "/api"
    V1_PREFIX = f"{PREFIX}"

    # Endpoints
    AUTH_PREFIX = "/auth"
    USERS_PREFIX = "/users"
    TUTORS_PREFIX = "/tutors"
    BOOKINGS_PREFIX = "/bookings"
    REVIEWS_PREFIX = "/reviews"
    MESSAGES_PREFIX = "/messages"
    SUBJECTS_PREFIX = "/subjects"
    ADMIN_PREFIX = "/admin"
    NOTIFICATIONS_PREFIX = "/notifications"


# Role Constants
class Roles:
    """User role constants."""

    STUDENT = "student"
    TUTOR = "tutor"
    ADMIN = "admin"
    OWNER = "owner"  # Super-admin with financial/business analytics access

    ALL = [STUDENT, TUTOR, ADMIN, OWNER]

    # Role hierarchy for access control
    # Higher index = more privileges
    HIERARCHY = {
        STUDENT: 0,
        TUTOR: 1,
        ADMIN: 2,
        OWNER: 3,  # Highest privilege level
    }

    @classmethod
    def has_admin_access(cls, role: str) -> bool:
        """Check if role has admin-level access (admin or owner)."""
        return role in [cls.ADMIN, cls.OWNER]

    @classmethod
    def is_owner(cls, role: str) -> bool:
        """Check if role is owner."""
        return role == cls.OWNER


# Booking Status Constants (State Machine)
class BookingStatus:
    """Booking status constants following marketplace state machine."""

    PENDING = "pending"  # Created by student, awaiting tutor confirmation
    CONFIRMED = "confirmed"  # Live session scheduled
    CANCELLED_BY_STUDENT = "cancelled_by_student"
    CANCELLED_BY_TUTOR = "cancelled_by_tutor"
    NO_SHOW_STUDENT = "no_show_student"  # Student didn't attend
    NO_SHOW_TUTOR = "no_show_tutor"  # Tutor didn't attend
    COMPLETED = "completed"  # Session finished successfully
    REFUNDED = "refunded"  # Payment refunded (terminal financial state)

    # Legal state transitions
    TRANSITIONS = {
        PENDING: [CONFIRMED, CANCELLED_BY_STUDENT, CANCELLED_BY_TUTOR],
        CONFIRMED: [
            CANCELLED_BY_STUDENT,
            CANCELLED_BY_TUTOR,
            NO_SHOW_STUDENT,
            NO_SHOW_TUTOR,
            COMPLETED,
        ],
        CANCELLED_BY_STUDENT: [REFUNDED],
        CANCELLED_BY_TUTOR: [REFUNDED],
        NO_SHOW_TUTOR: [REFUNDED],
        COMPLETED: [REFUNDED],  # Exception via admin only
    }

    ALL = [
        PENDING,
        CONFIRMED,
        CANCELLED_BY_STUDENT,
        CANCELLED_BY_TUTOR,
        NO_SHOW_STUDENT,
        NO_SHOW_TUTOR,
        COMPLETED,
        REFUNDED,
    ]


# Proficiency Levels
class ProficiencyLevels:
    """Subject proficiency level constants."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

    ALL = [BEGINNER, INTERMEDIATE, ADVANCED, EXPERT]
