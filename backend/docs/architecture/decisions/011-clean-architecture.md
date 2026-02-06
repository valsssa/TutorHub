# ADR-011: Clean Architecture Implementation

## Status

Accepted

## Date

2026-02-02

## Context

The EduStream backend evolved organically with increasing coupling to external services and infrastructure concerns mixed into business logic. An audit identified several architectural issues:

- **Tight coupling to external services**: 295 direct model imports across layers
- **Business logic in API routes**: Validation, orchestration, and domain rules scattered in route handlers
- **Testing difficulties**: Unit tests required spinning up external dependencies (Stripe, Redis, MinIO, Brevo)
- **Inconsistent error handling**: Each integration handled errors differently
- **Vendor lock-in**: Switching providers (e.g., Stripe to another payment processor) would require touching many files

Key forces at play:
- **Maintainability**: Growing codebase needs clear boundaries
- **Testability**: Fast, reliable tests require isolation from external services
- **Team scaling**: New engineers need to understand where code belongs
- **Production reliability**: External service failures should be handled consistently
- **Evolution**: Business requirements change faster than infrastructure

## Decision

We will implement **Clean Architecture** using the Port/Adapter pattern with Protocol-based interfaces.

### Core Principles

1. **Dependency Inversion**: Business logic depends on abstractions (ports), not concrete implementations (adapters)
2. **Separation of Concerns**: Each layer has a single responsibility
3. **Testability First**: All external dependencies are injectable and replaceable with fakes

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer (API Routes)                            │
│  - FastAPI routers, request/response models                │
│  - Depends on Application layer                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Application Layer (Services/Use Cases)                     │
│  - Orchestrates domain logic and infrastructure            │
│  - Uses port interfaces for external operations            │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐    ┌─────────────────────────────────┐
│  Domain Layer         │    │  Infrastructure Layer           │
│  - Entities           │    │  - Port implementations         │
│  - Value Objects      │    │  - Database access              │
│  - Domain Events      │    │  - External service adapters    │
│  - Business Rules     │    │                                 │
└───────────────────────┘    └─────────────────────────────────┘
```

### Port Interfaces (core/ports/)

Ports define contracts using Python's `Protocol` (structural subtyping):

```python
class PaymentPort(Protocol):
    """Protocol for payment processing operations."""

    def create_payment_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        customer_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> PaymentResult:
        """Create a payment intent for authorization."""
        ...

    def capture_payment(
        self,
        payment_intent_id: str,
        *,
        amount_cents: int | None = None,
    ) -> PaymentResult:
        """Capture an authorized payment."""
        ...
```

**Defined Ports:**
- `PaymentPort`: Payment processing (create intent, capture, refund)
- `EmailPort`: Transactional email sending
- `StoragePort`: File upload/download operations
- `CachePort`: Caching and distributed locks
- `MeetingPort`: Video meeting creation (Zoom/custom)
- `CalendarPort`: Calendar integration (Google Calendar)

### Adapter Implementations (core/adapters/)

Adapters implement port protocols for specific technologies:

| Port | Adapter | Technology |
|------|---------|------------|
| PaymentPort | StripeAdapter | Stripe API |
| EmailPort | BrevoAdapter | Brevo (Sendinblue) |
| StoragePort | MinIOAdapter | MinIO / S3-compatible |
| CachePort | RedisAdapter | Redis |
| MeetingPort | ZoomAdapter | Zoom API |
| CalendarPort | GoogleCalendarAdapter | Google Calendar API |

Each adapter:
- Implements the port protocol exactly
- Handles provider-specific error mapping
- Provides consistent logging and metrics
- Returns domain-agnostic result types

### Fake Implementations (core/fakes/)

In-memory implementations for testing:

```python
class FakePayment:
    """In-memory payment implementation for testing."""

    def __init__(self) -> None:
        self._payments: dict[str, dict] = {}
        self._should_fail = False
        self._failure_reason: str | None = None

    def create_payment_intent(self, ...) -> PaymentResult:
        if self._should_fail:
            return PaymentResult(success=False, error=self._failure_reason)
        # Create in-memory payment record
        ...
```

**Fakes provide:**
- Fast test execution (no network calls)
- Deterministic behavior
- Failure injection for edge case testing
- State inspection for assertions

### Domain Layer (modules/*/domain/)

Each complex module has a domain layer containing:

1. **Entities**: Pure data classes representing domain concepts
   ```python
   @dataclass
   class BookingEntity:
       id: int | None
       student_id: int
       tutor_id: int
       session_state: SessionState
       # ... no infrastructure dependencies
   ```

2. **Value Objects**: Immutable domain values
   ```python
   @dataclass(frozen=True)
   class EmailResult:
       success: bool
       status: EmailStatus
       message_id: str | None
   ```

3. **Repository Protocols**: Data access contracts
   ```python
   class BookingRepository(Protocol):
       def get_by_id(self, booking_id: int) -> BookingEntity | None:
           ...
   ```

4. **Domain Services**: Business rules and state machines
   ```python
   class BookingStateMachine:
       @classmethod
       def accept_booking(cls, booking: BookingEntity) -> TransitionResult:
           """REQUESTED -> SCHEDULED"""
   ```

### Event System (core/events.py)

Centralized domain event dispatcher for loose coupling between modules:

```python
@dataclass
class BookingConfirmedEvent(DomainEvent):
    booking_id: int
    student_id: int
    tutor_id: int
    start_time: datetime

# Handler registration
@event_dispatcher.on("BookingConfirmedEvent")
async def send_confirmation_emails(event: BookingConfirmedEvent):
    # Send emails to student and tutor
    ...

# Publishing
await event_dispatcher.publish(BookingConfirmedEvent(
    booking_id=123,
    student_id=456,
    tutor_id=789,
    start_time=session_time,
))
```

### Dependency Injection

Services receive port implementations via constructor injection:

```python
class BookingService:
    def __init__(
        self,
        payment: PaymentPort,
        email: EmailPort,
        calendar: CalendarPort,
    ) -> None:
        self._payment = payment
        self._email = email
        self._calendar = calendar

    async def confirm_booking(self, booking_id: int) -> BookingResult:
        # Uses injected ports, never concrete implementations
        result = self._payment.capture_payment(...)
        ...
```

FastAPI dependencies wire implementations:

```python
def get_payment_port() -> PaymentPort:
    return StripeAdapter(api_key=settings.STRIPE_SECRET_KEY)

def get_booking_service(
    payment: PaymentPort = Depends(get_payment_port),
    email: EmailPort = Depends(get_email_port),
) -> BookingService:
    return BookingService(payment=payment, email=email)
```

## Consequences

### Positive

- **Testability**: Unit tests run in milliseconds using fakes, no external dependencies required
- **Loose coupling**: Business logic doesn't know about Stripe, Redis, or any specific technology
- **Clear boundaries**: Each layer has explicit responsibilities
- **Swappable implementations**: Can replace Stripe with another processor without touching business logic
- **Consistent error handling**: All adapters return standardized result types
- **Better debugging**: Clear call stack from presentation through domain to infrastructure
- **Parallel development**: Teams can work on different layers simultaneously
- **Self-documenting**: Protocol interfaces serve as living documentation

### Negative

- **More files**: Port + Adapter + Fake = 3 files per external dependency (vs. 1 before)
- **Initial learning curve**: Engineers must understand the layering
- **Indirection**: Following code requires understanding the interface layer
- **Boilerplate**: Protocol definitions and result types add code
- **Over-engineering risk**: Simple CRUD operations may not need full layering

### Neutral

- **Migration path**: Existing code can be migrated incrementally; old direct imports still work
- **Module flexibility**: Not all modules need full DDD structure; simple modules use simpler patterns
- **Testing strategy**: Can mix fake-based unit tests with integration tests using real adapters

## Implementation Details

### Directory Structure

```
backend/
├── core/
│   ├── ports/           # Port interfaces (protocols)
│   │   ├── __init__.py
│   │   ├── payment.py   # PaymentPort, PaymentResult
│   │   ├── email.py     # EmailPort, EmailResult
│   │   ├── storage.py   # StoragePort, StorageResult
│   │   ├── cache.py     # CachePort, LockResult
│   │   ├── meeting.py   # MeetingPort, MeetingResult
│   │   └── calendar.py  # CalendarPort, CalendarResult
│   ├── adapters/        # Concrete implementations
│   │   ├── __init__.py
│   │   ├── stripe_adapter.py
│   │   ├── brevo_adapter.py
│   │   ├── minio_adapter.py
│   │   ├── redis_adapter.py
│   │   ├── zoom_adapter.py
│   │   └── google_calendar_adapter.py
│   ├── fakes/           # Test doubles
│   │   ├── __init__.py
│   │   ├── fake_payment.py
│   │   ├── fake_email.py
│   │   ├── fake_storage.py
│   │   ├── fake_cache.py
│   │   ├── fake_meeting.py
│   │   └── fake_calendar.py
│   └── events.py        # Domain event dispatcher
├── modules/
│   └── bookings/
│       └── domain/      # Module-specific domain layer
│           ├── entities.py
│           ├── repositories.py
│           ├── status.py
│           └── state_machine.py
```

### Migration Strategy

1. **New code**: All new external integrations must use port/adapter pattern
2. **Existing code**: Migrate when touched for other reasons
3. **Testing**: Prioritize adding fakes for most-tested services first
4. **Gradual adoption**: Not all modules need full domain layer; apply where complexity warrants

## Alternatives Considered

### Option A: Continue with Direct Integration

Keep calling external services directly from business logic.

**Pros:**
- No refactoring needed
- Fewer files
- Direct and simple for small features

**Cons:**
- Testing requires mocking or real services
- Tight coupling makes changes risky
- Inconsistent error handling
- Growing technical debt

**Why not chosen:** Testing difficulties and coupling already causing problems.

### Option B: Abstract Base Classes (ABC)

Use Python's ABC instead of Protocol for interfaces.

**Pros:**
- Explicit inheritance relationship
- IDE support for implementation checking
- Familiar to many Python developers

**Cons:**
- Requires explicit inheritance (nominal typing)
- More rigid class hierarchy
- Can't use existing classes that happen to match interface

**Why not chosen:** Protocol's structural subtyping is more flexible and Pythonic.

### Option C: Full Hexagonal Architecture

Stricter separation with explicit "driving" and "driven" ports.

**Pros:**
- More rigorous separation
- Clearer architecture documentation
- Established pattern with extensive literature

**Cons:**
- More complexity than needed
- Additional conceptual overhead
- Over-engineered for current team size

**Why not chosen:** Port/adapter pattern provides sufficient benefits with less complexity.

### Option D: Framework-Based DI (e.g., dependency-injector)

Use a dedicated dependency injection framework.

**Pros:**
- Automatic wiring
- Container management
- Lifecycle management

**Cons:**
- Additional dependency
- Framework learning curve
- May conflict with FastAPI's DI
- Magic behavior harder to debug

**Why not chosen:** FastAPI's built-in Depends() is sufficient and more explicit.

## References

- Port interfaces: `backend/core/ports/`
- Adapter implementations: `backend/core/adapters/`
- Fake implementations: `backend/core/fakes/`
- Domain event system: `backend/core/events.py`
- Booking domain layer: `backend/modules/bookings/domain/`
- Related: ADR-001 (Modular Monolith Architecture)
- Related: ADR-002 (Four-Field Booking State Machine)
- External: [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- External: [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
