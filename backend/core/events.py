"""
Domain Event System

Provides a centralized event dispatcher for publishing and handling domain events.
This enables loose coupling between modules through event-driven communication.

Usage:
    from core.events import DomainEvent, event_dispatcher

    # Define an event
    @dataclass
    class UserCreatedEvent(DomainEvent):
        user_id: int
        email: str
        role: str

    # Register a handler
    @event_dispatcher.on("UserCreatedEvent")
    async def handle_user_created(event: UserCreatedEvent):
        # Send welcome email, create related records, etc.
        pass

    # Publish an event
    await event_dispatcher.publish(UserCreatedEvent(
        user_id=123,
        email="user@example.com",
        role="student",
    ))
"""

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime

from core.datetime_utils import utc_now
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """
    Base class for domain events.

    All domain events should inherit from this class and define
    their specific data fields.
    """

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: utc_now())
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Get the event type name (class name)."""
        return self.__class__.__name__


EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventDispatcher:
    """
    Central event dispatcher for domain events.

    Supports:
    - Multiple handlers per event type
    - Async handlers
    - Handler priority
    - Fire-and-forget or wait-for-all modes
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[int, EventHandler]]] = defaultdict(list)
        self._enabled = True

    def register(
        self,
        event_type: str,
        handler: EventHandler,
        priority: int = 0,
    ) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: Name of the event type (class name)
            handler: Async function to handle the event
            priority: Higher priority handlers run first (default: 0)
        """
        self._handlers[event_type].append((priority, handler))
        # Sort by priority (descending)
        self._handlers[event_type].sort(key=lambda x: -x[0])
        logger.debug("Registered handler for %s (priority %d)", event_type, priority)

    def on(
        self,
        event_type: str,
        priority: int = 0,
    ) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator to register an event handler.

        Usage:
            @event_dispatcher.on("UserCreatedEvent")
            async def handle_user_created(event):
                ...
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.register(event_type, handler, priority)
            return handler
        return decorator

    async def publish(
        self,
        event: DomainEvent,
        *,
        wait: bool = True,
    ) -> None:
        """
        Publish a domain event to all registered handlers.

        Args:
            event: The event to publish
            wait: If True, wait for all handlers to complete.
                  If False, run handlers in background.
        """
        if not self._enabled:
            logger.debug("Event dispatcher disabled, skipping: %s", event.event_type)
            return

        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug("No handlers for event: %s", event.event_type)
            return

        logger.info(
            "Publishing event %s (id=%s) to %d handlers",
            event.event_type,
            event.event_id,
            len(handlers),
        )

        async def run_handler(handler: EventHandler) -> None:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    "Handler failed for event %s: %s",
                    event.event_type,
                    e,
                    exc_info=True,
                )

        tasks = [run_handler(handler) for _, handler in handlers]

        if wait:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Fire and forget
            for task in tasks:
                asyncio.create_task(task)

    async def publish_all(
        self,
        events: list[DomainEvent],
        *,
        wait: bool = True,
    ) -> None:
        """
        Publish multiple events.

        Args:
            events: List of events to publish
            wait: If True, wait for all handlers to complete
        """
        if wait:
            for event in events:
                await self.publish(event, wait=True)
        else:
            for event in events:
                await self.publish(event, wait=False)

    def clear_handlers(self, event_type: str | None = None) -> None:
        """
        Clear registered handlers.

        Args:
            event_type: If provided, clear only handlers for this type.
                       If None, clear all handlers.
        """
        if event_type:
            self._handlers[event_type] = []
        else:
            self._handlers.clear()

    def enable(self) -> None:
        """Enable event dispatching."""
        self._enabled = True

    def disable(self) -> None:
        """Disable event dispatching (useful for testing)."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if dispatcher is enabled."""
        return self._enabled


# Singleton instance
event_dispatcher = EventDispatcher()


# =============================================================================
# Common Domain Events
# =============================================================================


@dataclass
class UserCreatedEvent(DomainEvent):
    """Event fired when a new user is created."""

    user_id: int = 0
    email: str = ""
    role: str = ""
    first_name: str = ""
    last_name: str = ""


@dataclass
class UserRoleChangedEvent(DomainEvent):
    """Event fired when a user's role changes."""

    user_id: int = 0
    old_role: str = ""
    new_role: str = ""
    changed_by_user_id: int | None = None


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
class BookingCancelledEvent(DomainEvent):
    """Event fired when a booking is cancelled."""

    booking_id: int = 0
    cancelled_by_user_id: int = 0
    reason: str | None = None
    refund_amount_cents: int = 0


@dataclass
class SessionCompletedEvent(DomainEvent):
    """Event fired when a session completes successfully."""

    booking_id: int = 0
    student_id: int = 0
    tutor_id: int = 0
    duration_minutes: int = 0


@dataclass
class PaymentCompletedEvent(DomainEvent):
    """Event fired when a payment is completed."""

    booking_id: int | None = None
    user_id: int = 0
    amount_cents: int = 0
    currency: str = "USD"
    payment_intent_id: str = ""
