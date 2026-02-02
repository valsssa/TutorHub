# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EduStream is a student-tutor booking platform MVP with role-based access control.

**Stack**: FastAPI (Python 3.12) + Next.js 15 (TypeScript) + PostgreSQL 17 + Redis + MinIO

**Roles**: admin, tutor, student, owner

## Essential Commands

### Fast Development (Recommended)

```bash
# Quick start with Makefile (recommended)
make dev          # Start dev environment (backend + frontend + db)
make minimal      # Start minimal (backend + db + redis only) - FASTEST
make full         # Start all services including Celery workers

# Or use docker-compose.fast.yml directly
docker compose -f docker-compose.fast.yml up db redis backend -d        # Minimal
docker compose -f docker-compose.fast.yml up db redis minio backend frontend -d  # Dev
docker compose -f docker-compose.fast.yml --profile workers up -d       # Full

# View logs
make logs         # All services
make logs-b       # Backend only
make logs-f       # Frontend only

# Stop and clean
make stop         # Stop all services
make clean        # Stop and remove volumes
```

### Standard Development (Legacy)

```bash
# Start all services (slower, includes lint stages)
docker compose up --build -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Clean reset (removes volumes)
docker compose down -v
```

### Production Build

```bash
# Build production images
docker compose -f docker-compose.prod.yml build --parallel

# Deploy production
docker compose -f docker-compose.prod.yml up -d
```

### Testing

```bash
# Full test suite (lint + unit + integration + E2E)
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Individual test suites
docker compose -f docker-compose.test.yml up backend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up frontend-tests --abort-on-container-exit
docker compose -f docker-compose.test.yml up e2e-tests --abort-on-container-exit

# Local single test (from repo root)
pytest tests/test_favorites.py::test_add_favorite_tutor -v
```

### Linting

```bash
# All linting (check mode)
./scripts/lint-all.sh

# Fix mode
./scripts/lint-all.sh --fix
./scripts/lint-backend.sh --fix   # Backend only (Ruff, Mypy, Bandit)
./scripts/lint-frontend.sh --fix  # Frontend only (ESLint, Prettier, TypeScript)
```

### Database

```bash
docker compose exec db psql -U postgres -d authapp
```

## Architecture

### Backend Structure (`backend/`)

Feature-based modular architecture with three patterns based on complexity:

**Full DDD** (`bookings/`, `auth/`): `domain/` → `application/` → `infrastructure/` → `presentation/`

**Service + Presentation** (`packages/`, `notifications/`, `messages/`): `services/` → `presentation/`

**Presentation Only** (`reviews/`, `favorites/`): Direct `api.py` routes

Key directories:
- `core/` - Shared utilities: config, security, dependencies, middleware, storage, email, calendar, Stripe, audit, pagination, caching
- `modules/` - 15+ feature modules (auth, bookings, payments, packages, messages, tutors, etc.)
- `models/` - SQLAlchemy ORM models organized by domain

### Frontend Structure (`frontend/`)

Next.js 15 App Router with protected routes and role-based UI:
- `app/` - Pages: dashboard, admin, owner, tutor/, tutors/, bookings/, messages/, settings/, packages/, wallet/
- `components/` - Reusable React components including ProtectedRoute HOC
- `lib/` - Auth utilities and helpers

### Booking State Machine

The bookings module uses a four-field status system (`backend/modules/bookings/domain/`):
- `SessionState`: pending_tutor, pending_student, confirmed, in_progress, completed, cancelled, expired, no_show
- `SessionOutcome`: pending, successful, failed, cancelled, disputed
- `PaymentState`: pending, authorized, captured, refunded, released_to_tutor, failed
- `DisputeState`: none, filed, under_review, resolved_student_favor, resolved_tutor_favor

State transitions are enforced by `BookingStateMachine` class. Background jobs handle auto-transitions (expire, start, end sessions).

### Background Task Processing (Celery)

The project uses Celery with Redis for reliable background task processing:

**Architecture**:
- `backend/core/celery_app.py` - Celery configuration with Redis broker
- `backend/tasks/booking_tasks.py` - Booking state transition tasks
- `celery-worker` service - Processes tasks from Redis queue
- `celery-beat` service - Schedules periodic tasks

**Tasks**:
- `expire_requests`: REQUESTED -> EXPIRED (every 5 min, 24h timeout)
- `start_sessions`: SCHEDULED -> ACTIVE (every 1 min, at start_time)
- `end_sessions`: ACTIVE -> ENDED (every 1 min, at end_time + grace)

**Commands**:
```bash
# View Celery worker logs
docker compose logs -f celery-worker

# View Celery beat logs
docker compose logs -f celery-beat

# Enable Flower monitoring (uncomment in docker-compose.yml)
# Access at http://localhost:5555
```

**Migration from APScheduler**:
The legacy APScheduler implementation in `core/scheduler.py` and `modules/bookings/jobs.py` is deprecated but retained for backwards compatibility. Celery provides persistent queues, retry logic with exponential backoff, and monitoring capabilities.

### Database

Schema in `database/init.sql`. Migrations in `database/migrations/` (34+ SQL files). Uses soft delete with `deleted_at` timestamps on most tables.

### Clean Architecture (Port/Adapter Pattern)

All external services are accessed via ports (interfaces) and adapters (implementations):

**Ports** (`core/ports/`): Protocol interfaces defining contracts
- `PaymentPort` - Stripe operations (checkout, refunds, webhooks)
- `EmailPort` - Email sending (Brevo/SendinBlue)
- `StoragePort` - File storage (MinIO/S3)
- `CachePort` - Caching and distributed locks (Redis)
- `MeetingPort` - Video meetings (Zoom, Google Meet)
- `CalendarPort` - Calendar operations (Google Calendar)

**Adapters** (`core/adapters/`): Real implementations wrapping external SDKs
- `StripeAdapter`, `BrevoAdapter`, `MinIOAdapter`, `RedisAdapter`, `ZoomAdapter`, `GoogleCalendarAdapter`

**Fakes** (`core/fakes/`): In-memory implementations for testing
- `FakePayment`, `FakeEmail`, `FakeStorage`, `FakeCache`, `FakeMeeting`, `FakeCalendar`

**Usage in routes**:
```python
from core.dependencies import get_payment_port

@router.post("/checkout")
async def create_checkout(
    payment: Annotated[PaymentPort, Depends(get_payment_port)]
):
    result = await payment.create_checkout_session(...)
```

### Domain Layer Structure

Each module's `domain/` directory contains:
- `entities.py` - Pure dataclasses (no SQLAlchemy)
- `value_objects.py` - Immutable validated primitives
- `repositories.py` - Protocol interfaces for data access
- `exceptions.py` - Domain-specific exceptions

**Example**:
```python
# domain/entities.py
@dataclass
class BookingEntity:
    id: int | None
    student_id: int
    session_state: SessionState
    # ... pure data, no ORM

# domain/repositories.py
class BookingRepository(Protocol):
    def get_by_id(self, booking_id: int) -> BookingEntity | None: ...
    def create(self, booking: BookingEntity) -> BookingEntity: ...
```

### Domain Events

Centralized event dispatcher for cross-module communication:
```python
from core.events import event_dispatcher, BookingCreatedEvent

# Publish event
await event_dispatcher.publish(BookingCreatedEvent(
    booking_id=123,
    student_id=456,
))

# Register handler
@event_dispatcher.on("BookingCreatedEvent")
async def handle_booking_created(event: BookingCreatedEvent):
    # Send notification, update stats, etc.
```

## Key Patterns

### Protected Backend Endpoints

```python
from core.dependencies import get_current_user, get_current_admin_user

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    ...

@router.get("/admin-only")
async def admin_route(current_user: User = Depends(get_current_admin_user)):
    ...
```

### Adding New Modules

1. Create directory in `backend/modules/` with appropriate structure
2. Add `__init__.py` files
3. Register router in `backend/main.py` with API v1 prefix
4. Add tests

```python
# modules/my_feature/api.py
# NOTE: Router prefix does NOT include /api - added centrally in main.py
router = APIRouter(prefix="/my-feature", tags=["my-feature"])

# main.py
from modules.my_feature.api import router as my_feature_router
API_V1_PREFIX = "/api/v1"
app.include_router(my_feature_router, prefix=API_V1_PREFIX)
```

### API Versioning

All API endpoints are versioned under `/api/v1`:
- Router prefixes use just the resource name (e.g., `/auth`, `/bookings`)
- The version prefix (`/api/v1`) is added centrally in `main.py`
- Future breaking changes will be introduced under `/api/v2`

## Code Quality Requirements

- 100% type-hint coverage
- Max file length ~300 lines
- Logging through centralized config (no `print()`)
- snake_case for variables/functions, PascalCase for classes
- Run full test suite before committing

## Architecture Verification

Run the architecture verification script to check clean architecture compliance:
```bash
./backend/scripts/verify-architecture.sh
```

Checks performed:
- No SQLAlchemy imports in domain layers
- No FastAPI imports in domain layers
- No ORM model imports in domain layers
- External SDKs only imported in adapters

## Documentation

- [Project spec](project_spec.md) - Full requirements, API specs, tech details
- [Architecture](docs/architecture.md) - System design and data flow
- [Clean Architecture Guide](docs/architecture/clean-architecture-guide.md) - Port/adapter, repository, testing patterns
- [ADR: Clean Architecture](docs/architecture/decisions/011-clean-architecture.md) - Decision record
- [Modules README](backend/modules/README.md) - Module structure templates
- [Changelog](docs/changelog.md) - Version history
- [Project status](docs/project_status.md) - Current progress
- Update files in the docs folder after major milestones and major additions to the project

## Feature Implementation System Guidelines

### Feature Implementation Priority Rules
- IMMEDIATE EXECUTION: Launch parallel Tasks immediately upon feature requests.
- NO CLARIFICATION: Skip asking what type of implementation unless absolutely critical.
- PARALLEL BY DEFAULT: Always use 7-parallel-Task method for efficiency.

### Parallel Feature Implementation Workflow
1. **Component:** Create main component file.
2. **Styles:** Create component styles/CSS.
3. **Tests:** Create test files.
4. **Types:** Create type definitions.
5. **Hooks:** Create custom hooks/utilities.
6. **Integration:** Update routing, imports, exports.
7. **Remaining:** Update package.json, documentation, configuration files.
8. **Review and Validation:** Coordinate integration, run tests, verify build, check for conflicts.

### Context Optimization Rules
- Strip out all comments when reading code files for analysis.
- Each task handles ONLY specified files or file types.
- Task 7 combines small config/doc updates to prevent over-splitting.

### Feature Implementation Guidelines
- **CRITICAL:** Make MINIMAL CHANGES to existing patterns and structures.
- **CRITICAL:** Preserve existing naming conventions and file organization.
- Follow project's established architecture and component patterns.
- Use existing utility functions and avoid duplicating functionality.