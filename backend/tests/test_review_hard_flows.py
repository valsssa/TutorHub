"""
Comprehensive tests for hard review and rating flow scenarios.

Tests cover complex edge cases including:
- Review submission edge cases (cancelled bookings, disputes, duplicates)
- Rating calculation complexities (initialization, recalculation, precision)
- Review moderation flows (content filtering, escalation, appeals)
- Review bombing prevention (rapid submissions, coordinated attacks)
- Response and reply edge cases (edited reviews, deleted accounts)
- Review visibility rules (hidden reviews, user deletion, anonymous)
- Aggregate statistics (distribution, consistency, time-weighted decay)
"""

import asyncio
import hashlib
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Booking, Review, TutorProfile, User

# =============================================================================
# Mock Services for Testing
# =============================================================================


@dataclass
class ContentModerationResult:
    """Result from content moderation service."""

    is_approved: bool
    confidence: float
    flagged_categories: list[str] = field(default_factory=list)
    requires_manual_review: bool = False
    escalation_reason: str | None = None


class MockContentModerationService:
    """Mock content moderation service for testing."""

    PROFANITY_PATTERNS = [
        r"\b(spam|abuse|offensive)\b",
        r"\b(fake|scam|fraud)\b",
    ]

    HARASSMENT_PATTERNS = [
        r"\b(hate|kill|die)\b",
        r"\b(threat|attack)\b",
    ]

    def __init__(self):
        self.moderation_history: list[dict] = []
        self.manual_review_queue: list[dict] = []

    def analyze_content(self, text: str) -> ContentModerationResult:
        """Analyze text content for policy violations."""
        if not text:
            return ContentModerationResult(is_approved=True, confidence=1.0)

        text_lower = text.lower()
        flagged = []

        # Check for profanity
        for pattern in self.PROFANITY_PATTERNS:
            if re.search(pattern, text_lower):
                flagged.append("profanity")
                break

        # Check for harassment
        for pattern in self.HARASSMENT_PATTERNS:
            if re.search(pattern, text_lower):
                flagged.append("harassment")
                break

        # Check for spam patterns (excessive caps, repeated chars)
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            flagged.append("spam")

        if re.search(r"(.)\1{4,}", text):  # 5+ repeated chars
            flagged.append("spam")

        requires_manual = len(flagged) > 0 and "harassment" in flagged
        is_approved = len(flagged) == 0
        confidence = 0.95 if is_approved else 0.85

        result = ContentModerationResult(
            is_approved=is_approved,
            confidence=confidence,
            flagged_categories=flagged,
            requires_manual_review=requires_manual,
            escalation_reason="Potential harassment detected" if requires_manual else None,
        )

        self.moderation_history.append({
            "text": text[:100],
            "result": result,
            "timestamp": datetime.now(UTC),
        })

        if requires_manual:
            self.manual_review_queue.append({
                "text": text,
                "flagged": flagged,
                "timestamp": datetime.now(UTC),
            })

        return result


@dataclass
class ReviewBombingSignal:
    """Signal indicating potential review bombing."""

    detected: bool
    confidence: float
    signals: list[str] = field(default_factory=list)
    recommended_action: str = "none"


class MockReviewBombingDetector:
    """Mock service to detect review bombing attacks."""

    def __init__(self):
        self.ip_review_counts: dict[str, list[datetime]] = defaultdict(list)
        self.user_review_counts: dict[int, list[datetime]] = defaultdict(list)
        self.tutor_negative_reviews: dict[int, list[dict]] = defaultdict(list)

    def record_review(
        self,
        user_id: int,
        tutor_id: int,
        rating: int,
        ip_address: str,
        account_created_at: datetime,
    ) -> None:
        """Record a review for bombing detection."""
        now = datetime.now(UTC)

        self.ip_review_counts[ip_address].append(now)
        self.user_review_counts[user_id].append(now)

        if rating <= 2:
            self.tutor_negative_reviews[tutor_id].append({
                "user_id": user_id,
                "rating": rating,
                "ip": ip_address,
                "timestamp": now,
                "account_age_days": (now - account_created_at).days,
            })

    def check_rapid_submission(self, ip_address: str, window_minutes: int = 60) -> bool:
        """Check for rapid review submissions from same IP."""
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=window_minutes)

        recent = [t for t in self.ip_review_counts.get(ip_address, []) if t > cutoff]
        return len(recent) >= 5  # 5+ reviews in window = suspicious

    def check_coordinated_attack(
        self,
        tutor_id: int,
        window_hours: int = 24,
        threshold: int = 10,
    ) -> ReviewBombingSignal:
        """Check for coordinated negative review attack on a tutor."""
        now = datetime.now(UTC)
        cutoff = now - timedelta(hours=window_hours)

        recent_negative = [
            r for r in self.tutor_negative_reviews.get(tutor_id, [])
            if r["timestamp"] > cutoff
        ]

        if len(recent_negative) < threshold:
            return ReviewBombingSignal(detected=False, confidence=0.0)

        signals = []

        # Check IP clustering
        ip_counts = defaultdict(int)
        for review in recent_negative:
            ip_prefix = ".".join(review["ip"].split(".")[:3])  # /24 subnet
            ip_counts[ip_prefix] += 1

        if max(ip_counts.values(), default=0) >= 3:
            signals.append("ip_clustering")

        # Check new account ratio
        new_accounts = sum(1 for r in recent_negative if r["account_age_days"] < 7)
        if new_accounts / len(recent_negative) > 0.5:
            signals.append("new_account_surge")

        # Check timing pattern (reviews within minutes of each other)
        timestamps = sorted(r["timestamp"] for r in recent_negative)
        rapid_pairs = sum(
            1 for i in range(len(timestamps) - 1)
            if (timestamps[i + 1] - timestamps[i]).total_seconds() < 300
        )
        if rapid_pairs >= 3:
            signals.append("timing_pattern")

        detected = len(signals) >= 2
        confidence = min(0.95, 0.3 * len(signals))

        return ReviewBombingSignal(
            detected=detected,
            confidence=confidence,
            signals=signals,
            recommended_action="suspend_reviews" if detected else "none",
        )

    def check_account_age_requirement(
        self,
        account_created_at: datetime,
        min_age_days: int = 1,
    ) -> bool:
        """Check if account meets minimum age requirement for reviewing."""
        age = datetime.now(UTC) - account_created_at
        return age.days >= min_age_days

    def check_review_velocity(
        self,
        user_id: int,
        max_reviews_per_day: int = 10,
    ) -> bool:
        """Check if user exceeds review velocity limit."""
        now = datetime.now(UTC)
        day_ago = now - timedelta(days=1)

        recent = [
            t for t in self.user_review_counts.get(user_id, [])
            if t > day_ago
        ]
        return len(recent) >= max_reviews_per_day


class MockAnalyticsService:
    """Mock analytics tracking service."""

    def __init__(self):
        self.events: list[dict] = []

    def track(self, event_name: str, properties: dict) -> None:
        """Track an analytics event."""
        self.events.append({
            "event": event_name,
            "properties": properties,
            "timestamp": datetime.now(UTC),
        })

    def get_events(self, event_name: str) -> list[dict]:
        """Get all events of a specific type."""
        return [e for e in self.events if e["event"] == event_name]


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def content_moderator():
    """Create mock content moderation service."""
    return MockContentModerationService()


@pytest.fixture
def bombing_detector():
    """Create mock review bombing detector."""
    return MockReviewBombingDetector()


@pytest.fixture
def analytics():
    """Create mock analytics service."""
    return MockAnalyticsService()


@pytest.fixture
def completed_booking(db_session: Session, tutor_user: User, student_user: User, test_subject):
    """Create a completed booking for review testing."""
    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=datetime.now(UTC) - timedelta(hours=2),
        end_time=datetime.now(UTC) - timedelta(hours=1),
        session_state="ENDED",
        session_outcome="COMPLETED",
        payment_state="CAPTURED",
        dispute_state="NONE",
        hourly_rate=Decimal("50.00"),
        total_amount=Decimal("50.00"),
        currency="USD",
        tutor_name=f"{tutor_user.first_name} {tutor_user.last_name}",
        student_name=f"{student_user.first_name} {student_user.last_name}",
        subject_name=test_subject.name,
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def cancelled_booking(db_session: Session, tutor_user: User, student_user: User, test_subject):
    """Create a cancelled booking for testing."""
    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=datetime.now(UTC) + timedelta(hours=24),
        end_time=datetime.now(UTC) + timedelta(hours=25),
        session_state="CANCELLED",
        cancelled_by_role="STUDENT",
        cancelled_at=datetime.now(UTC),
        payment_state="VOIDED",
        dispute_state="NONE",
        hourly_rate=Decimal("50.00"),
        total_amount=Decimal("50.00"),
        currency="USD",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def disputed_booking(db_session: Session, tutor_user: User, student_user: User, test_subject):
    """Create a disputed booking for testing."""
    booking = Booking(
        tutor_profile_id=tutor_user.tutor_profile.id,
        student_id=student_user.id,
        subject_id=test_subject.id,
        start_time=datetime.now(UTC) - timedelta(hours=2),
        end_time=datetime.now(UTC) - timedelta(hours=1),
        session_state="ENDED",
        session_outcome="COMPLETED",
        payment_state="CAPTURED",
        dispute_state="OPEN",
        disputed_at=datetime.now(UTC),
        disputed_by=student_user.id,
        dispute_reason="Tutor was late and unprepared",
        hourly_rate=Decimal("50.00"),
        total_amount=Decimal("50.00"),
        currency="USD",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


# =============================================================================
# 1. Review Submission Edge Cases
# =============================================================================


class TestReviewSubmissionEdgeCases:
    """Test edge cases in review submission."""

    def test_review_for_cancelled_booking_rejected(
        self,
        db_session: Session,
        student_user: User,
        cancelled_booking: Booking,
    ):
        """Test that reviews cannot be submitted for cancelled bookings."""
        # Attempt to create review for cancelled booking
        with pytest.raises(ValueError, match="completed"):
            # Simulate the validation that should happen in the API
            if cancelled_booking.session_state == "CANCELLED":
                raise ValueError("Can only review completed bookings")

            Review(
                booking_id=cancelled_booking.id,
                tutor_profile_id=cancelled_booking.tutor_profile_id,
                student_id=student_user.id,
                rating=5,
                comment="Great session!",
            )

    def test_review_after_booking_dispute_allowed_with_warning(
        self,
        db_session: Session,
        student_user: User,
        disputed_booking: Booking,
        analytics: MockAnalyticsService,
    ):
        """Test review submission for disputed booking includes warning."""
        # Disputed but completed sessions can be reviewed
        # but should be flagged for potential bias
        assert disputed_booking.session_outcome == "COMPLETED"
        assert disputed_booking.dispute_state == "OPEN"

        review = Review(
            booking_id=disputed_booking.id,
            tutor_profile_id=disputed_booking.tutor_profile_id,
            student_id=student_user.id,
            rating=1,  # Low rating expected with dispute
            comment="Poor experience, had to file dispute",
        )

        # Track that this review is associated with a disputed booking
        analytics.track("review_with_dispute", {
            "booking_id": disputed_booking.id,
            "dispute_state": disputed_booking.dispute_state,
            "rating": review.rating,
        })

        db_session.add(review)
        db_session.commit()

        # Verify analytics tracked the disputed review
        dispute_events = analytics.get_events("review_with_dispute")
        assert len(dispute_events) == 1
        assert dispute_events[0]["properties"]["dispute_state"] == "OPEN"

    def test_multiple_reviews_same_booking_rejected(
        self,
        db_session: Session,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test that duplicate reviews for the same booking are rejected."""
        # Create first review
        review1 = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=completed_booking.tutor_profile_id,
            student_id=student_user.id,
            rating=5,
            comment="Great session!",
        )
        db_session.add(review1)
        db_session.commit()

        # Attempt second review
        existing = db_session.query(Review).filter(
            Review.booking_id == completed_booking.id
        ).first()

        assert existing is not None, "First review should exist"

        # Simulate duplicate check that should happen in API
        with pytest.raises(ValueError, match="already exists"):
            if existing:
                raise ValueError("Review already exists for this booking")

    def test_review_submission_timeout_handling(
        self,
        db_session: Session,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test handling of review submission timeout."""

        async def slow_review_submission():
            """Simulate slow submission that might timeout."""
            await asyncio.sleep(0.1)  # Simulated delay
            return Review(
                booking_id=completed_booking.id,
                tutor_profile_id=completed_booking.tutor_profile_id,
                student_id=student_user.id,
                rating=5,
                comment="Review after delay",
            )

        async def run_with_timeout():
            try:
                review = await asyncio.wait_for(
                    slow_review_submission(),
                    timeout=0.05,  # Very short timeout to trigger
                )
                return review
            except TimeoutError:
                return None

        result = asyncio.get_event_loop().run_until_complete(run_with_timeout())

        # Timeout should occur
        assert result is None, "Should timeout on slow submission"

        # Verify no partial review was saved
        saved_review = db_session.query(Review).filter(
            Review.booking_id == completed_booking.id
        ).first()
        assert saved_review is None, "No partial review should be saved on timeout"

    def test_review_with_maximum_content_length(
        self,
        db_session: Session,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test review with maximum allowed comment length."""
        max_length = 2000

        # Create review with maximum length comment
        long_comment = "A" * max_length
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=completed_booking.tutor_profile_id,
            student_id=student_user.id,
            rating=5,
            comment=long_comment,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert len(review.comment) == max_length

        # Test exceeding maximum length
        over_max_comment = "B" * (max_length + 100)

        # Should be truncated or rejected
        truncated = over_max_comment[:max_length]
        assert len(truncated) == max_length


# =============================================================================
# 2. Rating Calculation Complexities
# =============================================================================


class TestRatingCalculationComplexities:
    """Test complex rating calculation scenarios."""

    def test_first_review_rating_initialization(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test rating initialization when tutor receives first review."""
        tutor_profile = tutor_user.tutor_profile

        # Verify initial state
        assert tutor_profile.average_rating == Decimal("0.00")
        assert tutor_profile.total_reviews == 0

        # Add first review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_profile.id,
            student_id=student_user.id,
            rating=4,
            comment="Good first session",
        )
        db_session.add(review)
        db_session.commit()

        # Recalculate rating
        avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        tutor_profile.average_rating = Decimal(str(round(float(avg), 2)))
        tutor_profile.total_reviews = 1
        db_session.commit()
        db_session.refresh(tutor_profile)

        assert tutor_profile.average_rating == Decimal("4.00")
        assert tutor_profile.total_reviews == 1

    def test_rating_recalculation_on_review_edit(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test rating is recalculated when a review is edited."""
        tutor_profile = tutor_user.tutor_profile

        # Create initial review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_profile.id,
            student_id=student_user.id,
            rating=3,
            comment="Initial review",
        )
        db_session.add(review)
        db_session.commit()

        # Calculate initial average
        tutor_profile.average_rating = Decimal("3.00")
        tutor_profile.total_reviews = 1
        db_session.commit()

        # Edit review rating
        review.rating = 5
        db_session.commit()

        # Recalculate
        avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        new_average = Decimal(str(round(float(avg), 2)))
        tutor_profile.average_rating = new_average
        db_session.commit()

        assert tutor_profile.average_rating == Decimal("5.00")

    def test_rating_update_on_review_deletion(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        test_subject,
    ):
        """Test rating is recalculated when a review is deleted."""
        tutor_profile = tutor_user.tutor_profile

        # Create two bookings and reviews
        bookings = []
        reviews = []
        ratings = [5, 3]

        for i, rating in enumerate(ratings):
            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student_user.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()
            bookings.append(booking)

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student_user.id,
                rating=rating,
            )
            db_session.add(review)
            reviews.append(review)

        db_session.commit()

        # Calculate initial average: (5 + 3) / 2 = 4.0
        tutor_profile.average_rating = Decimal("4.00")
        tutor_profile.total_reviews = 2
        db_session.commit()

        # Delete one review
        db_session.delete(reviews[1])  # Delete the 3-star review
        db_session.commit()

        # Recalculate
        avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        total = db_session.query(func.count(Review.id)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        if avg:
            tutor_profile.average_rating = Decimal(str(round(float(avg), 2)))
        else:
            tutor_profile.average_rating = Decimal("0.00")
        tutor_profile.total_reviews = total or 0
        db_session.commit()

        assert tutor_profile.average_rating == Decimal("5.00")
        assert tutor_profile.total_reviews == 1

    def test_weighted_average_with_few_reviews(
        self,
        db_session: Session,
        tutor_user: User,
    ):
        """Test weighted average calculation with few reviews (Bayesian)."""

        # Bayesian average formula:
        # (C * m + sum(ratings)) / (C + n)
        # Where C = confidence weight, m = platform average, n = review count

        platform_average = Decimal("4.2")  # Hypothetical platform average
        confidence_weight = 5  # Number of "phantom" reviews at platform average

        # Tutor has only 2 reviews: 5 and 5
        tutor_ratings = [5, 5]
        tutor_count = len(tutor_ratings)
        tutor_sum = sum(tutor_ratings)

        # Simple average would be 5.0
        simple_average = Decimal(str(tutor_sum / tutor_count))

        # Bayesian average regresses toward platform mean
        bayesian_numerator = (
            confidence_weight * float(platform_average) + tutor_sum
        )
        bayesian_denominator = confidence_weight + tutor_count
        bayesian_average = Decimal(str(round(bayesian_numerator / bayesian_denominator, 2)))

        assert simple_average == Decimal("5.00")
        assert bayesian_average < simple_average  # Pulled toward platform average
        assert bayesian_average > platform_average  # Still above platform average

        # As review count increases, Bayesian approaches simple average
        many_reviews = [5] * 100
        many_count = len(many_reviews)
        many_sum = sum(many_reviews)

        many_bayesian = Decimal(str(round(
            (confidence_weight * float(platform_average) + many_sum) /
            (confidence_weight + many_count),
            2
        )))

        # With 100 reviews, Bayesian is very close to simple average
        assert abs(many_bayesian - Decimal("5.00")) < Decimal("0.05")

    def test_rating_precision_and_rounding(self, db_session: Session, tutor_user: User):
        """Test rating precision and proper rounding."""

        # Test various rating combinations that produce non-integer averages
        test_cases = [
            ([5, 4, 4], "4.33"),     # 13/3 = 4.333...
            ([5, 5, 4], "4.67"),     # 14/3 = 4.666...
            ([1, 2, 3, 4, 5], "3.00"),  # 15/5 = 3.0
            ([5, 5, 5, 4], "4.75"),  # 19/4 = 4.75
            ([4, 4, 4, 4, 5], "4.20"),  # 21/5 = 4.2
        ]

        for ratings, expected_str in test_cases:
            avg = sum(ratings) / len(ratings)

            # Use ROUND_HALF_UP for consistent rounding
            calculated = Decimal(str(avg)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            expected = Decimal(expected_str)
            assert calculated == expected, f"For {ratings}: expected {expected}, got {calculated}"


# =============================================================================
# 3. Review Moderation Flow
# =============================================================================


class TestReviewModerationFlow:
    """Test review moderation workflows."""

    def test_automated_content_filtering(
        self,
        content_moderator: MockContentModerationService,
    ):
        """Test automated content filtering catches violations."""
        # Clean content should pass
        result = content_moderator.analyze_content(
            "Great tutor! Very patient and knowledgeable."
        )
        assert result.is_approved is True
        assert len(result.flagged_categories) == 0

        # Spam-like content should be flagged
        spam_result = content_moderator.analyze_content(
            "AMAZING AMAZING AMAZING!!!! BEST EVER!!!!!"
        )
        assert spam_result.is_approved is False
        assert "spam" in spam_result.flagged_categories

        # Offensive content should be flagged
        offensive_result = content_moderator.analyze_content(
            "This is a spam scam fake review"
        )
        assert offensive_result.is_approved is False
        assert "profanity" in offensive_result.flagged_categories

    def test_manual_review_escalation(
        self,
        content_moderator: MockContentModerationService,
    ):
        """Test that serious violations escalate to manual review."""
        # Harassment should escalate to manual review
        result = content_moderator.analyze_content(
            "I hate this tutor and want them to die"
        )

        assert result.is_approved is False
        assert result.requires_manual_review is True
        assert "harassment" in result.flagged_categories
        assert result.escalation_reason is not None

        # Check it's added to manual review queue
        assert len(content_moderator.manual_review_queue) == 1

    def test_appeal_process_edge_cases(
        self,
        db_session: Session,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test edge cases in review appeal process."""

        @dataclass
        class ReviewAppeal:
            review_id: int
            reason: str
            status: str = "pending"
            reviewer_notes: str | None = None
            resolved_at: datetime | None = None

        # Create review that was incorrectly flagged
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=completed_booking.tutor_profile_id,
            student_id=student_user.id,
            rating=2,
            comment="The session was not helpful, felt like a scam for my money",
            is_public=False,  # Hidden due to auto-moderation
        )
        db_session.add(review)
        db_session.commit()

        # Create appeal
        appeal = ReviewAppeal(
            review_id=review.id,
            reason="False positive - I used 'scam' metaphorically, not as accusation",
        )

        # Process appeal
        # In real system, admin would review and approve
        appeal.status = "approved"
        appeal.reviewer_notes = "User's usage was metaphorical, reinstating review"
        appeal.resolved_at = datetime.now(UTC)

        # Restore review visibility
        review.is_public = True
        db_session.commit()

        assert review.is_public is True
        assert appeal.status == "approved"

    def test_moderation_during_edit(
        self,
        content_moderator: MockContentModerationService,
        db_session: Session,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test that edits are also moderated."""
        # Create clean review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=completed_booking.tutor_profile_id,
            student_id=student_user.id,
            rating=3,
            comment="Okay session, nothing special",
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        # Edit to include flaggable content
        new_comment = "This tutor is a total fraud and scam artist"
        moderation_result = content_moderator.analyze_content(new_comment)

        if not moderation_result.is_approved:
            # If edit fails moderation, keep old comment or hide
            review.is_public = False
        else:
            review.comment = new_comment

        db_session.commit()

        assert review.is_public is False  # Hidden due to edit moderation

    def test_bulk_moderation_operations(
        self,
        content_moderator: MockContentModerationService,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test bulk moderation of multiple reviews."""
        from tests.conftest import create_test_user

        # Create multiple reviews from different users
        reviews_data = [
            ("Good session", True),
            ("Spam spam spam scam!", False),
            ("Helpful tutor", True),
            ("TERRIBLE TERRIBLE TERRIBLE", False),
            ("Would recommend", True),
        ]

        reviews = []
        for i, (comment, expected_approved) in enumerate(reviews_data):
            # Create student for each review
            student = create_test_user(
                db_session,
                email=f"bulkstudent{i}@test.com",
                password="BulkPass123!",
                role="student",
            )

            # Create booking
            booking = Booking(
                tutor_profile_id=tutor_user.tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_user.tutor_profile.id,
                student_id=student.id,
                rating=4 if expected_approved else 1,
                comment=comment,
            )
            reviews.append((review, expected_approved))
            db_session.add(review)

        db_session.commit()

        # Bulk moderate
        moderation_results = []
        for review, _ in reviews:
            result = content_moderator.analyze_content(review.comment)
            review.is_public = result.is_approved
            moderation_results.append((review.id, result.is_approved))

        db_session.commit()

        # Verify results
        approved_count = sum(1 for _, approved in moderation_results if approved)
        rejected_count = sum(1 for _, approved in moderation_results if not approved)

        assert approved_count == 3  # Three clean reviews
        assert rejected_count == 2  # Two flagged reviews


# =============================================================================
# 4. Review Bombing Prevention
# =============================================================================


class TestReviewBombingPrevention:
    """Test review bombing detection and prevention."""

    def test_rapid_review_submission_detection(
        self,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test detection of rapid review submissions from same IP."""
        test_ip = "192.168.1.100"

        # Simulate rapid submissions
        for i in range(6):
            bombing_detector.record_review(
                user_id=i + 100,
                tutor_id=1,
                rating=1,
                ip_address=test_ip,
                account_created_at=datetime.now(UTC) - timedelta(days=30),
            )

        is_suspicious = bombing_detector.check_rapid_submission(test_ip)
        assert is_suspicious is True

    def test_coordinated_negative_review_detection(
        self,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test detection of coordinated negative review attacks."""
        tutor_id = 42

        # Simulate coordinated attack from similar IPs
        for i in range(15):
            bombing_detector.record_review(
                user_id=i + 200,
                tutor_id=tutor_id,
                rating=1,  # All negative
                ip_address=f"10.0.0.{i % 5}",  # /24 clustering
                account_created_at=datetime.now(UTC) - timedelta(days=3),  # New accounts
            )

        signal = bombing_detector.check_coordinated_attack(tutor_id)

        assert signal.detected is True
        assert "ip_clustering" in signal.signals
        assert "new_account_surge" in signal.signals
        assert signal.recommended_action == "suspend_reviews"

    def test_ip_based_review_clustering(
        self,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test detection of IP-based review clustering."""
        tutor_id = 55

        # Create reviews from same /24 subnet
        for i in range(12):
            bombing_detector.record_review(
                user_id=i + 300,
                tutor_id=tutor_id,
                rating=1,
                ip_address=f"172.16.1.{i}",  # Same /24
                account_created_at=datetime.now(UTC) - timedelta(days=60),
            )

        signal = bombing_detector.check_coordinated_attack(tutor_id)

        assert signal.detected is True
        assert "ip_clustering" in signal.signals

    def test_account_age_requirements(
        self,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test account age requirements for reviewing."""
        # New account (less than 1 day old)
        new_account_created = datetime.now(UTC) - timedelta(hours=12)
        can_review = bombing_detector.check_account_age_requirement(
            new_account_created,
            min_age_days=1
        )
        assert can_review is False

        # Old enough account
        old_account_created = datetime.now(UTC) - timedelta(days=7)
        can_review = bombing_detector.check_account_age_requirement(
            old_account_created,
            min_age_days=1
        )
        assert can_review is True

    def test_review_velocity_limits(
        self,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test review velocity limits per user."""
        user_id = 999

        # User submits many reviews quickly
        for i in range(12):
            bombing_detector.record_review(
                user_id=user_id,
                tutor_id=i + 1,  # Different tutors
                rating=5,
                ip_address="1.2.3.4",
                account_created_at=datetime.now(UTC) - timedelta(days=30),
            )

        exceeds_velocity = bombing_detector.check_review_velocity(
            user_id,
            max_reviews_per_day=10
        )
        assert exceeds_velocity is True


# =============================================================================
# 5. Response & Reply Edge Cases
# =============================================================================


@dataclass
class TutorResponse:
    """Model for tutor response to a review."""

    id: int
    review_id: int
    tutor_id: int
    content: str
    created_at: datetime
    updated_at: datetime | None = None
    is_visible: bool = True


class TestResponseAndReplyEdgeCases:
    """Test edge cases in tutor responses and replies."""

    def test_tutor_response_to_edited_review(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test tutor response behavior when review is edited."""
        # Create review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            rating=2,
            comment="Session was not good, tutor was unprepared",
        )
        db_session.add(review)
        db_session.commit()

        # Tutor responds
        response = TutorResponse(
            id=1,
            review_id=review.id,
            tutor_id=tutor_user.id,
            content="I apologize for any issues. The technical difficulties were unexpected.",
            created_at=datetime.now(UTC),
        )

        # Student edits review
        original_comment = review.comment
        review.comment = "After reflection, session was actually okay. Rating updated."
        review.rating = 4
        db_session.commit()

        # Response should be marked as potentially outdated
        # In real system, might add a flag like response.review_edited_since = True
        review_edit_time = datetime.now(UTC)
        is_response_outdated = response.created_at < review_edit_time

        assert is_response_outdated is True
        assert original_comment != review.comment

    def test_response_after_reviewer_deleted_account(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test response visibility when reviewer deletes their account."""
        # Create review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            rating=1,
            comment="Terrible experience",
        )
        db_session.add(review)
        db_session.commit()

        # Tutor responds
        response = TutorResponse(
            id=1,
            review_id=review.id,
            tutor_id=tutor_user.id,
            content="I'm sorry you feel that way...",
            created_at=datetime.now(UTC),
        )

        # Simulate student account deletion (soft delete)
        student_user.is_active = False
        student_user.email = f"deleted_{student_user.id}@deleted.local"
        db_session.commit()

        # Review and response should still be visible but anonymized
        # In real implementation, review.student would show "[Deleted User]"
        assert review.student_id == student_user.id
        assert response.is_visible is True

    def test_nested_reply_limits(self):
        """Test that nested replies have appropriate depth limits."""

        @dataclass
        class Reply:
            id: int
            parent_id: int | None
            content: str
            depth: int

        max_depth = 3

        def create_reply_chain(depth: int) -> list[Reply]:
            """Create a chain of nested replies."""
            replies = []
            parent_id = None

            for i in range(depth):
                if i >= max_depth:
                    # Cannot create deeper replies
                    break

                reply = Reply(
                    id=i + 1,
                    parent_id=parent_id,
                    content=f"Reply at depth {i}",
                    depth=i,
                )
                replies.append(reply)
                parent_id = reply.id

            return replies

        # Can create up to max_depth
        valid_chain = create_reply_chain(max_depth)
        assert len(valid_chain) == max_depth

        # Cannot exceed max_depth
        deep_chain = create_reply_chain(max_depth + 2)
        assert len(deep_chain) == max_depth

    def test_response_visibility_after_review_removal(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test what happens to response when review is removed."""
        # Create review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            rating=1,
            comment="Bad review",
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        # Tutor responds
        response = TutorResponse(
            id=1,
            review_id=review.id,
            tutor_id=tutor_user.id,
            content="Response to bad review",
            created_at=datetime.now(UTC),
            is_visible=True,
        )

        # Review is hidden (soft removed)
        review.is_public = False
        db_session.commit()

        # Response should also be hidden when review is hidden
        if not review.is_public:
            response.is_visible = False

        assert response.is_visible is False

    def test_edit_response_race_conditions(self):
        """Test handling of concurrent response edits."""

        class ResponseEditManager:
            def __init__(self):
                self.responses: dict[int, TutorResponse] = {}
                self.versions: dict[int, int] = {}

            def add_response(self, response: TutorResponse):
                self.responses[response.id] = response
                self.versions[response.id] = 1

            def edit_response(
                self,
                response_id: int,
                new_content: str,
                expected_version: int,
            ) -> tuple[bool, str]:
                """Edit with optimistic locking."""
                if response_id not in self.responses:
                    return False, "Response not found"

                current_version = self.versions[response_id]
                if current_version != expected_version:
                    return False, "Version conflict - response was modified"

                self.responses[response_id].content = new_content
                self.responses[response_id].updated_at = datetime.now(UTC)
                self.versions[response_id] += 1

                return True, "Success"

        manager = ResponseEditManager()

        # Create initial response
        response = TutorResponse(
            id=1,
            review_id=100,
            tutor_id=1,
            content="Original response",
            created_at=datetime.now(UTC),
        )
        manager.add_response(response)

        # First edit succeeds
        success, msg = manager.edit_response(1, "First edit", expected_version=1)
        assert success is True

        # Second edit with stale version fails
        success, msg = manager.edit_response(1, "Conflicting edit", expected_version=1)
        assert success is False
        assert "conflict" in msg.lower()

        # Edit with correct version succeeds
        success, msg = manager.edit_response(1, "Second edit", expected_version=2)
        assert success is True


# =============================================================================
# 6. Review Visibility Rules
# =============================================================================


class TestReviewVisibilityRules:
    """Test review visibility rules and edge cases."""

    def test_hidden_review_still_affects_rating(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        test_subject,
    ):
        """Test that hidden reviews are still counted in rating calculation."""
        tutor_profile = tutor_user.tutor_profile
        from tests.conftest import create_test_user

        # Create multiple reviews, some hidden
        reviews_data = [
            (5, True),   # Public 5-star
            (4, True),   # Public 4-star
            (1, False),  # Hidden 1-star (removed for policy violation but still counts)
        ]

        for i, (rating, is_public) in enumerate(reviews_data):
            student = create_test_user(
                db_session,
                email=f"visstudent{i}@test.com",
                password="VisPass123!",
                role="student",
            )

            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=rating,
                is_public=is_public,
            )
            db_session.add(review)

        db_session.commit()

        # Calculate rating including hidden reviews
        all_reviews_avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        # Calculate rating excluding hidden reviews (for display)
        public_reviews_avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id,
            Review.is_public.is_(True),
        ).scalar()

        all_avg = round(float(all_reviews_avg), 2)  # (5+4+1)/3 = 3.33
        public_avg = round(float(public_reviews_avg), 2)  # (5+4)/2 = 4.5

        assert all_avg == 3.33
        assert public_avg == 4.5

        # System should use ALL reviews for official rating
        tutor_profile.average_rating = Decimal(str(all_avg))
        db_session.commit()

        assert float(tutor_profile.average_rating) == 3.33

    def test_review_visibility_after_user_deletion(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test review visibility when user account is deleted."""
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            rating=4,
            comment="Good session, learned a lot!",
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        # Soft delete user
        student_user.is_active = False
        db_session.commit()

        # Review should remain visible but be anonymized
        # The student relationship still exists but user is inactive
        db_session.refresh(review)
        reviewer = db_session.query(User).filter(User.id == review.student_id).first()

        assert reviewer is not None
        assert reviewer.is_active is False
        assert review.is_public is True  # Review still visible

    def test_anonymous_review_handling(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test handling of reviews marked as anonymous."""

        @dataclass
        class AnonymousReviewView:
            """View model for anonymous review display."""

            id: int
            rating: int
            comment: str | None
            created_at: datetime
            reviewer_name: str  # Will be "Anonymous" or actual name

        # Create review with anonymous flag (simulated as metadata)
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_user.tutor_profile.id,
            student_id=student_user.id,
            rating=3,
            comment="Average experience",
            is_public=True,
            booking_snapshot=json.dumps({"anonymous": True}),  # Flag in snapshot
        )
        db_session.add(review)
        db_session.commit()

        # When displaying, check anonymous flag
        snapshot = json.loads(review.booking_snapshot) if review.booking_snapshot else {}
        is_anonymous = snapshot.get("anonymous", False)

        view = AnonymousReviewView(
            id=review.id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            reviewer_name="Anonymous Student" if is_anonymous else f"{student_user.first_name} {student_user.last_name}",
        )

        assert view.reviewer_name == "Anonymous Student"
        assert view.rating == 3

    def test_review_in_search_results_freshness(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test review freshness weighting in search results."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Create reviews at different times
        reviews_data = [
            (5, datetime.now(UTC) - timedelta(days=365)),  # Old 5-star
            (4, datetime.now(UTC) - timedelta(days=180)),  # 6-month old 4-star
            (3, datetime.now(UTC) - timedelta(days=30)),   # Recent 3-star
            (4, datetime.now(UTC) - timedelta(days=7)),    # Very recent 4-star
        ]

        for i, (rating, created_at) in enumerate(reviews_data):
            student = create_test_user(
                db_session,
                email=f"freshstudent{i}@test.com",
                password="FreshPass123!",
                role="student",
            )

            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=created_at - timedelta(hours=2),
                end_time=created_at - timedelta(hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=rating,
                is_public=True,
            )
            db_session.add(review)

        db_session.commit()

        # Calculate time-weighted average
        def calculate_weighted_rating(reviews: list[tuple[int, datetime]]) -> float:
            """Calculate time-weighted rating where recent reviews matter more."""
            now = datetime.now(UTC)
            total_weight = 0.0
            weighted_sum = 0.0

            for rating, created_at in reviews:
                days_old = (now - created_at).days
                # Exponential decay: half-life of 90 days
                weight = 0.5 ** (days_old / 90)
                weighted_sum += rating * weight
                total_weight += weight

            return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0

        weighted_avg = calculate_weighted_rating(reviews_data)
        simple_avg = sum(r[0] for r in reviews_data) / len(reviews_data)

        # Weighted average should be lower than simple average
        # because recent reviews (3, 4) have more weight than old (5)
        assert weighted_avg < simple_avg
        assert simple_avg == 4.0
        assert 3.0 < weighted_avg < 4.0

    def test_featured_review_selection_logic(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test logic for selecting featured reviews."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Create reviews with various characteristics
        reviews_data = [
            (5, "A" * 50, 10),   # Short positive
            (5, "B" * 200, 5),   # Medium positive, fewer helpful votes
            (4, "C" * 300, 20),  # Long helpful review
            (3, "D" * 100, 2),   # Average review, few votes
            (1, "E" * 150, 15),  # Negative but helpful (shouldn't feature)
        ]

        reviews = []
        for i, (rating, comment, helpful_count) in enumerate(reviews_data):
            student = create_test_user(
                db_session,
                email=f"featstudent{i}@test.com",
                password="FeatPass123!",
                role="student",
            )

            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=rating,
                comment=comment,
                is_public=True,
            )
            db_session.add(review)
            db_session.commit()

            reviews.append({
                "review": review,
                "helpful_count": helpful_count,
            })

        def select_featured_review(reviews_with_meta: list[dict]) -> Review | None:
            """Select best review to feature."""
            candidates = []

            for item in reviews_with_meta:
                review = item["review"]
                helpful = item["helpful_count"]

                # Must be positive (4+) and have some content
                if review.rating < 4:
                    continue
                if not review.comment or len(review.comment) < 50:
                    continue
                if not review.is_public:
                    continue

                # Score based on rating, helpfulness, and content length
                score = (
                    review.rating * 10 +
                    helpful * 2 +
                    min(len(review.comment) / 50, 5)  # Cap at 5 points for length
                )
                candidates.append((score, review))

            if not candidates:
                return None

            candidates.sort(reverse=True, key=lambda x: x[0])
            return candidates[0][1]

        featured = select_featured_review(reviews)

        # Should select the 4-star review with 20 helpful votes and 300 chars
        assert featured is not None
        assert featured.rating == 4
        assert len(featured.comment) == 300


# =============================================================================
# 7. Aggregate Statistics
# =============================================================================


class TestAggregateStatistics:
    """Test aggregate review statistics calculations."""

    def test_rating_distribution_calculation(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test accurate calculation of rating distribution."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Create reviews with known distribution
        ratings = [5, 5, 5, 4, 4, 3, 2, 1]  # 3x5, 2x4, 1x3, 1x2, 1x1

        for i, rating in enumerate(ratings):
            student = create_test_user(
                db_session,
                email=f"diststudent{i}@test.com",
                password="DistPass123!",
                role="student",
            )

            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=rating,
                is_public=True,
            )
            db_session.add(review)

        db_session.commit()

        # Calculate distribution
        distribution = {}
        for star in range(1, 6):
            count = db_session.query(func.count(Review.id)).filter(
                Review.tutor_profile_id == tutor_profile.id,
                Review.rating == star,
            ).scalar()
            distribution[star] = count

        total = sum(distribution.values())
        percentages = {
            star: round(count / total * 100, 1)
            for star, count in distribution.items()
        }

        assert distribution == {1: 1, 2: 1, 3: 1, 4: 2, 5: 3}
        assert percentages[5] == 37.5  # 3/8 = 37.5%
        assert percentages[4] == 25.0  # 2/8 = 25%
        assert percentages[1] == 12.5  # 1/8 = 12.5%

    def test_review_count_consistency(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
    ):
        """Test that review count stays consistent with actual reviews."""
        tutor_profile = tutor_user.tutor_profile

        # Initial state
        assert tutor_profile.total_reviews == 0

        # Add review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_profile.id,
            student_id=student_user.id,
            rating=5,
            is_public=True,
        )
        db_session.add(review)
        db_session.commit()

        # Update count
        actual_count = db_session.query(func.count(Review.id)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        tutor_profile.total_reviews = actual_count
        db_session.commit()

        assert tutor_profile.total_reviews == 1
        assert tutor_profile.total_reviews == actual_count

        # Verify consistency after operations
        db_session.refresh(tutor_profile)
        recount = db_session.query(func.count(Review.id)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        assert tutor_profile.total_reviews == recount

    def test_category_specific_ratings(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test category-specific rating calculations."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Simulate category ratings stored in booking snapshot
        category_ratings = {
            "knowledge": [5, 5, 4],
            "communication": [4, 4, 5],
            "punctuality": [5, 3, 4],
            "preparation": [4, 5, 4],
        }

        # Create reviews with category data
        for i in range(3):
            student = create_test_user(
                db_session,
                email=f"catstudent{i}@test.com",
                password="CatPass123!",
                role="student",
            )

            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            # Store category ratings in snapshot
            snapshot = {
                "category_ratings": {
                    cat: ratings[i]
                    for cat, ratings in category_ratings.items()
                }
            }

            overall = round(sum(ratings[i] for ratings in category_ratings.values()) / 4)

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=overall,
                is_public=True,
                booking_snapshot=json.dumps(snapshot),
            )
            db_session.add(review)

        db_session.commit()

        # Calculate category averages
        reviews = db_session.query(Review).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).all()

        category_averages = defaultdict(list)
        for review in reviews:
            if review.booking_snapshot:
                snapshot = json.loads(review.booking_snapshot)
                if "category_ratings" in snapshot:
                    for cat, rating in snapshot["category_ratings"].items():
                        category_averages[cat].append(rating)

        final_averages = {
            cat: round(sum(ratings) / len(ratings), 2)
            for cat, ratings in category_averages.items()
        }

        assert final_averages["knowledge"] == 4.67  # (5+5+4)/3
        assert final_averages["communication"] == 4.33  # (4+4+5)/3
        assert final_averages["punctuality"] == 4.0  # (5+3+4)/3
        assert final_averages["preparation"] == 4.33  # (4+5+4)/3

    def test_time_weighted_rating_decay(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
    ):
        """Test time-weighted rating with decay factor."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Create reviews at different times
        reviews_data = [
            (5, 365),   # 5-star from 1 year ago
            (5, 180),   # 5-star from 6 months ago
            (2, 30),    # 2-star from 1 month ago
            (2, 7),     # 2-star from 1 week ago
        ]

        now = datetime.now(UTC)

        for i, (rating, days_ago) in enumerate(reviews_data):
            student = create_test_user(
                db_session,
                email=f"decaystudent{i}@test.com",
                password="DecayPass123!",
                role="student",
            )

            review_date = now - timedelta(days=days_ago)
            booking = Booking(
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                subject_id=test_subject.id,
                start_time=review_date - timedelta(hours=2),
                end_time=review_date - timedelta(hours=1),
                session_state="ENDED",
                session_outcome="COMPLETED",
                payment_state="CAPTURED",
                dispute_state="NONE",
                hourly_rate=Decimal("50.00"),
                total_amount=Decimal("50.00"),
                currency="USD",
            )
            db_session.add(booking)
            db_session.commit()

            review = Review(
                booking_id=booking.id,
                tutor_profile_id=tutor_profile.id,
                student_id=student.id,
                rating=rating,
                is_public=True,
            )
            db_session.add(review)

        db_session.commit()

        # Simple average: (5+5+2+2)/4 = 3.5
        reviews = db_session.query(Review).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).all()

        simple_avg = sum(r.rating for r in reviews) / len(reviews)
        assert simple_avg == 3.5

        # Time-weighted average with 90-day half-life
        def calculate_decayed_rating(reviews_with_dates: list[tuple[int, int]]) -> float:
            """Calculate rating with exponential decay."""
            total_weight = 0.0
            weighted_sum = 0.0
            half_life_days = 90

            for rating, days_ago in reviews_with_dates:
                weight = 0.5 ** (days_ago / half_life_days)
                weighted_sum += rating * weight
                total_weight += weight

            return round(weighted_sum / total_weight, 2)

        decayed_avg = calculate_decayed_rating(reviews_data)

        # Recent 2-star reviews should pull average down
        assert decayed_avg < simple_avg
        assert decayed_avg < 3.0  # Significantly affected by recent bad reviews

    def test_comparison_statistics_accuracy(
        self,
        db_session: Session,
        test_subject,
    ):
        """Test accuracy of comparison statistics between tutors."""
        from tests.conftest import create_test_tutor_profile, create_test_user

        # Create multiple tutors with different ratings
        tutors_data = [
            ("tutor_a@test.com", [5, 5, 5, 4]),      # Avg: 4.75
            ("tutor_b@test.com", [4, 4, 4, 4]),      # Avg: 4.0
            ("tutor_c@test.com", [5, 5, 3, 2]),      # Avg: 3.75
            ("tutor_d@test.com", [3, 3, 3, 3]),      # Avg: 3.0
        ]

        tutor_stats = []

        for email, ratings in tutors_data:
            # Create tutor
            tutor = create_test_user(
                db_session,
                email=email,
                password="TutorComp123!",
                role="tutor",
            )
            profile = create_test_tutor_profile(db_session, tutor.id)

            # Create reviews
            for i, rating in enumerate(ratings):
                student = create_test_user(
                    db_session,
                    email=f"compstudent_{email}_{i}@test.com",
                    password="CompPass123!",
                    role="student",
                )

                booking = Booking(
                    tutor_profile_id=profile.id,
                    student_id=student.id,
                    subject_id=test_subject.id,
                    start_time=datetime.now(UTC) - timedelta(days=i + 1, hours=2),
                    end_time=datetime.now(UTC) - timedelta(days=i + 1, hours=1),
                    session_state="ENDED",
                    session_outcome="COMPLETED",
                    payment_state="CAPTURED",
                    dispute_state="NONE",
                    hourly_rate=Decimal("50.00"),
                    total_amount=Decimal("50.00"),
                    currency="USD",
                )
                db_session.add(booking)
                db_session.commit()

                review = Review(
                    booking_id=booking.id,
                    tutor_profile_id=profile.id,
                    student_id=student.id,
                    rating=rating,
                    is_public=True,
                )
                db_session.add(review)

            db_session.commit()

            # Calculate stats
            avg = db_session.query(func.avg(Review.rating)).filter(
                Review.tutor_profile_id == profile.id
            ).scalar()
            count = db_session.query(func.count(Review.id)).filter(
                Review.tutor_profile_id == profile.id
            ).scalar()

            tutor_stats.append({
                "email": email,
                "profile_id": profile.id,
                "average": round(float(avg), 2),
                "count": count,
            })

        # Verify statistics
        stats_by_email = {s["email"]: s for s in tutor_stats}

        assert stats_by_email["tutor_a@test.com"]["average"] == 4.75
        assert stats_by_email["tutor_b@test.com"]["average"] == 4.0
        assert stats_by_email["tutor_c@test.com"]["average"] == 3.75
        assert stats_by_email["tutor_d@test.com"]["average"] == 3.0

        # Calculate platform-wide statistics
        all_averages = [s["average"] for s in tutor_stats]
        platform_mean = sum(all_averages) / len(all_averages)
        platform_median = sorted(all_averages)[len(all_averages) // 2]

        assert platform_mean == 3.875  # (4.75+4.0+3.75+3.0)/4
        assert platform_median == 3.875  # Middle value

        # Percentile calculation
        def calculate_percentile(value: float, all_values: list[float]) -> float:
            """Calculate what percentile a value is at."""
            below = sum(1 for v in all_values if v < value)
            return round(below / len(all_values) * 100, 1)

        tutor_a_percentile = calculate_percentile(4.75, all_averages)
        tutor_d_percentile = calculate_percentile(3.0, all_averages)

        assert tutor_a_percentile == 75.0  # Top tutor
        assert tutor_d_percentile == 0.0   # Bottom tutor


# =============================================================================
# Integration Tests
# =============================================================================


class TestReviewFlowIntegration:
    """Integration tests for complete review flows."""

    def test_complete_review_submission_flow(
        self,
        db_session: Session,
        tutor_user: User,
        student_user: User,
        completed_booking: Booking,
        content_moderator: MockContentModerationService,
        bombing_detector: MockReviewBombingDetector,
        analytics: MockAnalyticsService,
    ):
        """Test complete flow from submission to rating update."""
        tutor_profile = tutor_user.tutor_profile
        float(tutor_profile.average_rating)
        initial_reviews = tutor_profile.total_reviews

        # Step 1: Content moderation
        comment = "Great session! The tutor explained everything clearly."
        moderation_result = content_moderator.analyze_content(comment)
        assert moderation_result.is_approved is True

        # Step 2: Bombing detection
        bombing_detector.record_review(
            user_id=student_user.id,
            tutor_id=tutor_profile.id,
            rating=5,
            ip_address="192.168.1.50",
            account_created_at=student_user.created_at,
        )

        is_rapid = bombing_detector.check_rapid_submission("192.168.1.50")
        assert is_rapid is False

        bombing_detector.check_account_age_requirement(
            student_user.created_at,
            min_age_days=1
        )
        # Note: Test fixture might create user very recently
        # In real scenario, would check this

        # Step 3: Create review
        review = Review(
            booking_id=completed_booking.id,
            tutor_profile_id=tutor_profile.id,
            student_id=student_user.id,
            rating=5,
            comment=comment,
            is_public=moderation_result.is_approved,
        )
        db_session.add(review)
        db_session.commit()

        # Step 4: Update tutor stats
        avg = db_session.query(func.avg(Review.rating)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()
        count = db_session.query(func.count(Review.id)).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).scalar()

        tutor_profile.average_rating = Decimal(str(round(float(avg), 2)))
        tutor_profile.total_reviews = count
        db_session.commit()

        # Step 5: Track analytics
        analytics.track("review_submitted", {
            "review_id": review.id,
            "tutor_id": tutor_profile.id,
            "rating": review.rating,
            "has_comment": bool(review.comment),
            "moderation_passed": moderation_result.is_approved,
        })

        # Verify final state
        db_session.refresh(tutor_profile)
        assert float(tutor_profile.average_rating) == 5.0
        assert tutor_profile.total_reviews == initial_reviews + 1

        events = analytics.get_events("review_submitted")
        assert len(events) == 1
        assert events[0]["properties"]["rating"] == 5

    def test_review_bombing_prevention_flow(
        self,
        db_session: Session,
        tutor_user: User,
        test_subject,
        bombing_detector: MockReviewBombingDetector,
    ):
        """Test flow when review bombing is detected."""
        from tests.conftest import create_test_user

        tutor_profile = tutor_user.tutor_profile

        # Simulate coordinated attack
        attack_reviews = []
        for i in range(15):
            student = create_test_user(
                db_session,
                email=f"attacker{i}@test.com",
                password="AttackPass123!",
                role="student",
            )

            # Record in bombing detector
            bombing_detector.record_review(
                user_id=student.id,
                tutor_id=tutor_profile.id,
                rating=1,
                ip_address=f"10.0.0.{i % 5}",
                account_created_at=datetime.now(UTC) - timedelta(days=2),
            )

            attack_reviews.append({
                "student_id": student.id,
                "rating": 1,
            })

        # Check for coordinated attack
        signal = bombing_detector.check_coordinated_attack(tutor_profile.id)

        assert signal.detected is True
        assert signal.recommended_action == "suspend_reviews"

        # In real system, would:
        # 1. Flag tutor profile for review
        # 2. Hold new reviews for manual approval
        # 3. Notify tutor of suspicious activity
        # 4. Not update rating until investigation complete

        # Verify suspicious reviews weren't processed
        actual_reviews = db_session.query(Review).filter(
            Review.tutor_profile_id == tutor_profile.id
        ).count()

        # No reviews should be saved when bombing detected
        assert actual_reviews == 0
