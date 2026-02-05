"""Main FastAPI application - Student-Tutor Booking Platform MVP."""

import logging
import os

# Configure logging to stderr
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from io import BytesIO

from fastapi import Depends, FastAPI, HTTPException, Request

# Initialize Sentry early (before other imports that might error)
from core.sentry import init_sentry

sentry_initialized = init_sentry()

# Initialize tracing early
from core.tracing import init_tracing, shutdown_tracing  # noqa: E402

tracing_initialized = init_tracing()
# CORSMiddleware imported via core.cors.setup_cors  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, StreamingResponse  # noqa: E402
from slowapi.errors import RateLimitExceeded  # noqa: E402
from slowapi.middleware import SlowAPIMiddleware  # noqa: E402
from sqlalchemy import func  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from auth import get_password_hash  # noqa: E402
from core.config import settings  # noqa: E402
from core.cors import setup_cors  # noqa: E402
from core.dependencies import get_current_admin_user  # noqa: E402
from core.csrf_middleware import CSRFMiddleware  # noqa: E402
from core.middleware import SecurityHeadersMiddleware  # noqa: E402
from core.rate_limiting import limiter  # noqa: E402
from core.response_cache import ResponseCacheMiddleware  # noqa: E402
from core.tracing_middleware import TracingMiddleware  # noqa: E402
from core.transactions import atomic_operation  # noqa: E402
from database import get_db  # noqa: E402
from models import TutorProfile, User  # noqa: E402
from modules.admin.audit.router import router as audit_router  # noqa: E402
from modules.admin.feature_flags_router import (  # noqa: E402
    public_router as feature_flags_public_router,
)
from modules.admin.feature_flags_router import (  # noqa: E402
    router as feature_flags_router,
)
from modules.admin.owner.router import router as owner_router  # noqa: E402
from modules.admin.presentation.api import router as admin_router  # noqa: E402
from modules.auth.email_verification_router import router as email_verification_router  # noqa: E402
from modules.auth.oauth_router import router as oauth_router  # noqa: E402
from modules.auth.password_router import router as password_router  # noqa: E402

# Import module routers
from modules.auth.presentation.api import router as auth_router  # noqa: E402
from modules.bookings.presentation.api import router as bookings_router  # noqa: E402
from modules.integrations.calendar_router import router as calendar_router  # noqa: E402
from modules.integrations.zoom_router import router as zoom_router  # noqa: E402
from modules.messages.api import router as messages_router  # noqa: E402
from modules.messages.websocket import router as websocket_router  # noqa: E402
from modules.notifications.presentation.api import router as notifications_router  # noqa: E402
from modules.packages.presentation.api import router as packages_router  # noqa: E402
from modules.payments.connect_router import admin_connect_router  # noqa: E402
from modules.payments.connect_router import router as connect_router  # noqa: E402
from modules.payments.router import router as payments_router  # noqa: E402
from modules.payments.wallet_router import router as wallet_router  # noqa: E402
from modules.profiles.presentation.api import router as profiles_router  # noqa: E402
from modules.public.router import router as public_router  # noqa: E402
from modules.reviews.presentation.api import router as reviews_router  # noqa: E402
from modules.students.presentation.api import favorites_router  # noqa: E402
from modules.students.presentation.api import router as students_router  # noqa: E402
from modules.subjects.presentation.api import router as subjects_router  # noqa: E402
from modules.tutor_profile.presentation.api import router as tutor_profile_router  # noqa: E402
from modules.tutor_profile.presentation.availability_api import (  # noqa: E402
    router as availability_router,
)
from modules.tutors.student_notes_router import router as student_notes_router  # noqa: E402
from modules.tutors.video_settings_router import router as video_settings_router  # noqa: E402
from modules.users.avatar.router import router as avatar_router  # noqa: E402
from modules.users.currency.router import router as currency_router  # noqa: E402
from modules.users.preferences.router import router as preferences_router  # noqa: E402
from modules.utils.presentation.api import router as utils_router  # noqa: E402

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Note: limiter is imported from core.rate_limiting (shared instance)


# ============================================================================
# Lifespan Event - Create Default Users and Setup
# ============================================================================


def _generate_secure_password() -> str:
    """Generate a secure random password."""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(16))


def _get_or_generate_password(env_var: str, user_type: str) -> tuple[str, bool]:
    """
    Get password from environment or generate a secure one.
    Returns (password, was_generated) tuple.
    """
    password = os.getenv(env_var)
    if password:
        return password, False

    # Generate secure password
    generated = _generate_secure_password()
    return generated, True


async def create_default_users():
    """Create default admin, tutor, and student users."""
    logger.info("Starting default users creation...")

    # Use a fresh database session
    from sqlalchemy.orm import Session

    from database import engine

    db = Session(bind=engine)
    generated_credentials = []  # Track auto-generated passwords

    try:
        # Create admin
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        logger.debug(f"Checking for admin user: {admin_email}")
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            admin_password, was_generated = _get_or_generate_password("DEFAULT_ADMIN_PASSWORD", "admin")
            if was_generated:
                generated_credentials.append(("ADMIN", admin_email, admin_password))

            admin = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                role="admin",
                is_verified=True,
                first_name="Admin",
                last_name="User",
            )
            db.add(admin)
            logger.info(f"Created default admin: {admin_email}")
        else:
            # Update existing admin if missing names
            logger.debug(f"Admin exists, first_name: '{existing_admin.first_name}', last_name: '{existing_admin.last_name}'")
            if not existing_admin.first_name or not existing_admin.last_name:
                existing_admin.first_name = existing_admin.first_name or "Admin"
                existing_admin.last_name = existing_admin.last_name or "User"
                logger.info(f"Updated default admin with names: {admin_email}")
            else:
                logger.debug(f"Admin user already exists with names: {admin_email}")

        # Create owner (highest privilege level)
        owner_email = os.getenv("DEFAULT_OWNER_EMAIL", "owner@example.com")
        logger.debug(f"Checking for owner user: {owner_email}")
        existing_owner = db.query(User).filter(User.email == owner_email).first()
        if not existing_owner:
            owner_password, was_generated = _get_or_generate_password("DEFAULT_OWNER_PASSWORD", "owner")
            if was_generated:
                generated_credentials.append(("OWNER", owner_email, owner_password))

            owner = User(
                email=owner_email,
                hashed_password=get_password_hash(owner_password),
                role="owner",
                is_verified=True,
                first_name="Owner",
                last_name="User",
            )
            db.add(owner)
            logger.info(f"Created default owner: {owner_email}")
        else:
            # Update existing owner if missing names
            logger.debug(f"Owner exists, first_name: '{existing_owner.first_name}', last_name: '{existing_owner.last_name}'")
            if not existing_owner.first_name or not existing_owner.last_name:
                existing_owner.first_name = existing_owner.first_name or "Owner"
                existing_owner.last_name = existing_owner.last_name or "User"
                logger.info(f"Updated default owner with names: {owner_email}")
            else:
                logger.debug(f"Owner user already exists with names: {owner_email}")

        # Create student
        student_email = os.getenv("DEFAULT_STUDENT_EMAIL", "student@example.com")
        logger.debug(f"Checking for student user: {student_email}")
        existing_student = db.query(User).filter(User.email == student_email).first()
        if not existing_student:
            student_password, was_generated = _get_or_generate_password("DEFAULT_STUDENT_PASSWORD", "student")
            if was_generated:
                generated_credentials.append(("STUDENT", student_email, student_password))

            student = User(
                email=student_email,
                hashed_password=get_password_hash(student_password),
                role="student",
                is_verified=True,
                first_name="Demo",
                last_name="Student",
            )
            db.add(student)
            logger.info(f"Created default student: {student_email}")
        else:
            # Update existing student if missing names
            logger.debug(f"Student exists, first_name: '{existing_student.first_name}', last_name: '{existing_student.last_name}'")
            if not existing_student.first_name or not existing_student.last_name:
                existing_student.first_name = existing_student.first_name or "Demo"
                existing_student.last_name = existing_student.last_name or "Student"
                logger.info(f"Updated default student with names: {student_email}")
                db.commit()  # Commit immediately after update
            else:
                logger.debug(f"Student user already exists with names: {student_email}")

        # Commit non-tutor users first (in case new users were added)
        db.commit()

        # Create tutor (with proper profile creation via DDD event handler)
        tutor_email = os.getenv("DEFAULT_TUTOR_EMAIL", "tutor@example.com")
        logger.debug(f"Checking for tutor user: {tutor_email}")
        existing_tutor = db.query(User).filter(User.email == tutor_email).first()
        if not existing_tutor:
            tutor_password, was_generated = _get_or_generate_password("DEFAULT_TUTOR_PASSWORD", "tutor")
            if was_generated:
                generated_credentials.append(("TUTOR", tutor_email, tutor_password))

            # Use atomic transaction to ensure User + TutorProfile are created together
            # Prevents orphaned user without profile if profile creation fails
            with atomic_operation(db):
                # Create user first with student role (will be changed to tutor)
                tutor = User(
                    email=tutor_email,
                    hashed_password=get_password_hash(tutor_password),
                    role="student",  # Start as student, then change to tutor
                    is_verified=True,
                    first_name="Demo",
                    last_name="Tutor",
                )
                db.add(tutor)
                db.flush()  # Get user ID

                # Now change role to tutor using DDD event handler (creates profile)
                from modules.users.domain.events import UserRoleChanged
                from modules.users.domain.handlers import RoleChangeEventHandler

                event = UserRoleChanged(
                    user_id=tutor.id,
                    old_role="student",
                    new_role="tutor",
                    changed_by=tutor.id,  # Self-registration
                )

                handler = RoleChangeEventHandler()
                handler.handle(db, event)

                # Update user role
                tutor.role = "tutor"
                tutor.updated_at = datetime.now(UTC)

                db.flush()

                # Now update the created profile with demo data
                tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
                if tutor_profile:
                    tutor_profile.title = "Experienced Math and Science Tutor"
                    tutor_profile.headline = "10+ years teaching experience"
                    tutor_profile.bio = "Passionate about helping students excel in STEM subjects."
                    tutor_profile.hourly_rate = 45.00
                    tutor_profile.experience_years = 10
                    tutor_profile.education = "Master's in Education"
                    tutor_profile.languages = ["English", "Spanish"]
                    tutor_profile.video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Demo intro video
                    tutor_profile.is_approved = True
                    tutor_profile.profile_status = "approved"
                    tutor_profile.updated_at = datetime.now(UTC)
                # atomic_operation commits all changes together

            logger.info(f"Created default tutor with approved profile: {tutor_email}")
        else:
            logger.debug(f"Tutor user already exists: {tutor_email}")
            # Update existing tutor profile with video URL if missing
            tutor_profile = db.query(TutorProfile).filter(TutorProfile.user_id == existing_tutor.id).first()
            if tutor_profile and not tutor_profile.video_url:
                tutor_profile.video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # Demo intro video
                tutor_profile.updated_at = datetime.now(UTC)
                db.commit()
                logger.info(f"Updated existing tutor profile with demo video URL: {tutor_email}")

        # Log generated credentials (ONLY on first startup when users are created)
        if generated_credentials:
            logger.warning("=" * 70)
            logger.warning("SECURITY NOTICE: Auto-generated credentials for default users")
            logger.warning("SAVE THESE NOW - they will NOT be shown again!")
            logger.warning("Set these in environment variables for production:")
            logger.warning("-" * 70)
            for role, email, password in generated_credentials:
                logger.warning(f"  {role}: {email} / {password}")
                logger.warning(f"    Set: DEFAULT_{role}_PASSWORD={password}")
            logger.warning("-" * 70)
            logger.warning("For production, set these environment variables BEFORE first run.")
            logger.warning("=" * 70)

        logger.info("Default users creation completed successfully")
    except Exception as e:
        logger.error(f"Error creating default users: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("=== Application Startup ===")

    # 0. Log Sentry and tracing status
    if sentry_initialized:
        logger.info("Sentry error monitoring enabled")
    else:
        logger.info("Sentry error monitoring disabled (no DSN configured)")

    if tracing_initialized:
        logger.info("Distributed tracing enabled")
    else:
        logger.info("Distributed tracing disabled (TRACING_ENABLED=false)")

    # 1. Run database migrations (auto-apply schema changes)
    # Skip during tests when SKIP_STARTUP_MIGRATIONS is set
    if not os.environ.get("SKIP_STARTUP_MIGRATIONS"):
        from core.migrations import run_startup_migrations
        from database import engine

        db = Session(bind=engine)
        try:
            run_startup_migrations(db)
        finally:
            db.close()
    else:
        logger.info("Skipping startup migrations (SKIP_STARTUP_MIGRATIONS=true)")

    # 2. Create default users
    await create_default_users()

    # 3. Initialize feature flags
    try:
        from core.feature_flags import init_default_flags
        await init_default_flags()
        logger.info("Feature flags initialized")
    except Exception as e:
        logger.warning(f"Feature flags initialization failed (Redis may be unavailable): {e}")

    # 4. Set up OpenTelemetry instrumentation
    if tracing_initialized:
        try:
            from core.tracing import (
                configure_logging_with_trace_id,
                instrument_fastapi,
                instrument_httpx,
                instrument_requests,
                instrument_sqlalchemy,
            )
            from database import engine

            # Instrument components
            instrument_fastapi(app)
            instrument_sqlalchemy(engine)
            instrument_httpx()
            instrument_requests()
            configure_logging_with_trace_id()
            logger.info("OpenTelemetry instrumentation configured")
        except Exception as e:
            logger.warning(f"OpenTelemetry instrumentation failed: {e}")

    logger.info("Application started successfully")
    yield
    # Shutdown
    logger.info("Application shutting down")

    # Shutdown tracing (flush pending spans)
    if tracing_initialized:
        try:
            shutdown_tracing()
        except Exception as e:
            logger.debug("Error during tracing shutdown: %s", e)

    # Close feature flags Redis connection
    try:
        from core.feature_flags import feature_flags
        await feature_flags.close()
    except Exception as e:
        logger.debug("Error closing feature flags Redis connection: %s", e)


# OpenAPI Tags Metadata - Comprehensive API documentation structure
tags_metadata = [
    {
        "name": "auth",
        "description": """**Authentication and Authorization**

Secure user registration, login, and token-based session management. Supports three roles: student, tutor, and admin. All endpoints use JWT Bearer tokens with 30-minute expiry. Rate-limited to prevent abuse (5/min registration, 10/min login).""",
    },
    {
        "name": "users",
        "description": """**User Management**

User profile operations including preferences (currency, language), avatar management, and profile updates. Supports role-based access control with student/tutor/admin distinction.""",
    },
    {
        "name": "tutors",
        "description": """**Tutor Profiles and Discovery**

Comprehensive tutor profile management including education, certifications, experience, specializations, and availability. Public search and filtering for students. Supports tutor approval workflow for marketplace quality control.""",
    },
    {
        "name": "bookings",
        "description": """**Session Booking Management**

End-to-end booking lifecycle: creation, confirmation, rescheduling, cancellation, and completion. Supports package credits, calendar integration, and no-show reporting. State machine: PENDING → CONFIRMED → COMPLETED/CANCELLED.""",
    },
    {
        "name": "packages",
        "description": """**Tutor Packages and Pricing**

Tutors create session packages (e.g., "5 sessions for $200") with flexible pricing and session counts. Students purchase packages and consume credits per booking. Supports discounts and bulk pricing.""",
    },
    {
        "name": "reviews",
        "description": """**Ratings and Reviews**

Students review completed sessions with 1-5 star ratings and written feedback. Reviews are public and affect tutor average ratings. Supports review responses from tutors.""",
    },
    {
        "name": "messages",
        "description": """**Direct Messaging**

Real-time messaging between students and tutors. Supports conversation threads, unread counts, and message history. WebSocket support for live notifications (future enhancement).""",
    },
    {
        "name": "notifications",
        "description": """**Notification System**

Multi-channel notifications (in-app, email, push) for booking updates, messages, and system events. Supports user preferences for notification types and delivery methods.""",
    },
    {
        "name": "subjects",
        "description": """**Subject Taxonomy**

Hierarchical subject classification for tutor specializations and session topics. Used for search filtering and tutor matching.""",
    },
    {
        "name": "admin",
        "description": """**Admin Panel Operations**

Platform administration including user management, tutor approval workflow, analytics dashboards, and system monitoring. Restricted to admin role only.""",
    },
    {
        "name": "analytics",
        "description": """**Analytics and Reporting**

Business intelligence endpoints for revenue tracking, user growth, session metrics, and subject distribution. Supports date range filtering and export formats.""",
    },
    {
        "name": "audit",
        "description": """**Audit Logs**

Comprehensive audit trail for all critical operations (role changes, deletions, approvals). Immutable logs for compliance and security investigation.""",
    },
    {
        "name": "profiles",
        "description": """**Student and Tutor Profiles**

Extended profile information beyond basic user data. Students: learning goals, education level. Tutors: teaching philosophy, credentials, verification status.""",
    },
    {
        "name": "calendar",
        "description": """**Calendar and Availability**

Tutor availability management with recurring schedules and one-time blocks. Calendar view integration for booking conflicts and session scheduling.""",
    },
    {
        "name": "health",
        "description": """**Health and Monitoring**

System health checks, readiness probes, and service status endpoints. Used by load balancers and monitoring systems.""",
    },
    {
        "name": "integrations",
        "description": """**Third-Party Integrations**

External service integrations including Zoom video conferencing for virtual tutoring sessions. Handles OAuth flows, meeting creation, and lifecycle management.""",
    },
]

def _get_openapi_servers() -> list[dict]:
    """
    Build OpenAPI server list based on environment configuration.

    Uses BACKEND_URL environment variable if set, otherwise falls back to
    environment-appropriate defaults.
    """
    servers = []
    env = settings.ENVIRONMENT.lower()
    backend_url = os.getenv("BACKEND_URL")

    if backend_url:
        # Use explicitly configured backend URL
        servers.append({
            "url": f"{backend_url.rstrip('/')}/api/v1",
            "description": "API v1",
        })
    elif env == "production":
        # Production only shows production server
        servers.append({
            "url": "https://api.valsa.solutions/api/v1",
            "description": "Production API v1",
        })
    else:
        # Development/staging shows both for flexibility
        servers.append({
            "url": "http://localhost:8000/api/v1",
            "description": "Local development API v1",
        })
        # Also include production for reference in non-prod environments
        servers.append({
            "url": "https://api.valsa.solutions/api/v1",
            "description": "Production API v1",
        })

    return servers


# Create FastAPI app with lifespan and comprehensive OpenAPI metadata
app = FastAPI(
    title="EduStream - Student-Tutor Booking Platform",
    description="""
# EduStream API v1.0

**Production EdTech Marketplace** for connecting students with verified tutors.

## 🎯 Core Features
- **Multi-role Authentication**: JWT-based auth with student/tutor/admin roles
- **Tutor Marketplace**: Profile creation, approval workflow, search & filtering
- **Session Booking**: Package-based credits, calendar integration, state machine
- **Reviews & Ratings**: Public feedback system with tutor responses
- **Direct Messaging**: Real-time communication between students and tutors
- **Admin Dashboard**: Analytics, user management, audit logs

## 🔐 Security
- **Rate Limiting**: Per-endpoint limits (5/min registration, 10/min login)
- **JWT Tokens**: 30-minute expiry with Bearer authentication
- **Role-Based Access**: Enforced at API and database levels
- **Audit Logging**: Immutable trail for compliance

## 🏗️ Architecture
- **FastAPI**: Async Python 3.12 backend
- **PostgreSQL 17**: Optimized with indexes (60% faster queries)
- **Domain-Driven Design**: Modular structure by feature domain
- **12-Factor App**: Environment-based config, stateless services

## 📚 API Usage
1. **Register**: `POST /api/v1/auth/register` → Get JWT token
2. **Login**: `POST /api/v1/auth/login` → Refresh token
3. **Protected Endpoints**: Include `Authorization: Bearer <token>` header
4. **Role Requirements**: Check endpoint descriptions for required roles

## 🔗 Base URLs
- **Production API**: https://api.valsa.solutions/api/v1
- **Documentation**: https://api.valsa.solutions/docs
- **ReDoc**: https://api.valsa.solutions/redoc

## 🏷️ API Versioning
All endpoints are versioned under `/api/v1`. Future breaking changes will be introduced under `/api/v2`.
    """,
    version="1.0.0",
    contact={
        "name": "EduStream Support",
        "email": "support@valsa.solutions",
        "url": "https://edustream.valsa.solutions",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://edustream.valsa.solutions/terms",
    },
    terms_of_service="https://edustream.valsa.solutions/terms",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    servers=_get_openapi_servers(),
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter

# CORS Configuration - Single Source of Truth (core/cors.py)
# Sets up CORSMiddleware, CORSSafetyNetMiddleware, and exception handlers
setup_cors(app)

# Add tracing middleware (must be early to capture full request lifecycle)
app.add_middleware(TracingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add response caching middleware
app.add_middleware(ResponseCacheMiddleware)

# Add response compression (processes before CORSMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# Add SlowAPI middleware for rate limiting enforcement
app.add_middleware(SlowAPIMiddleware)

# Add CSRF protection middleware for HttpOnly cookie auth
# Auth endpoints are exempt since they need to set the initial cookies
app.add_middleware(
    CSRFMiddleware,
    exempt_paths=[
        "/api/v1/auth/*",  # All auth endpoints (login, register, refresh, logout)
        "/api/v1/webhooks/*",  # Webhook endpoints (Stripe, etc.) use their own verification
    ],
)

# ============================================================================
# Register Module Routers - API v1
# ============================================================================
# All API endpoints are versioned under /api/v1 prefix

API_V1_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_V1_PREFIX)
app.include_router(oauth_router, prefix=API_V1_PREFIX)
app.include_router(password_router, prefix=API_V1_PREFIX)
app.include_router(email_verification_router, prefix=API_V1_PREFIX)
app.include_router(profiles_router, prefix=API_V1_PREFIX)
app.include_router(students_router, prefix=API_V1_PREFIX)
app.include_router(favorites_router, prefix=API_V1_PREFIX)
app.include_router(subjects_router, prefix=API_V1_PREFIX)
app.include_router(bookings_router, prefix=API_V1_PREFIX)
app.include_router(reviews_router, prefix=API_V1_PREFIX)
app.include_router(messages_router, prefix=API_V1_PREFIX)
app.include_router(notifications_router, prefix=API_V1_PREFIX)
app.include_router(packages_router, prefix=API_V1_PREFIX)
app.include_router(payments_router, prefix=API_V1_PREFIX)
app.include_router(wallet_router, prefix=API_V1_PREFIX)
app.include_router(connect_router, prefix=API_V1_PREFIX)
app.include_router(admin_connect_router, prefix=API_V1_PREFIX)
app.include_router(admin_router, prefix=API_V1_PREFIX)
app.include_router(audit_router, prefix=API_V1_PREFIX)
app.include_router(owner_router, prefix=API_V1_PREFIX)
app.include_router(avatar_router, prefix=API_V1_PREFIX)
app.include_router(preferences_router, prefix=API_V1_PREFIX)
app.include_router(currency_router, prefix=API_V1_PREFIX)
app.include_router(tutor_profile_router, prefix=API_V1_PREFIX)
app.include_router(availability_router, prefix=API_V1_PREFIX)
app.include_router(student_notes_router, prefix=API_V1_PREFIX)
app.include_router(video_settings_router, prefix=API_V1_PREFIX)
app.include_router(utils_router, prefix=API_V1_PREFIX)
app.include_router(websocket_router, prefix=API_V1_PREFIX)
app.include_router(zoom_router, prefix=API_V1_PREFIX)
app.include_router(calendar_router, prefix=API_V1_PREFIX)
app.include_router(feature_flags_router, prefix=API_V1_PREFIX)
app.include_router(feature_flags_public_router, prefix=API_V1_PREFIX)
app.include_router(public_router, prefix=API_V1_PREFIX)


# ============================================================================
# Legacy Avatar Route - Handle old avatar URLs for tutor profile photos
# ============================================================================

@app.get("/api/v1/avatars/{user_id}/{filename:path}")
async def serve_legacy_avatar(
    user_id: int,
    filename: str,
    db: Session = Depends(get_db),
):
    """
    Legacy route to serve tutor profile photos stored with old avatar URL format.
    This handles URLs like /api/avatars/3/filename.webp and serves the actual
    tutor profile photo from MinIO storage.
    """
    from core.storage import MINIO_BUCKET, _s3_client

    # Get user to find their avatar_key (which contains the tutor profile photo URL)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.avatar_key:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Extract storage key from the avatar_key URL
    from core.storage import _extract_key_from_url
    storage_key = _extract_key_from_url(user.avatar_key)

    # If extraction failed, try to construct key from tutor_profiles path
    if not storage_key:
        # Try tutor_profiles path format
        storage_key = f"tutor_profiles/{user_id}/photo/{filename}"

    # Get file from MinIO
    try:
        client = _s3_client()
        response = client.get_object(Bucket=MINIO_BUCKET, Key=storage_key)
        content = response["Body"].read()
        content_type = response.get("ContentType", "image/jpeg")

        return StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
            },
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Photo not found in storage")


# ============================================================================
# Health Check
# ============================================================================


@app.get(
    "/health",
    tags=["health"],
    summary="System health check",
    description="""
**Health Check Endpoint**

Returns the current system health status including:
- API service status
- Database connectivity
- Timestamp for monitoring

**Use Cases**:
- Load balancer health probes
- Kubernetes readiness/liveness checks
- Monitoring system integrations
- Uptime status verification

**No Authentication Required** - Public endpoint for operational monitoring.
    """,
    responses={
        200: {
            "description": "System is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-10-21T10:30:00.000Z",
                        "database": "connected",
                    }
                }
            },
        },
        503: {
            "description": "System is unhealthy - database connection failed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-10-21T10:30:00.000Z",
                        "database": "disconnected",
                        "error": "Database connection timeout",
                    }
                }
            },
        },
    },
)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    try:
        # Test database connection
        db.execute(func.now())
        logger.debug("Database connection successful")
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(UTC).isoformat(),
                "database": "disconnected",
            },
        )


# CORS debug endpoints removed - use logs and browser DevTools for debugging
# See docs/CORS_DEBUGGING.md for troubleshooting guide


@app.get(
    "/api/v1/health/integrity",
    tags=["health"],
    summary="Data integrity check (admin only)",
    description="""
**Data Integrity Verification**

Validates database consistency between user roles and profile tables:
- Students must have student_profile records
- Tutors must have tutor_profile records
- Detects orphaned profiles and role mismatches

**Admin Only** - Requires admin role authentication.

**Use Cases**:
- Post-migration validation
- Scheduled integrity monitoring
- Troubleshooting profile-related bugs
- Audit trail verification

**Future Enhancement**: Add `?repair=true` query parameter to auto-fix inconsistencies.

**Response includes**:
- Health status: "healthy", "warnings", or "critical"
- Detailed consistency report
- Counts of mismatches and orphans
    """,
    responses={
        200: {
            "description": "Integrity check completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "report": {
                            "health_status": "healthy",
                            "total_users": 150,
                            "role_counts": {"student": 100, "tutor": 45, "admin": 5},
                            "issues": [],
                            "timestamp": "2025-10-21T10:30:00.000Z",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Not authenticated - missing or invalid JWT token",
            "content": {"application/json": {"example": {"detail": "Not authenticated"}}},
        },
        403: {
            "description": "Forbidden - requires admin role",
            "content": {"application/json": {"example": {"detail": "Admin access required"}}},
        },
    },
)
async def check_data_integrity(
    repair: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Check data integrity (admin only).

    Validates role-profile consistency and returns detailed report.
    Use with query parameter ?repair=true to auto-fix issues.
    """
    from core.integrity_checks import DataIntegrityChecker

    if repair:
        result = DataIntegrityChecker.auto_repair_consistency(db)
        return {
            "status": "repaired",
            "repairs": result,
        }
    else:
        result = DataIntegrityChecker.get_consistency_report(db)
        return {
            "status": result["health_status"],
            "report": result,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
