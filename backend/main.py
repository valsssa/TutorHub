"""Main FastAPI application - Student-Tutor Booking Platform MVP."""

import logging
import os

# Configure logging to stderr
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_password_hash
from core.config import settings
from core.dependencies import get_current_admin_user
from core.middleware import SecurityHeadersMiddleware
from core.response_cache import ResponseCacheMiddleware
from database import get_db
from models import TutorProfile, User
from modules.admin.audit.router import router as audit_router
from modules.admin.presentation.api import router as admin_router

# Import module routers
from modules.auth.presentation.api import router as auth_router
from modules.bookings.presentation.api import router as bookings_router
from modules.messages.api import router as messages_router
from modules.messages.websocket import router as websocket_router
from modules.notifications.presentation.api import router as notifications_router
from modules.packages.presentation.api import router as packages_router
from modules.profiles.presentation.api import router as profiles_router
from modules.reviews.presentation.api import router as reviews_router
from modules.students.presentation.api import router as students_router
from modules.subjects.presentation.api import router as subjects_router
from modules.tutor_profile.presentation.api import router as tutor_profile_router
from modules.tutor_profile.presentation.availability_api import (
    router as availability_router,
)
from modules.users.avatar.router import router as avatar_router
from modules.users.currency.router import router as currency_router
from modules.users.preferences.router import router as preferences_router
from modules.utils.presentation.api import router as utils_router

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

# Initialize rate limiter (shared instance)
limiter = Limiter(key_func=get_remote_address)


# ============================================================================
# Lifespan Event - Create Default Users and Setup
# ============================================================================


async def create_default_users():
    """Create default admin, tutor, and student users."""
    logger.info("Starting default users creation...")

    # Use a fresh database session
    from sqlalchemy.orm import Session

    from database import engine

    db = Session(bind=engine)
    try:
        # Create admin
        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
        logger.debug(f"Checking for admin user: {admin_email}")
        if not db.query(User).filter(User.email == admin_email).first():
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash(
                    os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
                ),
                role="admin",
                is_verified=True,
            )
            db.add(admin)
            logger.info(f"Created default admin: {admin_email}")
        else:
            logger.debug(f"Admin user already exists: {admin_email}")

        # Create student
        student_email = os.getenv("DEFAULT_STUDENT_EMAIL", "student@example.com")
        logger.debug(f"Checking for student user: {student_email}")
        if not db.query(User).filter(User.email == student_email).first():
            student = User(
                email=student_email,
                hashed_password=get_password_hash(
                    os.getenv("DEFAULT_STUDENT_PASSWORD", "student123")
                ),
                role="student",
                is_verified=True,
            )
            db.add(student)
            logger.info(f"Created default student: {student_email}")
        else:
            logger.debug(f"Student user already exists: {student_email}")

        # Commit non-tutor users first
        db.commit()

        # Create tutor (with proper profile creation via DDD event handler)
        tutor_email = os.getenv("DEFAULT_TUTOR_EMAIL", "tutor@example.com")
        logger.debug(f"Checking for tutor user: {tutor_email}")
        existing_tutor = db.query(User).filter(User.email == tutor_email).first()
        if not existing_tutor:
            # Create user first with student role (will be changed to tutor)
            tutor = User(
                email=tutor_email,
                hashed_password=get_password_hash(
                    os.getenv("DEFAULT_TUTOR_PASSWORD", "tutor123")
                ),
                role="student",  # Start as student, then change to tutor
                is_verified=True,
            )
            db.add(tutor)
            db.flush()  # Get user ID
            
            # Now change role to tutor using DDD event handler (creates profile) and update with demo data
            from modules.users.domain.events import UserRoleChanged
            from modules.users.domain.handlers import RoleChangeEventHandler
            from datetime import datetime, timezone as tz
            
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
            tutor.updated_at = datetime.now(tz.utc)
            
            db.flush()
            
            # Now update the created profile with demo data
            tutor_profile = (
                db.query(TutorProfile).filter(TutorProfile.user_id == tutor.id).first()
            )
            if tutor_profile:
                tutor_profile.title = "Experienced Math and Science Tutor"
                tutor_profile.headline = "10+ years teaching experience"
                tutor_profile.bio = "Passionate about helping students excel in STEM subjects."
                tutor_profile.hourly_rate = 45.00
                tutor_profile.experience_years = 10
                tutor_profile.education = "Master's in Education"
                tutor_profile.languages = ["English", "Spanish"]
                tutor_profile.is_approved = True
                tutor_profile.profile_status = "approved"
                tutor_profile.updated_at = datetime.now(tz.utc)
                
            db.commit()
            logger.info(f"Created default tutor with approved profile: {tutor_email}")
        else:
            logger.debug(f"Tutor user already exists: {tutor_email}")

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
    
    # 1. Run database migrations (auto-apply schema changes)
    from core.migrations import run_startup_migrations
    from database import engine
    db = Session(bind=engine)
    try:
        run_startup_migrations(db)
    finally:
        db.close()
    
    # 2. Create default users
    await create_default_users()

    logger.info("✓ Application started successfully")
    yield
    # Shutdown
    logger.info("Application shutting down")


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
]

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
1. **Register**: `POST /auth/register` → Get JWT token
2. **Login**: `POST /auth/login` → Refresh token
3. **Protected Endpoints**: Include `Authorization: Bearer <token>` header
4. **Role Requirements**: Check endpoint descriptions for required roles

## 🔗 Base URLs
- **Production**: https://api.valsa.solutions
- **Documentation**: https://api.valsa.solutions/docs
- **ReDoc**: https://api.valsa.solutions/redoc
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
    servers=[
        {
            "url": "https://api.valsa.solutions",
            "description": "Production server",
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development server (Docker)",
        },
    ],
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
raw_cors_origins = os.getenv("CORS_ORIGINS")
if raw_cors_origins:
    CORS_ORIGINS = [
        origin.strip().rstrip("/")
        for origin in raw_cors_origins.split(",")
        if origin.strip()
    ]
else:
    CORS_ORIGINS = [origin.rstrip("/") for origin in settings.CORS_ORIGINS]

ENV = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
logger.info("CORS allowed origins: %s", CORS_ORIGINS)
logger.info("Runtime environment: %s", ENV)

# In production, be more restrictive
if ENV == "production":
    ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["Authorization", "Content-Type", "Accept"]
else:
    ALLOWED_METHODS = ["*"]
    ALLOWED_HEADERS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    max_age=600,  # Cache preflight for 10 minutes
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add response caching middleware
app.add_middleware(ResponseCacheMiddleware)

# Add response compression (processes before CORSMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# Add SlowAPI middleware for rate limiting enforcement
app.add_middleware(SlowAPIMiddleware)

# ============================================================================
# Register Module Routers
# ============================================================================

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(students_router)
app.include_router(subjects_router)
app.include_router(bookings_router)
app.include_router(reviews_router)
app.include_router(messages_router)
app.include_router(notifications_router)
app.include_router(packages_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(avatar_router)
app.include_router(preferences_router)
app.include_router(currency_router)
app.include_router(tutor_profile_router)
app.include_router(availability_router)
app.include_router(utils_router)
app.include_router(websocket_router)


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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "database": "disconnected",
            },
        )


@app.get(
    "/api/health/integrity",
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
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        403: {
            "description": "Forbidden - requires admin role",
            "content": {
                "application/json": {"example": {"detail": "Admin access required"}}
            },
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
