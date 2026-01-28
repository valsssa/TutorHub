# Booking Service - True DDD Implementation
## Complete Reference Implementation

This is how to properly implement ONE microservice with True DDD patterns.

---

## 📁 Directory Structure

```
booking-service/
├── domain/                      # Pure business logic (no dependencies)
│   ├── model/
│   │   ├── __init__.py
│   │   ├── booking.py          # Booking Aggregate Root
│   │   ├── value_objects.py    # Money, DateRange, etc.
│   │   └── enums.py            # BookingStatus, PaymentStatus
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── domain_event.py     # Base event class
│   │   ├── booking_requested.py
│   │   ├── booking_confirmed.py
│   │   ├── booking_cancelled.py
│   │   └── payment_processed.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── booking_conflict_checker.py
│   │   └── refund_calculator.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── booking_repository.py  # Interface (ABC)
│   │
│   └── exceptions.py
│
├── application/                 # Use cases
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── create_booking.py
│   │   ├── confirm_booking.py
│   │   ├── cancel_booking.py
│   │   └── complete_booking.py
│   │
│   ├── queries/
│   │   ├── __init__.py
│   │   ├── get_booking.py
│   │   └── list_bookings.py
│   │
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── command_handler.py
│   │   └── query_handler.py
│   │
│   └── event_handlers/
│       ├── __init__.py
│       └── payment_succeeded_handler.py
│
├── infrastructure/              # External dependencies
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── sqlalchemy_booking_repository.py
│   │   ├── models.py           # SQLAlchemy models
│   │   └── database.py
│   │
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── kafka_event_bus.py
│   │   └── event_mapper.py
│   │
│   └── clients/
│       ├── __init__.py
│       ├── identity_service_client.py
│       └── tutoring_service_client.py
│
├── presentation/                # API layer
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── schemas.py          # Pydantic DTOs
│   │   └── dependencies.py
│   │
│   └── grpc/
│       └── booking_grpc.py
│
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── logging_config.py
│   └── utils.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── main.py
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

---

## 1. Domain Layer (Pure Business Logic)

### domain/model/value_objects.py

```python
"""Value Objects - Immutable, no identity."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)  # Immutable
class Money:
    """Money value object."""
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in ["USD", "EUR", "GBP"]:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)

    def __str__(self):
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class DateTimeRange:
    """Time range value object."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("End time must be after start time")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

    def overlaps_with(self, other: 'DateTimeRange') -> bool:
        """Check if this range overlaps with another."""
        return self.start < other.end and other.start < self.end

    def __str__(self):
        return f"{self.start} - {self.end}"


@dataclass(frozen=True)
class BookingSnapshot:
    """Immutable snapshot of booking details at time of creation."""
    tutor_id: int
    tutor_name: str
    tutor_email: str
    student_id: int
    student_name: str
    student_email: str
    subject: str
    hourly_rate: Money
    created_at: datetime

    def __str__(self):
        return f"Booking: {self.student_name} with {self.tutor_name} for {self.subject}"
```

### domain/model/enums.py

```python
"""Domain enums."""
from enum import Enum


class BookingStatus(str, Enum):
    """Booking status enum."""
    PENDING = "pending"           # Created, awaiting confirmation
    CONFIRMED = "confirmed"       # Payment successful, confirmed
    IN_PROGRESS = "in_progress"   # Session started
    COMPLETED = "completed"       # Session finished
    CANCELLED = "cancelled"       # Cancelled by student/tutor
    REFUNDED = "refunded"         # Cancelled and refunded

    def can_transition_to(self, new_status: 'BookingStatus') -> bool:
        """Check if transition to new status is valid."""
        transitions = {
            self.PENDING: [self.CONFIRMED, self.CANCELLED],
            self.CONFIRMED: [self.IN_PROGRESS, self.CANCELLED, self.REFUNDED],
            self.IN_PROGRESS: [self.COMPLETED, self.CANCELLED],
            self.COMPLETED: [],  # Terminal state
            self.CANCELLED: [self.REFUNDED],
            self.REFUNDED: [],  # Terminal state
        }
        return new_status in transitions.get(self, [])


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
```

### domain/model/booking.py (Aggregate Root)

```python
"""Booking Aggregate Root."""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from domain.events.booking_requested import BookingRequested
from domain.events.booking_confirmed import BookingConfirmed
from domain.events.booking_cancelled import BookingCancelled
from domain.events.domain_event import DomainEvent
from domain.exceptions import InvalidBookingStateError
from domain.model.enums import BookingStatus, PaymentStatus
from domain.model.value_objects import Money, DateTimeRange, BookingSnapshot


class Booking:
    """Booking Aggregate Root.

    Responsible for:
    - Ensuring booking business rules
    - Coordinating between entities
    - Publishing domain events
    """

    def __init__(
        self,
        booking_id: Optional[int] = None,
        snapshot: Optional[BookingSnapshot] = None,
        scheduled_time: Optional[DateTimeRange] = None,
        amount: Optional[Money] = None,
        status: BookingStatus = BookingStatus.PENDING,
        payment_status: PaymentStatus = PaymentStatus.PENDING,
        meeting_url: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        self.id = booking_id
        self.snapshot = snapshot
        self.scheduled_time = scheduled_time
        self.amount = amount
        self.status = status
        self.payment_status = payment_status
        self.meeting_url = meeting_url
        self.notes = notes
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

        # Domain events that have occurred
        self._domain_events: List[DomainEvent] = []

    @staticmethod
    def request_booking(
        snapshot: BookingSnapshot,
        scheduled_time: DateTimeRange,
        amount: Money,
        notes: Optional[str] = None,
    ) -> 'Booking':
        """Factory method to create a new booking request."""

        # Business rule: Booking must be in the future
        if scheduled_time.start <= datetime.now(timezone.utc):
            raise InvalidBookingStateError("Cannot book a session in the past")

        # Business rule: Minimum session duration (30 minutes)
        if scheduled_time.duration.total_seconds() < 1800:
            raise InvalidBookingStateError("Session must be at least 30 minutes")

        # Business rule: Maximum session duration (4 hours)
        if scheduled_time.duration.total_seconds() > 14400:
            raise InvalidBookingStateError("Session cannot exceed 4 hours")

        booking = Booking(
            snapshot=snapshot,
            scheduled_time=scheduled_time,
            amount=amount,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            notes=notes,
        )

        # Publish domain event
        booking._add_domain_event(
            BookingRequested(
                booking_id=booking.id,  # Will be set after persistence
                student_id=snapshot.student_id,
                tutor_id=snapshot.tutor_id,
                scheduled_time=scheduled_time,
                amount=amount,
                occurred_at=datetime.now(timezone.utc)
            )
        )

        return booking

    def confirm(self, payment_id: str, meeting_url: str) -> None:
        """Confirm booking after successful payment."""

        # Business rule: Can only confirm pending bookings
        if self.status != BookingStatus.PENDING:
            raise InvalidBookingStateError(
                f"Cannot confirm booking with status: {self.status}"
            )

        # Business rule: Payment must be successful
        if self.payment_status != PaymentStatus.SUCCEEDED:
            raise InvalidBookingStateError(
                f"Cannot confirm booking without successful payment"
            )

        # Transition state
        self._transition_to(BookingStatus.CONFIRMED)
        self.meeting_url = meeting_url
        self.updated_at = datetime.now(timezone.utc)

        # Publish domain event
        self._add_domain_event(
            BookingConfirmed(
                booking_id=self.id,
                student_id=self.snapshot.student_id,
                tutor_id=self.snapshot.tutor_id,
                scheduled_time=self.scheduled_time,
                meeting_url=meeting_url,
                occurred_at=datetime.now(timezone.utc)
            )
        )

    def cancel(self, cancelled_by: int, reason: Optional[str] = None) -> None:
        """Cancel booking."""

        # Business rule: Cannot cancel completed bookings
        if self.status == BookingStatus.COMPLETED:
            raise InvalidBookingStateError("Cannot cancel completed booking")

        # Business rule: Cannot cancel already cancelled bookings
        if self.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
            raise InvalidBookingStateError("Booking already cancelled")

        old_status = self.status
        self._transition_to(BookingStatus.CANCELLED)
        self.updated_at = datetime.now(timezone.utc)

        # Publish domain event
        self._add_domain_event(
            BookingCancelled(
                booking_id=self.id,
                student_id=self.snapshot.student_id,
                tutor_id=self.snapshot.tutor_id,
                cancelled_by=cancelled_by,
                reason=reason,
                previous_status=old_status.value,
                refund_eligible=self._is_refund_eligible(),
                occurred_at=datetime.now(timezone.utc)
            )
        )

    def mark_payment_successful(self, payment_id: str) -> None:
        """Mark payment as successful."""
        self.payment_status = PaymentStatus.SUCCEEDED
        self.updated_at = datetime.now(timezone.utc)

    def mark_payment_failed(self, error: str) -> None:
        """Mark payment as failed and cancel booking."""
        self.payment_status = PaymentStatus.FAILED
        self._transition_to(BookingStatus.CANCELLED)
        self.updated_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        """Mark booking as completed."""

        # Business rule: Must be confirmed or in-progress
        if self.status not in [BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS]:
            raise InvalidBookingStateError(
                f"Cannot complete booking with status: {self.status}"
            )

        self._transition_to(BookingStatus.COMPLETED)
        self.updated_at = datetime.now(timezone.utc)

    def _is_refund_eligible(self) -> bool:
        """Check if booking is eligible for refund."""
        # Business rule: Refund if cancelled > 24 hours before session
        if not self.scheduled_time:
            return False

        time_until_session = (
            self.scheduled_time.start - datetime.now(timezone.utc)
        ).total_seconds()

        return time_until_session > 86400  # 24 hours

    def _transition_to(self, new_status: BookingStatus) -> None:
        """Transition to new status with validation."""
        if not self.status.can_transition_to(new_status):
            raise InvalidBookingStateError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status

    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event to be published."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def __repr__(self):
        return (
            f"<Booking(id={self.id}, "
            f"status={self.status.value}, "
            f"amount={self.amount})>"
        )
```

### domain/events/domain_event.py

```python
"""Base domain event."""
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: str
    occurred_at: datetime

    def __post_init__(self):
        if not hasattr(self, 'event_id') or not self.event_id:
            self.event_id = str(uuid4())
```

### domain/events/booking_confirmed.py

```python
"""Booking confirmed domain event."""
from dataclasses import dataclass
from datetime import datetime

from domain.events.domain_event import DomainEvent
from domain.model.value_objects import DateTimeRange


@dataclass
class BookingConfirmed(DomainEvent):
    """Emitted when booking is confirmed."""
    booking_id: int
    student_id: int
    tutor_id: int
    scheduled_time: DateTimeRange
    meeting_url: str
    occurred_at: datetime
    event_id: str = None  # Auto-generated in __post_init__

    @property
    def event_type(self) -> str:
        return "BookingConfirmed"
```

### domain/services/booking_conflict_checker.py (Domain Service)

```python
"""Domain service for checking booking conflicts."""
from typing import List
from datetime import datetime

from domain.model.booking import Booking
from domain.model.value_objects import DateTimeRange
from domain.repositories.booking_repository import BookingRepository


class BookingConflictChecker:
    """Domain service for checking scheduling conflicts.

    This is a DOMAIN SERVICE because:
    - The logic doesn't naturally belong to any single aggregate
    - It requires multiple aggregates (checking against existing bookings)
    - It's pure business logic with no infrastructure dependencies
    """

    def __init__(self, booking_repository: BookingRepository):
        self._repository = booking_repository

    async def has_conflict(
        self,
        tutor_id: int,
        time_range: DateTimeRange,
        exclude_booking_id: int = None
    ) -> bool:
        """Check if tutor has conflicting bookings."""

        # Get tutor's bookings in the time range
        existing_bookings = await self._repository.find_by_tutor_and_time_range(
            tutor_id=tutor_id,
            start_time=time_range.start,
            end_time=time_range.end,
            exclude_booking_id=exclude_booking_id
        )

        # Check for overlaps
        for booking in existing_bookings:
            if booking.scheduled_time.overlaps_with(time_range):
                return True

        return False

    async def get_conflicting_bookings(
        self,
        tutor_id: int,
        time_range: DateTimeRange
    ) -> List[Booking]:
        """Get list of conflicting bookings."""

        existing_bookings = await self._repository.find_by_tutor_and_time_range(
            tutor_id=tutor_id,
            start_time=time_range.start,
            end_time=time_range.end
        )

        return [
            booking for booking in existing_bookings
            if booking.scheduled_time.overlaps_with(time_range)
        ]
```

---

## 2. Application Layer (Use Cases)

### application/commands/create_booking.py

```python
"""Create booking command and handler."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.model.value_objects import Money, DateTimeRange, BookingSnapshot
from domain.model.booking import Booking
from domain.repositories.booking_repository import BookingRepository
from domain.services.booking_conflict_checker import BookingConflictChecker
from infrastructure.clients.identity_service_client import IdentityServiceClient
from infrastructure.clients.tutoring_service_client import TutoringServiceClient
from infrastructure.messaging.kafka_event_bus import EventBus


@dataclass
class CreateBookingCommand:
    """Command to create a new booking."""
    student_id: int
    tutor_id: int
    scheduled_start: datetime
    scheduled_end: datetime
    subject: str
    notes: Optional[str] = None


class CreateBookingCommandHandler:
    """Handler for CreateBookingCommand."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        conflict_checker: BookingConflictChecker,
        identity_client: IdentityServiceClient,
        tutoring_client: TutoringServiceClient,
        event_bus: EventBus,
    ):
        self._repository = booking_repository
        self._conflict_checker = conflict_checker
        self._identity_client = identity_client
        self._tutoring_client = tutoring_client
        self._event_bus = event_bus

    async def handle(self, command: CreateBookingCommand) -> int:
        """Handle create booking command."""

        # 1. Validate time range
        time_range = DateTimeRange(
            start=command.scheduled_start,
            end=command.scheduled_end
        )

        # 2. Check for conflicts
        has_conflict = await self._conflict_checker.has_conflict(
            tutor_id=command.tutor_id,
            time_range=time_range
        )
        if has_conflict:
            raise ValueError("Tutor is not available at this time")

        # 3. Get user details from Identity Service
        student = await self._identity_client.get_user(command.student_id)
        tutor = await self._identity_client.get_user(command.tutor_id)

        # 4. Get tutor pricing from Tutoring Service
        tutor_profile = await self._tutoring_client.get_tutor_profile(
            command.tutor_id
        )
        hourly_rate = tutor_profile.hourly_rate

        # 5. Calculate amount
        hours = time_range.duration.total_seconds() / 3600
        amount = hourly_rate.multiply(hours)

        # 6. Create booking snapshot (immutable)
        snapshot = BookingSnapshot(
            tutor_id=tutor.id,
            tutor_name=tutor.name,
            tutor_email=tutor.email,
            student_id=student.id,
            student_name=student.name,
            student_email=student.email,
            subject=command.subject,
            hourly_rate=hourly_rate,
            created_at=datetime.now()
        )

        # 7. Create booking aggregate
        booking = Booking.request_booking(
            snapshot=snapshot,
            scheduled_time=time_range,
            amount=amount,
            notes=command.notes
        )

        # 8. Save booking
        booking_id = await self._repository.save(booking)
        booking.id = booking_id

        # 9. Publish domain events
        events = booking.get_domain_events()
        for event in events:
            await self._event_bus.publish("booking.events", event)

        return booking_id
```

### application/event_handlers/payment_succeeded_handler.py

```python
"""Handler for PaymentSucceeded event from Payment Service."""
from dataclasses import dataclass
from datetime import datetime

from domain.repositories.booking_repository import BookingRepository
from infrastructure.messaging.kafka_event_bus import EventBus


@dataclass
class PaymentSucceeded:
    """Event from Payment Service."""
    event_id: str
    booking_id: int
    payment_id: str
    amount: float
    occurred_at: datetime


class PaymentSucceededHandler:
    """Handle PaymentSucceeded event."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        event_bus: EventBus,
    ):
        self._repository = booking_repository
        self._event_bus = event_bus

    async def handle(self, event: PaymentSucceeded) -> None:
        """Handle payment succeeded event."""

        # 1. Get booking
        booking = await self._repository.find_by_id(event.booking_id)
        if not booking:
            # Log error - booking not found
            return

        # 2. Mark payment successful
        booking.mark_payment_successful(event.payment_id)

        # 3. Generate meeting URL (Zoom integration)
        meeting_url = await self._generate_meeting_url(booking)

        # 4. Confirm booking
        booking.confirm(
            payment_id=event.payment_id,
            meeting_url=meeting_url
        )

        # 5. Save booking
        await self._repository.save(booking)

        # 6. Publish domain events (BookingConfirmed)
        events = booking.get_domain_events()
        for event in events:
            await self._event_bus.publish("booking.events", event)

    async def _generate_meeting_url(self, booking) -> str:
        """Generate Zoom meeting URL."""
        # Integration with Zoom API
        return f"https://zoom.us/j/{booking.id}"
```

---

## 3. Infrastructure Layer

### infrastructure/persistence/sqlalchemy_booking_repository.py

```python
"""SQLAlchemy implementation of BookingRepository."""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from domain.model.booking import Booking
from domain.model.enums import BookingStatus, PaymentStatus
from domain.model.value_objects import Money, DateTimeRange, BookingSnapshot
from domain.repositories.booking_repository import BookingRepository
from infrastructure.persistence.models import BookingModel


class SQLAlchemyBookingRepository(BookingRepository):
    """SQLAlchemy implementation of booking repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, booking: Booking) -> int:
        """Save booking to database."""

        if booking.id:
            # Update existing
            model = await self._session.get(BookingModel, booking.id)
            if not model:
                raise ValueError(f"Booking {booking.id} not found")
            self._update_model(model, booking)
        else:
            # Create new
            model = self._to_model(booking)
            self._session.add(model)

        await self._session.commit()
        await self._session.refresh(model)

        return model.id

    async def find_by_id(self, booking_id: int) -> Optional[Booking]:
        """Find booking by ID."""
        model = await self._session.get(BookingModel, booking_id)
        if not model:
            return None
        return self._to_domain(model)

    async def find_by_tutor_and_time_range(
        self,
        tutor_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_booking_id: int = None
    ) -> List[Booking]:
        """Find bookings for tutor in time range."""

        query = select(BookingModel).where(
            and_(
                BookingModel.tutor_id == tutor_id,
                BookingModel.scheduled_start < end_time,
                BookingModel.scheduled_end > start_time,
                BookingModel.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.IN_PROGRESS
                ])
            )
        )

        if exclude_booking_id:
            query = query.where(BookingModel.id != exclude_booking_id)

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: BookingModel) -> Booking:
        """Convert SQLAlchemy model to domain entity."""
        return Booking(
            booking_id=model.id,
            snapshot=BookingSnapshot(
                tutor_id=model.tutor_id,
                tutor_name=model.tutor_name,
                tutor_email=model.tutor_email,
                student_id=model.student_id,
                student_name=model.student_name,
                student_email=model.student_email,
                subject=model.subject,
                hourly_rate=Money(model.hourly_rate, model.currency),
                created_at=model.created_at
            ),
            scheduled_time=DateTimeRange(
                start=model.scheduled_start,
                end=model.scheduled_end
            ),
            amount=Money(model.amount, model.currency),
            status=BookingStatus(model.status),
            payment_status=PaymentStatus(model.payment_status),
            meeting_url=model.meeting_url,
            notes=model.notes,
        )

    def _to_model(self, booking: Booking) -> BookingModel:
        """Convert domain entity to SQLAlchemy model."""
        return BookingModel(
            tutor_id=booking.snapshot.tutor_id,
            tutor_name=booking.snapshot.tutor_name,
            tutor_email=booking.snapshot.tutor_email,
            student_id=booking.snapshot.student_id,
            student_name=booking.snapshot.student_name,
            student_email=booking.snapshot.student_email,
            subject=booking.snapshot.subject,
            hourly_rate=booking.snapshot.hourly_rate.amount,
            currency=booking.snapshot.hourly_rate.currency,
            scheduled_start=booking.scheduled_time.start,
            scheduled_end=booking.scheduled_time.end,
            amount=booking.amount.amount,
            status=booking.status.value,
            payment_status=booking.payment_status.value,
            meeting_url=booking.meeting_url,
            notes=booking.notes,
        )
```

---

## 4. API Layer

### presentation/api/schemas.py

```python
"""API Request/Response schemas (DTOs)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateBookingRequest(BaseModel):
    """Request to create booking."""
    tutor_id: int = Field(..., gt=0)
    scheduled_start: datetime
    scheduled_end: datetime
    subject: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class BookingResponse(BaseModel):
    """Booking response."""
    id: int
    student_id: int
    student_name: str
    tutor_id: int
    tutor_name: str
    subject: str
    scheduled_start: datetime
    scheduled_end: datetime
    amount: float
    currency: str
    status: str
    payment_status: str
    meeting_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### presentation/api/routes.py

```python
"""API routes for booking service."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from presentation.api.schemas import CreateBookingRequest, BookingResponse
from presentation.api.dependencies import get_command_handler, get_current_user
from application.commands.create_booking import CreateBookingCommand


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    request: CreateBookingRequest,
    current_user = Depends(get_current_user),
    handler = Depends(get_command_handler)
):
    """Create a new booking."""

    # Only students can create bookings
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create bookings"
        )

    # Create command
    command = CreateBookingCommand(
        student_id=current_user.id,
        tutor_id=request.tutor_id,
        scheduled_start=request.scheduled_start,
        scheduled_end=request.scheduled_end,
        subject=request.subject,
        notes=request.notes
    )

    # Execute command
    try:
        booking_id = await handler.handle(command)
        # Fetch and return booking
        # ...
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

---

## 5. Docker & Kubernetes Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root
RUN useradd -m -u 1000 bookinguser
USER bookinguser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8003/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### k8s/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: booking-service
  namespace: edustream-services
spec:
  replicas: 3
  selector:
    matchLabels:
      app: booking-service
  template:
    metadata:
      labels:
        app: booking-service
        version: v1
    spec:
      containers:
      - name: booking-service
        image: edustream/booking-service:latest
        ports:
        - containerPort: 8003
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: booking-db-secret
              key: connection-string
        - name: KAFKA_BROKERS
          value: "kafka-0.kafka-headless.edustream-infra:9092"
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8003
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: booking-service
  namespace: edustream-services
spec:
  selector:
    app: booking-service
  ports:
  - port: 8003
    targetPort: 8003
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: booking-service-hpa
  namespace: edustream-services
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: booking-service
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

**This is TRUE DDD with Microservices**. Notice:

✅ **Pure domain layer** - No dependencies on infrastructure
✅ **Aggregates** - Booking is aggregate root with business rules
✅ **Value Objects** - Money, DateTimeRange are immutable
✅ **Domain Events** - Published when state changes
✅ **Domain Services** - BookingConflictChecker
✅ **Repository Interface** - In domain, implementation in infrastructure
✅ **Command/Query Separation** - CQRS pattern
✅ **Event-driven** - Services communicate via events
✅ **Saga Pattern** - PaymentSucceeded triggers booking confirmation
✅ **Independent deployment** - Kubernetes with auto-scaling

Want me to show you the other services or explain any pattern in detail?
