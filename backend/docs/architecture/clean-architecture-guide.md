# Clean Architecture Guide

This guide documents the clean architecture patterns used in the EduStream backend codebase. It provides practical guidance for understanding and extending the system while maintaining separation of concerns.

## Table of Contents

1. [Overview](#overview)
2. [Layer Structure](#layer-structure)
3. [Port/Adapter Pattern](#portadapter-pattern)
4. [Repository Pattern](#repository-pattern)
5. [Domain Events](#domain-events)
6. [Testing with Fakes](#testing-with-fakes)
7. [Adding a New Module](#adding-a-new-module)

---

## Overview

### What is Clean Architecture?

Clean Architecture is a software design philosophy that separates concerns into distinct layers, with dependencies pointing inward toward the domain. The core principle is that business logic (domain) should be independent of external concerns like databases, UI frameworks, and third-party services.

```
+----------------------------------------------------------+
|                    Presentation Layer                     |
|                   (API Routes, DTOs)                      |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
|                   Application Layer                       |
|              (Services, Use Cases, DTOs)                  |
+----------------------------------------------------------+
                            |
                            v
+----------------------------------------------------------+
|                     Domain Layer                          |
|     (Entities, Value Objects, Repository Interfaces)      |
+----------------------------------------------------------+
                            ^
                            |
+----------------------------------------------------------+
|                  Infrastructure Layer                     |
|         (Repository Implementations, Adapters)            |
+----------------------------------------------------------+
```

### Why We Adopted It

1. **Testability**: Business logic can be tested without databases or external services
2. **Maintainability**: Changes to infrastructure don't ripple through business logic
3. **Flexibility**: Easy to swap implementations (e.g., different payment providers)
4. **Team Scalability**: Clear boundaries enable parallel development
5. **Onboarding**: New developers understand where code belongs

### Benefits for the Team

- **Consistent Structure**: Every module follows the same patterns
- **Easy Testing**: Fakes allow fast, isolated unit tests
- **Clear Dependencies**: Ports define explicit contracts
- **Incremental Migration**: Can adopt DDD patterns gradually per module
- **Code Reviews**: Reviewers know what to look for in each layer

---

## Layer Structure

The EduStream backend uses three patterns based on module complexity:

| Pattern | When to Use | Examples |
|---------|-------------|----------|
| **Full DDD** | Complex business logic, state machines | `bookings/`, `auth/` |
| **Service + Presentation** | Moderate logic with reusable services | `packages/`, `notifications/` |
| **Presentation Only** | Simple CRUD operations | `reviews/`, `favorites/` |

### Domain Layer

The innermost layer containing business logic with no external dependencies.

**Location**: `modules/{module}/domain/`

**Components**:

#### Entities

Domain entities represent core business objects with identity and behavior.

```python
# modules/bookings/domain/entities.py

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.bookings.domain.status import (
    SessionState, SessionOutcome, PaymentState, DisputeState
)


@dataclass
class BookingEntity:
    """
    Core booking domain entity.

    Represents a tutoring session booking with its four-field status system.
    """
    id: int | None
    student_id: int
    tutor_id: int
    tutor_profile_id: int

    # Session timing
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"

    # Status fields (4-field system)
    session_state: SessionState = SessionState.PENDING_TUTOR
    session_outcome: SessionOutcome = SessionOutcome.PENDING
    payment_state: PaymentState = PaymentState.PENDING
    dispute_state: DisputeState = DisputeState.NONE

    # Pricing
    amount_cents: int = 0
    currency: str = "USD"

    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def is_confirmed(self) -> bool:
        """Check if booking is confirmed."""
        return self.session_state == SessionState.CONFIRMED
```

#### Value Objects

Immutable objects representing concepts without identity.

```python
# modules/payments/domain/value_objects.py

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    """
    Immutable value object representing a monetary amount.

    Amounts are stored in cents to avoid floating-point precision issues.
    """
    amount_cents: int
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate money fields."""
        if not isinstance(self.amount_cents, int):
            object.__setattr__(self, "amount_cents", int(self.amount_cents))
        if len(self.currency) != 3:
            raise ValueError(f"Currency must be 3-character ISO code: {self.currency}")
        object.__setattr__(self, "currency", self.currency.upper())

    @property
    def amount_decimal(self) -> float:
        """Get amount as decimal (for display purposes)."""
        return self.amount_cents / 100

    def __add__(self, other: "Money") -> "Money":
        """Add two Money objects."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(
            amount_cents=self.amount_cents + other.amount_cents,
            currency=self.currency,
        )

    @classmethod
    def zero(cls, currency: str = "USD") -> "Money":
        """Create a zero amount."""
        return cls(amount_cents=0, currency=currency)
```

#### Repository Interfaces

Protocol-based interfaces defining data access contracts.

```python
# modules/bookings/domain/repositories.py

from datetime import datetime
from typing import Protocol

from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.status import SessionState


class BookingRepository(Protocol):
    """
    Protocol for booking repository operations.

    Implementations should handle:
    - Booking CRUD operations
    - Status-based queries
    - Optimistic locking
    """

    def get_by_id(self, booking_id: int) -> BookingEntity | None:
        """Get a booking by its ID."""
        ...

    def create(self, booking: BookingEntity) -> BookingEntity:
        """Create a new booking."""
        ...

    def update(self, booking: BookingEntity) -> BookingEntity:
        """Update an existing booking with optimistic locking."""
        ...
```

#### Domain Exceptions

Business rule violations specific to the domain.

```python
# modules/auth/domain/exceptions.py

class AuthError(Exception):
    """Base exception for authentication domain errors."""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)


class AccountLockedError(AuthError):
    """Raised when account is locked due to too many failed attempts."""
    def __init__(
        self,
        user_id: int,
        locked_until: str | None = None,
        reason: str = "Too many failed login attempts",
    ):
        self.user_id = user_id
        self.locked_until = locked_until
        self.reason = reason
        message = f"Account locked: {reason}"
        if locked_until:
            message += f" until {locked_until}"
        super().__init__(message)
```

### Application Layer

Orchestrates domain logic and external services.

**Location**: `modules/{module}/application/` or `modules/{module}/services/`

```python
# modules/auth/application/services.py

from sqlalchemy.orm import Session
from modules.auth.domain.entities import UserEntity
from modules.auth.infrastructure.repository import UserRepository


class AuthService:
    """Service for authentication business logic."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        self.repository = UserRepository(db)
        self.db = db

    def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "student",
    ) -> UserEntity:
        """
        Register a new user.

        Orchestrates validation, hashing, and persistence.
        """
        # Validate inputs
        email = sanitize_email(email)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Check for duplicates
        if self.repository.exists_by_email(email):
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create domain entity
        user_entity = UserEntity(
            id=None,
            email=email,
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            is_verified=False,
        )

        # Persist and return
        return self.repository.create(user_entity)
```

### Infrastructure Layer

Implements interfaces defined in the domain layer.

**Location**: `modules/{module}/infrastructure/` or `core/adapters/`

```python
# modules/auth/infrastructure/repository.py

from sqlalchemy.orm import Session
from models import User
from modules.auth.domain.entities import UserEntity


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, user: User) -> UserEntity:
        """Convert database model to domain entity."""
        return UserEntity(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

    def find_by_email(self, email: str) -> UserEntity | None:
        """Find user by email, excluding soft-deleted users."""
        user = self.db.query(User).filter(
            User.email == email.lower(),
            User.deleted_at.is_(None),
        ).first()
        return self._to_entity(user) if user else None

    def create(self, entity: UserEntity) -> UserEntity:
        """Create new user."""
        user = User(
            email=entity.email.lower(),
            hashed_password=entity.hashed_password,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_entity(user)
```

### Presentation Layer

API routes and request/response handling.

**Location**: `modules/{module}/api.py` or `modules/{module}/presentation/`

```python
# modules/auth/presentation/routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from modules.auth.application.services import AuthService
from modules.auth.presentation.schemas import RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    service = AuthService(db)
    user = service.register_user(
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
    )
    return UserResponse.from_entity(user)
```

---

## Port/Adapter Pattern

Ports are interfaces (protocols) that define how the application core interacts with external systems. Adapters are concrete implementations of these ports.

### Explanation of Ports (Interfaces)

Ports define contracts without specifying implementation details. They use Python's `Protocol` for structural typing.

```python
# core/ports/payment.py

from typing import Protocol, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentResult:
    """Result of a payment operation."""
    success: bool
    payment_id: str | None = None
    error_message: str | None = None


class PaymentPort(Protocol):
    """
    Protocol for payment processing operations.

    Implementations should handle:
    - Idempotency to prevent double charges
    - Error categorization (transient vs permanent)
    - Retry logic for transient failures
    """

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSessionResult:
        """Create a checkout session for payment."""
        ...

    def create_refund(
        self,
        *,
        payment_intent_id: str,
        amount_cents: int | None = None,
    ) -> RefundResult:
        """Process a refund for a payment."""
        ...
```

### Explanation of Adapters (Implementations)

Adapters implement ports for specific technologies.

```python
# core/adapters/stripe_adapter.py

import stripe
from core.ports.payment import PaymentPort, CheckoutSessionResult


class StripeAdapter:
    """
    Stripe implementation of PaymentPort.

    Features:
    - Circuit breaker pattern for resilience
    - Idempotency keys for double-payment prevention
    """

    def create_checkout_session(
        self,
        *,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
    ) -> CheckoutSessionResult:
        """Create a Stripe Checkout session."""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "unit_amount": amount_cents,
                        "product_data": {"name": description},
                    },
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return CheckoutSessionResult(
                success=True,
                session_id=session.id,
                checkout_url=session.url,
            )
        except stripe.error.StripeError as e:
            return CheckoutSessionResult(
                success=False,
                error_message=str(e),
            )
```

### Available Ports

The codebase provides six ports for external service integration:

| Port | Interface | Adapter | Purpose |
|------|-----------|---------|---------|
| `PaymentPort` | `core/ports/payment.py` | `StripeAdapter` | Payment processing |
| `EmailPort` | `core/ports/email.py` | `BrevoAdapter` | Transactional email |
| `StoragePort` | `core/ports/storage.py` | `MinIOAdapter` | File storage (S3-compatible) |
| `CachePort` | `core/ports/cache.py` | `RedisAdapter` | Caching and distributed locks |
| `MeetingPort` | `core/ports/meeting.py` | `ZoomAdapter` | Video meeting creation |
| `CalendarPort` | `core/ports/calendar.py` | `GoogleCalendarAdapter` | Calendar integration |

### How to Create New Ports

1. **Define the port interface** in `core/ports/`:

```python
# core/ports/sms.py

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SMSResult:
    """Result of an SMS operation."""
    success: bool
    message_id: str | None = None
    error_message: str | None = None


class SMSPort(Protocol):
    """Protocol for SMS operations."""

    def send_sms(
        self,
        *,
        to_phone: str,
        message: str,
    ) -> SMSResult:
        """Send an SMS message."""
        ...
```

2. **Create the adapter** in `core/adapters/`:

```python
# core/adapters/twilio_adapter.py

from twilio.rest import Client
from core.ports.sms import SMSPort, SMSResult


class TwilioAdapter:
    """Twilio implementation of SMSPort."""

    def __init__(self):
        self.client = Client()

    def send_sms(
        self,
        *,
        to_phone: str,
        message: str,
    ) -> SMSResult:
        try:
            msg = self.client.messages.create(
                to=to_phone,
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
            )
            return SMSResult(success=True, message_id=msg.sid)
        except Exception as e:
            return SMSResult(success=False, error_message=str(e))
```

3. **Create a fake** in `core/fakes/`:

```python
# core/fakes/fake_sms.py

from dataclasses import dataclass, field
from core.ports.sms import SMSResult


@dataclass
class FakeSMS:
    """In-memory fake implementation for testing."""

    sent_messages: list[dict] = field(default_factory=list)
    should_fail: bool = False

    def send_sms(self, *, to_phone: str, message: str) -> SMSResult:
        if self.should_fail:
            return SMSResult(success=False, error_message="Simulated failure")

        self.sent_messages.append({"to": to_phone, "message": message})
        return SMSResult(success=True, message_id="fake_msg_123")
```

4. **Add factory function** in `core/dependencies.py`:

```python
def get_sms_port():
    """Get the SMS port implementation."""
    if _use_fakes:
        from core.fakes import FakeSMS
        return FakeSMS()
    from core.adapters import TwilioAdapter
    return TwilioAdapter()
```

5. **Export from __init__.py** files in ports, adapters, and fakes.

---

## Repository Pattern

Repositories abstract data access, allowing domain logic to remain independent of database specifics.

### Protocol-Based Interfaces

Repository interfaces are defined as Protocols in the domain layer:

```python
# modules/bookings/domain/repositories.py

from typing import Protocol
from datetime import datetime

from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.status import SessionState


class BookingRepository(Protocol):
    """Protocol for booking repository operations."""

    def get_by_id(self, booking_id: int) -> BookingEntity | None:
        """Get a booking by its ID."""
        ...

    def get_by_student(
        self,
        student_id: int,
        *,
        states: list[SessionState] | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[BookingEntity]:
        """Get bookings for a student with optional filtering."""
        ...

    def create(self, booking: BookingEntity) -> BookingEntity:
        """Create a new booking."""
        ...

    def update(self, booking: BookingEntity) -> BookingEntity:
        """Update with optimistic locking."""
        ...

    def check_time_conflict(
        self,
        tutor_id: int,
        start_time: datetime,
        end_time: datetime,
        *,
        exclude_booking_id: int | None = None,
    ) -> bool:
        """Check if a time slot conflicts with existing bookings."""
        ...
```

### How to Define a Repository

1. **Identify the operations** your domain needs
2. **Define methods** with clear parameters and return types
3. **Document** expected behavior including error cases
4. **Keep it domain-focused** - no SQLAlchemy or ORM specifics

### How to Implement a Repository

```python
# modules/auth/infrastructure/repository.py

from sqlalchemy.orm import Session
from models import User
from modules.auth.domain.entities import UserEntity


class UserRepository:
    """SQLAlchemy implementation of user repository."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, user: User) -> UserEntity:
        """Convert ORM model to domain entity."""
        return UserEntity(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
        )

    def _to_model(self, entity: UserEntity) -> User:
        """Convert domain entity to ORM model."""
        return User(
            id=entity.id,
            email=entity.email.lower(),
            hashed_password=entity.hashed_password,
            first_name=entity.first_name,
            last_name=entity.last_name,
            role=entity.role,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
        )

    def find_by_id(self, user_id: int) -> UserEntity | None:
        """Find user by ID, excluding soft-deleted."""
        user = self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()
        return self._to_entity(user) if user else None

    def find_by_email(self, email: str) -> UserEntity | None:
        """Find user by email (case-insensitive)."""
        from sqlalchemy import func

        user = self.db.query(User).filter(
            func.lower(User.email) == email.lower(),
            User.deleted_at.is_(None),
        ).first()
        return self._to_entity(user) if user else None

    def exists_by_email(self, email: str) -> bool:
        """Check if email is already registered."""
        return self.find_by_email(email) is not None

    def create(self, entity: UserEntity) -> UserEntity:
        """Create new user."""
        user = self._to_model(entity)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_entity(user)

    def update(self, entity: UserEntity) -> UserEntity:
        """Update existing user."""
        user = self.db.query(User).filter(User.id == entity.id).first()
        if not user:
            raise ValueError(f"User with id {entity.id} not found")

        user.email = entity.email.lower()
        user.first_name = entity.first_name
        user.last_name = entity.last_name
        user.role = entity.role
        user.is_active = entity.is_active
        user.is_verified = entity.is_verified

        self.db.commit()
        self.db.refresh(user)
        return self._to_entity(user)
```

---

## Domain Events

Domain events enable loose coupling between modules through event-driven communication.

### Using the EventDispatcher

The `EventDispatcher` is a singleton that manages event publication and subscription.

```python
from core.events import event_dispatcher, DomainEvent
```

### Defining Events

Events are immutable dataclasses inheriting from `DomainEvent`:

```python
# core/events.py (or in your module's domain/events.py)

from dataclasses import dataclass, field
from datetime import datetime, UTC
import uuid

from core.events import DomainEvent


@dataclass
class BookingCreatedEvent(DomainEvent):
    """Event fired when a new booking is created."""

    booking_id: int = 0
    student_id: int = 0
    tutor_id: int = 0
    subject_id: int | None = None
    start_time: datetime | None = None
    amount_cents: int = 0


@dataclass
class BookingConfirmedEvent(DomainEvent):
    """Event fired when a booking is confirmed."""

    booking_id: int = 0
    student_id: int = 0
    tutor_id: int = 0
    start_time: datetime | None = None


@dataclass
class SessionCompletedEvent(DomainEvent):
    """Event fired when a session completes successfully."""

    booking_id: int = 0
    student_id: int = 0
    tutor_id: int = 0
    duration_minutes: int = 0
```

### Registering Handlers

Use the decorator syntax for clean handler registration:

```python
# modules/notifications/handlers.py

from core.events import event_dispatcher, BookingConfirmedEvent


@event_dispatcher.on("BookingConfirmedEvent")
async def send_confirmation_notifications(event: BookingConfirmedEvent):
    """Send confirmation emails when booking is confirmed."""
    # Send email to student
    await email_service.send_booking_confirmed(
        booking_id=event.booking_id,
        user_id=event.student_id,
    )
    # Send email to tutor
    await email_service.send_booking_confirmed(
        booking_id=event.booking_id,
        user_id=event.tutor_id,
    )


@event_dispatcher.on("SessionCompletedEvent")
async def request_review(event: SessionCompletedEvent):
    """Request review after session completion."""
    await email_service.send_review_request(
        booking_id=event.booking_id,
        student_id=event.student_id,
    )
```

Or register programmatically with priority:

```python
def handle_booking_created(event: BookingCreatedEvent):
    """High-priority handler for new bookings."""
    # Create calendar event, etc.
    pass

# Higher priority handlers run first
event_dispatcher.register("BookingCreatedEvent", handle_booking_created, priority=10)
```

### Example Code

Publishing events from a service:

```python
# modules/bookings/application/services.py

from core.events import event_dispatcher, BookingCreatedEvent


class BookingService:
    async def create_booking(self, request: CreateBookingRequest) -> BookingEntity:
        # Create the booking
        booking = self.repository.create(booking_entity)

        # Publish domain event
        await event_dispatcher.publish(BookingCreatedEvent(
            booking_id=booking.id,
            student_id=booking.student_id,
            tutor_id=booking.tutor_id,
            subject_id=booking.subject_id,
            start_time=booking.start_time,
            amount_cents=booking.amount_cents,
        ))

        return booking
```

Disabling events in tests:

```python
def test_booking_creation():
    # Disable events to avoid side effects
    event_dispatcher.disable()
    try:
        # Test logic
        pass
    finally:
        event_dispatcher.enable()
```

---

## Testing with Fakes

Fakes are in-memory implementations of ports that enable fast, isolated testing without external services.

### Available Fakes

| Fake | Location | Purpose |
|------|----------|---------|
| `FakePayment` | `core/fakes/fake_payment.py` | Payment processing |
| `FakeEmail` | `core/fakes/fake_email.py` | Email sending |
| `FakeStorage` | `core/fakes/fake_storage.py` | File storage |
| `FakeCache` | `core/fakes/fake_cache.py` | Caching and locks |
| `FakeMeeting` | `core/fakes/fake_meeting.py` | Video meetings |
| `FakeCalendar` | `core/fakes/fake_calendar.py` | Calendar operations |

### How to Use Fakes in Tests

Import and configure fakes:

```python
# tests/test_booking_service.py

import pytest
from core.dependencies import set_use_fakes
from core.fakes import FakePayment, FakeEmail


@pytest.fixture(autouse=True)
def use_fakes():
    """Enable fakes for all tests in this module."""
    set_use_fakes(True)
    yield
    set_use_fakes(False)


def test_booking_creation_sends_confirmation_email():
    # Arrange
    fake_email = FakeEmail()

    # Act
    booking_service.create_booking(request, email_port=fake_email)

    # Assert
    assert len(fake_email.sent_emails) == 2
    assert fake_email.sent_emails[0].template_type == "booking_request"


def test_payment_failure_handling():
    # Arrange
    fake_payment = FakePayment()
    fake_payment.should_fail = True
    fake_payment.failure_message = "Card declined"

    # Act & Assert
    with pytest.raises(PaymentError) as exc_info:
        payment_service.process_payment(request, payment_port=fake_payment)

    assert "Card declined" in str(exc_info.value)
```

### Dependency Injection with `set_use_fakes(True)`

The `set_use_fakes()` function configures the dependency injection system:

```python
# core/dependencies.py

_use_fakes = False


def set_use_fakes(use_fakes: bool) -> None:
    """Configure whether to use fake implementations (for testing)."""
    global _use_fakes
    _use_fakes = use_fakes


def get_payment_port():
    """Get the payment port implementation."""
    if _use_fakes:
        from core.fakes import FakePayment
        return FakePayment()
    from core.adapters import StripeAdapter
    return StripeAdapter()


def get_email_port():
    """Get the email port implementation."""
    if _use_fakes:
        from core.fakes import FakeEmail
        return FakeEmail()
    from core.adapters import BrevoAdapter
    return BrevoAdapter()
```

Usage in conftest.py:

```python
# tests/conftest.py

import pytest
from core.dependencies import set_use_fakes


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment():
    """Configure test environment with fakes."""
    set_use_fakes(True)
    yield
    set_use_fakes(False)
```

### Fake Test Helpers

Fakes provide helper methods for test assertions:

```python
# FakeEmail helpers
fake_email = FakeEmail()

# Get emails sent to a specific address
emails = fake_email.get_emails_to("student@example.com")

# Get emails by template type
reminders = fake_email.get_emails_by_type("booking_reminder")

# Get the most recent email
last_email = fake_email.get_last_email()

# Clear all sent emails
fake_email.clear()

# Reset all state including failure configuration
fake_email.reset()


# FakePayment helpers
fake_payment = FakePayment()

# Mark a session as paid
fake_payment.mark_session_paid(session_id)

# Enable a Connect account
fake_payment.enable_connect_account(account_id)

# Get calls to a specific method
checkout_calls = fake_payment.get_calls("create_checkout_session")
```

---

## Adding a New Module

Follow this step-by-step guide when creating a new module.

### Step-by-Step Guide

#### 1. Determine the Pattern

Choose based on complexity:

- **Presentation Only**: Simple CRUD, minimal business logic
- **Service + Presentation**: Reusable logic, no complex state
- **Full DDD**: Complex business rules, state machines

#### 2. Create Directory Structure

For Full DDD:

```
modules/my_feature/
    __init__.py
    domain/
        __init__.py
        entities.py
        value_objects.py
        repositories.py
        exceptions.py
    application/
        __init__.py
        services.py
        dto.py
    infrastructure/
        __init__.py
        repositories.py
    presentation/
        __init__.py
        routes.py
        schemas.py
```

For Service + Presentation:

```
modules/my_feature/
    __init__.py
    services/
        __init__.py
        my_service.py
    api.py
    schemas.py
```

For Presentation Only:

```
modules/my_feature/
    __init__.py
    api.py
    schemas.py
```

#### 3. Create Domain Layer (if applicable)

```python
# modules/my_feature/domain/entities.py

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MyEntity:
    """Core domain entity for my feature."""
    id: int | None
    name: str
    status: str
    created_at: datetime | None = None
```

```python
# modules/my_feature/domain/repositories.py

from typing import Protocol
from modules.my_feature.domain.entities import MyEntity


class MyRepository(Protocol):
    """Repository interface for my feature."""

    def get_by_id(self, entity_id: int) -> MyEntity | None:
        ...

    def create(self, entity: MyEntity) -> MyEntity:
        ...
```

#### 4. Create Infrastructure Layer

```python
# modules/my_feature/infrastructure/repositories.py

from sqlalchemy.orm import Session
from models import MyModel
from modules.my_feature.domain.entities import MyEntity


class SqlAlchemyMyRepository:
    """SQLAlchemy implementation of MyRepository."""

    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: MyModel) -> MyEntity:
        return MyEntity(
            id=model.id,
            name=model.name,
            status=model.status,
            created_at=model.created_at,
        )

    def get_by_id(self, entity_id: int) -> MyEntity | None:
        model = self.db.query(MyModel).filter(MyModel.id == entity_id).first()
        return self._to_entity(model) if model else None
```

#### 5. Create Application Layer

```python
# modules/my_feature/application/services.py

from sqlalchemy.orm import Session
from modules.my_feature.infrastructure.repositories import SqlAlchemyMyRepository


class MyFeatureService:
    """Service for my feature business logic."""

    def __init__(self, db: Session):
        self.repository = SqlAlchemyMyRepository(db)

    def get_by_id(self, entity_id: int) -> MyEntity | None:
        return self.repository.get_by_id(entity_id)
```

#### 6. Create Presentation Layer

```python
# modules/my_feature/presentation/routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from modules.my_feature.application.services import MyFeatureService

router = APIRouter(prefix="/my-feature", tags=["my-feature"])


@router.get("/{entity_id}")
async def get_entity(entity_id: int, db: Session = Depends(get_db)):
    """Get an entity by ID."""
    service = MyFeatureService(db)
    entity = service.get_by_id(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Not found")
    return entity
```

#### 7. Register Router in main.py

```python
# main.py

from modules.my_feature.presentation.routes import router as my_feature_router

API_V1_PREFIX = "/api/v1"
app.include_router(my_feature_router, prefix=API_V1_PREFIX)
```

#### 8. Add Tests

```python
# tests/test_my_feature.py

import pytest
from core.dependencies import set_use_fakes


@pytest.fixture(autouse=True)
def use_fakes():
    set_use_fakes(True)
    yield
    set_use_fakes(False)


def test_get_entity_by_id(client, db_session):
    # Arrange
    # Create test data

    # Act
    response = client.get("/api/v1/my-feature/1")

    # Assert
    assert response.status_code == 200
```

### File Templates

#### `__init__.py` Template

```python
"""
My Feature Module

Provides [brief description of what this module does].
"""

from modules.my_feature.presentation.routes import router

__all__ = ["router"]
```

#### Entity Template

```python
"""Domain entities for my_feature module."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MyEntity:
    """
    Core domain entity.

    Represents [what this entity represents].
    """
    id: int | None
    # Add fields here

    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### Checklist

- [ ] Determined appropriate pattern (Presentation Only / Service / Full DDD)
- [ ] Created directory structure with all required files
- [ ] Added `__init__.py` with proper exports to all directories
- [ ] Created domain entities (if using DDD)
- [ ] Created repository interfaces (if using DDD)
- [ ] Created repository implementations
- [ ] Created service layer
- [ ] Created API routes
- [ ] Created request/response schemas (Pydantic models)
- [ ] Registered router in `main.py` with API v1 prefix
- [ ] Added unit tests for services
- [ ] Added integration tests for API endpoints
- [ ] Updated `docs/api_inventory.md` with new endpoints
- [ ] Added docstrings to all public classes and functions

---

## Related Documentation

- [Backend Architecture](../../../docs/architecture/04-backend-architecture.md) - High-level backend design
- [Domain Model](../../../docs/architecture/03-domain-model.md) - DDD patterns and bounded contexts
- [ADR-001: Modular Monolith](../../../docs/architecture/decisions/001-modular-monolith.md) - Why we chose this architecture
- [ADR-010: Booking State Machine](../../../docs/architecture/decisions/010-booking-state-machine-design.md) - State machine design
