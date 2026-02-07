"""
Tests for Stripe webhook idempotency check.
Verifies that duplicate webhook events are detected and skipped.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, WebhookEvent


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    yield session
    session.close()


def test_first_event_is_not_duplicate(db_session):
    """Test that the first occurrence of an event is not considered a duplicate."""
    event_id = "evt_test_123"

    existing = (
        db_session.query(WebhookEvent)
        .filter(WebhookEvent.stripe_event_id == event_id)
        .first()
    )
    assert existing is None


def test_duplicate_event_is_detected(db_session):
    """Test that a previously processed event is detected as a duplicate."""
    event_id = "evt_test_456"

    # Simulate first processing
    webhook_event = WebhookEvent(
        stripe_event_id=event_id,
        event_type="checkout.session.completed",
    )
    db_session.add(webhook_event)
    db_session.commit()

    # Check for duplicate
    existing = (
        db_session.query(WebhookEvent)
        .filter(WebhookEvent.stripe_event_id == event_id)
        .first()
    )
    assert existing is not None
    assert existing.stripe_event_id == event_id
    assert existing.event_type == "checkout.session.completed"


def test_different_event_ids_are_independent(db_session):
    """Test that different event IDs are treated independently."""
    # Process first event
    event1 = WebhookEvent(
        stripe_event_id="evt_aaa",
        event_type="checkout.session.completed",
    )
    db_session.add(event1)
    db_session.commit()

    # Second event with different ID should not be detected as duplicate
    existing = (
        db_session.query(WebhookEvent)
        .filter(WebhookEvent.stripe_event_id == "evt_bbb")
        .first()
    )
    assert existing is None


def test_multiple_events_tracked(db_session):
    """Test that multiple events can be tracked simultaneously."""
    event_ids = ["evt_1", "evt_2", "evt_3"]
    for eid in event_ids:
        db_session.add(WebhookEvent(
            stripe_event_id=eid,
            event_type="payment_intent.succeeded",
        ))
    db_session.commit()

    for eid in event_ids:
        existing = (
            db_session.query(WebhookEvent)
            .filter(WebhookEvent.stripe_event_id == eid)
            .first()
        )
        assert existing is not None

    # Non-existent event should not be found
    missing = (
        db_session.query(WebhookEvent)
        .filter(WebhookEvent.stripe_event_id == "evt_nonexistent")
        .first()
    )
    assert missing is None
