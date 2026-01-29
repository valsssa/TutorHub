# Backend Architecture

## 1. Architectural Style

### Layered DDD with Vertical Slices

The backend implements a hybrid architecture combining layered DDD for complex domains and simpler patterns for CRUD operations:

```
+------------------------------------------------------------------------------+
|                        PRESENTATION LAYER                                     |
|                (FastAPI routers, Pydantic schemas)                           |
+------------------------------------------------------------------------------+
|  modules/bookings/presentation/api.py  |  modules/reviews/api.py             |
|  modules/tutor_profile/presentation/   |  modules/favorites/api.py           |
|  modules/payments/...                  |  (simple CRUD routers)              |
+-------------------------------------+----------------------------------------+
                                      |
                                      v
+------------------------------------------------------------------------------+
|                        APPLICATION LAYER                                      |
|           (Services, DTOs, policy engines, use cases)                        |
+------------------------------------------------------------------------------+
|  modules/bookings/service.py           |  (N/A for simple CRUD)              |
|  modules/bookings/policy_engine.py     |                                     |
|  modules/packages/services/...         |                                     |
+-------------------------------------+----------------------------------------+
                                      |
                                      v
+------------------------------------------------------------------------------+
|                          DOMAIN LAYER                                         |
|         (Entities, value objects, state machines, domain events)             |
+------------------------------------------------------------------------------+
|  modules/bookings/domain/state_machine.py                                     |
|  modules/bookings/domain/status.py                                            |
|  (Pure Python, no framework dependencies)                                     |
+-------------------------------------+----------------------------------------+
                                      |
                                      v
+------------------------------------------------------------------------------+
|                      INFRASTRUCTURE LAYER                                     |
|        (SQLAlchemy models, repositories, external service clients)           |
+------------------------------------------------------------------------------+
|  models/*.py (ORM definitions)         |  core/stripe_client.py              |
|  database.py (connection pool)         |  core/email_service.py              |
|  core/storage.py (MinIO client)        |  core/google_calendar.py            |
+------------------------------------------------------------------------------+
```

## 2. Module Organization

### 18 Backend Modules

| Pattern | Modules | Structure |
|---------|---------|-----------|
| **Full DDD** | bookings, auth, tutor_profile | domain/ -> application/ -> infrastructure/ -> presentation/ |
| **Service + Presentation** | packages, notifications, messages, payments, admin | services/ -> presentation/ |
| **Presentation Only** | reviews, favorites, students, subjects, profiles, users, tutors, utils | api.py with inline logic |

### Directory Structure

```
backend/
+-- main.py                 # Application entry, router registration
+-- database.py             # SQLAlchemy engine, session factory
+-- core/                   # Shared utilities (27 modules)
|   +-- config.py           # Pydantic settings
|   +-- dependencies.py     # FastAPI dependency injection
|   +-- security.py         # JWT, password hashing
|   +-- transactions.py     # Transaction management
|   +-- middleware.py       # Security headers
|   +-- utils.py            # Common utilities
|   +-- stripe_client.py    # Payment integration
|   +-- email_service.py    # Email delivery
|   +-- storage.py          # MinIO file storage
|   +-- ...
+-- models/                 # SQLAlchemy ORM models
|   +-- base.py             # Base class, custom types
|   +-- auth.py             # User, UserProfile
|   +-- tutors.py           # 13 tutor-related models
|   +-- bookings.py         # Booking, SessionMaterial
|   +-- students.py         # StudentProfile, StudentPackage
|   +-- payments.py         # Payment, Refund, Payout
|   +-- ...
+-- modules/                # Feature modules
    +-- auth/               # Full DDD
    +-- bookings/           # Full DDD
    +-- tutor_profile/      # Full DDD
    +-- packages/           # Service + Presentation
    +-- notifications/      # Service + Presentation
    +-- messages/           # Service + Presentation
    +-- payments/           # Multiple routers
    +-- reviews/            # Simple CRUD
    +-- favorites/          # Simple CRUD
    +-- ...
```

## 3. Booking State Machine

### Four-Field State Model

The booking module uses a four-field state machine to decouple concerns:

```
+------------------------------------------------------------------------------+
|                         BOOKING STATE FIELDS                                  |
+------------------------------------------------------------------------------+

SESSION STATE (Lifecycle)
  REQUESTED ---> SCHEDULED ---> ACTIVE ---> ENDED (terminal)
      |              |            |
      +---> CANCELLED <-----------+
      +---> EXPIRED (24h timeout)

SESSION OUTCOME (Result, only on terminal states)
  COMPLETED | NOT_HELD | NO_SHOW_STUDENT | NO_SHOW_TUTOR

PAYMENT STATE (Money flow)
  PENDING ---> AUTHORIZED ---> CAPTURED ---> REFUNDED
      |            |                 +---> PARTIALLY_REFUNDED ---> REFUNDED
      +---> VOIDED <+

DISPUTE STATE (Conflict resolution)
  NONE ---> OPEN ---> RESOLVED_UPHELD
                 +---> RESOLVED_REFUNDED
```

### State Machine Implementation

**File**: `modules/bookings/domain/state_machine.py` (438 lines)

```python
class BookingStateMachine:
    """Enforces all valid state transitions."""

    SESSION_STATE_TRANSITIONS = {
        SessionState.REQUESTED: {SessionState.SCHEDULED, SessionState.CANCELLED, SessionState.EXPIRED},
        SessionState.SCHEDULED: {SessionState.ACTIVE, SessionState.CANCELLED},
        SessionState.ACTIVE: {SessionState.ENDED},
        # Terminal states
        SessionState.ENDED: set(),
        SessionState.CANCELLED: set(),
        SessionState.EXPIRED: set(),
    }

    @classmethod
    def can_transition_session_state(cls, current: SessionState, target: SessionState) -> bool:
        return target in cls.SESSION_STATE_TRANSITIONS.get(current, set())

    # High-level operations
    @classmethod
    def accept_booking(cls, booking: Booking) -> TransitionResult: ...
    @classmethod
    def decline_booking(cls, booking: Booking) -> TransitionResult: ...
    @classmethod
    def cancel_booking(cls, booking: Booking, cancelled_by: str, refund: bool) -> TransitionResult: ...
    @classmethod
    def expire_booking(cls, booking: Booking) -> TransitionResult: ...
    @classmethod
    def start_session(cls, booking: Booking) -> TransitionResult: ...
    @classmethod
    def end_session(cls, booking: Booking, outcome: SessionOutcome) -> TransitionResult: ...
    @classmethod
    def mark_no_show(cls, booking: Booking, who_was_absent: str) -> TransitionResult: ...
    @classmethod
    def open_dispute(cls, booking: Booking, reason: str, user_id: int) -> TransitionResult: ...
    @classmethod
    def resolve_dispute(cls, booking: Booking, resolution: str, ...) -> TransitionResult: ...
```

### Design Rationale

1. **Why four fields instead of one mega-status?**
   - Prevents combinatorial explosion (would need 40+ enum values)
   - Each concern evolves independently
   - Enables targeted queries ("all with open disputes")

2. **Why application-enforced instead of DB triggers?**
   - Testable in unit tests
   - Visible business logic in code
   - Easier debugging and tracing

## 4. Policy Engine

### Separation of Rules from Transitions

**File**: `modules/bookings/policy_engine.py` (301 lines)

```python
@dataclass
class PolicyDecision:
    allow: bool
    reason_code: str
    refund_cents: int = 0
    tutor_compensation_cents: int = 0
    apply_strike_to_tutor: bool = False
    restore_package_unit: bool = False
    message: str = ""

class CancellationPolicy:
    @staticmethod
    def evaluate_student_cancellation(booking: Booking) -> PolicyDecision:
        hours_until = (booking.start_time - datetime.now(UTC)).total_seconds() / 3600
        if hours_until >= 12:
            return PolicyDecision(allow=True, refund_cents=booking.rate_cents, ...)
        return PolicyDecision(allow=True, refund_cents=0, ...)  # No refund

    @staticmethod
    def evaluate_tutor_cancellation(booking: Booking) -> PolicyDecision:
        hours_until = (booking.start_time - datetime.now(UTC)).total_seconds() / 3600
        if hours_until < 12:
            return PolicyDecision(allow=True, apply_strike_to_tutor=True, ...)
        return PolicyDecision(allow=True, ...)
```

### Policy Types

| Policy | Purpose | Key Rules |
|--------|---------|-----------|
| CancellationPolicy | Cancellation refund logic | 12h threshold for refunds |
| ReschedulePolicy | Reschedule validation | Must be 24h+ before |
| NoShowPolicy | No-show reporting | 10min+ after start, within 24h |
| GraceEditPolicy | Post-creation edits | 5min grace period |

## 5. API Design

### REST API Structure

```
/api/auth/*           Authentication & OAuth
/api/users/*          User profile management
/api/tutors/*         Public tutor listings
/api/tutor/*          Authenticated tutor operations
/api/bookings/*       Booking lifecycle (student view)
/api/tutor/bookings/* Booking lifecycle (tutor view)
/api/admin/*          Admin operations
/api/owner/*          Owner analytics
/api/messages/*       Messaging
/api/notifications/*  Notifications
/api/packages/*       Package management
/api/reviews/*        Session reviews
/api/favorites/*      Saved tutors
```

### Authorization Patterns

```python
# Role-based access via dependency injection
@router.get("/admin-only")
async def admin_route(user: AdminUser):  # AdminUser = admin OR owner
    ...

@router.get("/owner-only")
async def owner_route(user: OwnerUser):  # OwnerUser = owner only
    ...

# Resource-based access
def _verify_booking_ownership(booking: Booking, current_user: User, db: Session) -> bool:
    if current_user.role == "student":
        return booking.student_id == current_user.id
    elif current_user.role == "tutor":
        tutor = get_tutor_profile(current_user.id, db)
        return booking.tutor_profile_id == tutor.id
    elif current_user.role in ("admin", "owner"):
        return True
    return False
```

### Request/Response Patterns

```python
# Request validation with Pydantic
class BookingCreateRequest(BaseModel):
    tutor_profile_id: int
    start_at: datetime  # UTC
    duration_minutes: int = Field(ge=15, le=180)
    lesson_type: Literal["TRIAL", "REGULAR", "PACKAGE"]
    subject_id: Optional[int] = None
    notes_student: Optional[str] = Field(max_length=2000)

# Response with DTO
class BookingDTO(BaseModel):
    id: int
    session_state: str
    session_outcome: Optional[str]
    payment_state: str
    dispute_state: str
    status: str  # Legacy computed field
    start_at: datetime
    end_at: datetime
    rate_cents: int
    tutor: TutorInfoDTO
    student: StudentInfoDTO
```

## 6. Background Jobs

### APScheduler Implementation

**File**: `modules/bookings/jobs.py` (174 lines)

```python
# Registered in main.py via core/scheduler.py

async def expire_requests():
    """Every 5 minutes: REQUESTED -> EXPIRED after 24h"""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    bookings = db.query(Booking).filter(
        Booking.session_state == SessionState.REQUESTED,
        Booking.created_at < cutoff
    ).all()
    for booking in bookings:
        BookingStateMachine.expire_booking(booking)
    db.commit()

async def start_sessions():
    """Every 1 minute: SCHEDULED -> ACTIVE at start_time"""
    now = datetime.now(UTC)
    bookings = db.query(Booking).filter(
        Booking.session_state == SessionState.SCHEDULED,
        Booking.start_time <= now
    ).all()
    for booking in bookings:
        BookingStateMachine.start_session(booking)
    db.commit()

async def end_sessions():
    """Every 1 minute: ACTIVE -> ENDED at end_time + 5min grace"""
    grace_cutoff = datetime.now(UTC) - timedelta(minutes=5)
    bookings = db.query(Booking).filter(
        Booking.session_state == SessionState.ACTIVE,
        Booking.end_time <= grace_cutoff
    ).all()
    for booking in bookings:
        BookingStateMachine.end_session(booking, SessionOutcome.COMPLETED)
    db.commit()
```

### Job Schedule

| Job | Interval | Purpose |
|-----|----------|---------|
| expire_requests | 5 min | Expire unanswered requests after 24h |
| start_sessions | 1 min | Transition to ACTIVE at start time |
| end_sessions | 1 min | Transition to ENDED after end + grace |

### Future Migration Path

| Aspect | APScheduler (Current) | Celery (Future) |
|--------|----------------------|-----------------|
| Persistence | In-memory | Redis-backed |
| Scaling | Single process | Multiple workers |
| Retry Logic | Manual | Built-in |
| Monitoring | Logs only | Flower dashboard |

## 7. Error Handling

### Centralized Error Decorator

```python
# core/utils.py
def handle_db_errors(operation_name: str, rollback: bool = True):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except IntegrityError as e:
                if rollback:
                    db.rollback()
                raise HTTPException(400, f"Data integrity error in {operation_name}")
            except Exception as e:
                if rollback:
                    db.rollback()
                logger.error(f"Error in {operation_name}: {e}")
                raise HTTPException(500, "Internal server error")
        return wrapper
    return decorator

# Usage
@router.post("/bookings")
@handle_db_errors("create booking", rollback=True)
async def create_booking(...):
    ...
```

### HTTP Status Codes

| Status | Usage |
|--------|-------|
| 200 | Success with response body |
| 201 | Resource created |
| 204 | Success without body |
| 400 | Validation error, business rule violation |
| 401 | Authentication required |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

## 8. Transaction Management

### Transaction Patterns

```python
# core/transactions.py

# Pattern 1: Context manager
with transaction(db):
    booking = create_booking(...)
    deduct_package_credits(...)
    # Auto-commit on exit, rollback on exception

# Pattern 2: Safe commit with error handling
if safe_commit(db, error_message="Failed to save"):
    return {"status": "success"}

# Pattern 3: Commit or raise HTTP exception
commit_or_raise(db, status.HTTP_400_BAD_REQUEST, "Invalid data")

# Pattern 4: Decorator for endpoints
@transactional
async def my_endpoint(db: Session = Depends(get_db)):
    # Automatic transaction handling
```

### Connection Pool Configuration

```python
# database.py
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,     # Validate connections
    pool_size=10,           # Base pool size
    max_overflow=20,        # Max additional connections
    pool_recycle=3600,      # Recycle after 1 hour
    pool_timeout=30,        # Wait timeout
)
```

## 9. Logging & Audit

### Structured Logging

```python
# core/config.py sets up logging
import logging
logger = logging.getLogger(__name__)

# Usage in code
logger.info("Booking created", extra={
    "booking_id": booking.id,
    "student_id": student.id,
    "tutor_id": tutor.id,
})
```

### Audit Trail

```python
# models/admin.py
class AuditLog(Base):
    id = Column(BigInteger, primary_key=True)
    table_name = Column(String(100))
    record_id = Column(Integer)
    action = Column(String(20))  # INSERT, UPDATE, DELETE, SOFT_DELETE, RESTORE
    old_data = Column(JSONB)
    new_data = Column(JSONB)
    changed_by = Column(Integer, ForeignKey("users.id"))
    changed_at = Column(TIMESTAMP(timezone=True))
    ip_address = Column(INET)
    user_agent = Column(Text)
```
