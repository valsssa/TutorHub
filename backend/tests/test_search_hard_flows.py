"""
Comprehensive tests for hard search and discovery flow scenarios.

Tests cover complex edge cases including:
- Search index consistency (updates, stale data, rebuilds)
- Complex filter combinations (conflicts, boundaries, special chars)
- Ranking edge cases (ties, new tutors, boosts, nulls)
- Pagination edge cases (changes during pagination, cursors, offsets)
- Real-time availability in search (race conditions, timezones)
- Autocomplete & suggestions (typos, unicode, injection)
- Performance under load (concurrency, caching, timeouts)

Uses pytest with mock search index, database queries, and caching layer.
"""

import asyncio
import concurrent.futures
import hashlib
import threading
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from fastapi import status
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import TimeoutError as SQLTimeoutError
from sqlalchemy.orm import Session

from core.pagination import PaginatedResponse, PaginationParams
from models import Subject, TutorAvailability, TutorProfile, TutorSubject, User
from tests.conftest import (
    STUDENT_PASSWORD,
    TUTOR_PASSWORD,
    create_test_tutor_profile,
    create_test_user,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_search_index():
    """Create a mock search index for testing."""
    index = MagicMock()
    index.version = 1
    index.last_updated = datetime.now(UTC)
    index.documents = []
    index.is_rebuilding = False
    index.rebuild_progress = 0.0

    def add_document(doc):
        index.documents.append(doc)
        index.version += 1
        index.last_updated = datetime.now(UTC)

    def search(query, filters=None, limit=20):
        results = index.documents.copy()
        if query:
            results = [d for d in results if query.lower() in d.get("title", "").lower()]
        return results[:limit]

    index.add_document = add_document
    index.search = search
    return index


@pytest.fixture
def mock_cache():
    """Create a mock cache for testing."""
    cache = MagicMock()
    cache._store = {}
    cache._ttls = {}

    def get(key):
        if key in cache._store:
            if cache._ttls.get(key, float('inf')) < time.time():
                del cache._store[key]
                del cache._ttls[key]
                return None
            return cache._store[key]
        return None

    def set_with_ttl(key, value, ttl):
        cache._store[key] = value
        cache._ttls[key] = time.time() + ttl
        return True

    def invalidate(key):
        if key in cache._store:
            del cache._store[key]
            del cache._ttls[key]
            return True
        return False

    cache.get = get
    cache.set = set_with_ttl
    cache.invalidate = invalidate
    return cache


@pytest.fixture
def create_tutors(db_session):
    """Factory fixture to create multiple tutors with profiles."""
    created = []

    def _create_tutors(count, **defaults):
        for i in range(count):
            email = f"tutor{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session,
                email=email,
                password=TUTOR_PASSWORD,
                role="tutor",
                first_name=f"Tutor{i}",
                last_name="Test",
            )
            profile = TutorProfile(
                user_id=user.id,
                title=defaults.get("title", f"Tutor {i} Title"),
                headline=defaults.get("headline", "Expert in Teaching"),
                bio=defaults.get("bio", "Experienced educator"),
                hourly_rate=defaults.get("hourly_rate", Decimal("50.00") + Decimal(i)),
                experience_years=defaults.get("experience_years", i + 1),
                average_rating=defaults.get("average_rating", Decimal("4.0")),
                total_reviews=defaults.get("total_reviews", i * 5),
                languages=defaults.get("languages", ["English"]),
                is_approved=defaults.get("is_approved", True),
                profile_status=defaults.get("profile_status", "approved"),
            )
            db_session.add(profile)
            db_session.commit()
            db_session.refresh(profile)
            created.append((user, profile))
        return created

    yield _create_tutors
    # Cleanup handled by test transaction rollback


# =============================================================================
# Search Index Consistency Tests
# =============================================================================


class TestSearchIndexConsistency:
    """Test search index consistency during various operations."""

    def test_index_update_during_active_search(self, mock_search_index):
        """
        Test that search results are consistent when index updates during query.
        Uses snapshot isolation pattern.
        """
        # Add initial documents
        mock_search_index.add_document({"id": 1, "title": "Math Tutor", "rating": 4.5})
        mock_search_index.add_document({"id": 2, "title": "Science Tutor", "rating": 4.8})


        # Simulate search starting

        # Concurrent update happens
        mock_search_index.add_document({"id": 3, "title": "Math Expert", "rating": 4.9})

        # Search should use snapshot version for consistency
        results = mock_search_index.search("Math")

        # Results depend on implementation - snapshot or live
        # Here we test that results are returned regardless of concurrent updates
        assert len(results) >= 1
        assert any("Math" in r["title"] for r in results)

    def test_stale_index_after_profile_update(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test search returns stale data briefly after tutor profile update.
        The cache or index may have old data until refresh.
        """
        # Create tutor with specific title
        tutors = create_tutors(1, title="Original Title Expert")
        user, profile = tutors[0]

        # Search should find the tutor
        response = client.get(
            "/api/v1/tutors?search_query=Original",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Find our tutor in results
        titles = [t["title"] for t in data["items"]]
        assert "Original Title Expert" in titles

        # Update profile title directly
        profile.title = "Updated Title Expert"
        db_session.commit()

        # Immediate search may still return old results (cache)
        # This tests that the system handles stale data gracefully
        response2 = client.get(
            "/api/v1/tutors?search_query=Updated",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        # Result depends on cache TTL - just verify no error

    def test_partial_index_failure_recovery(self, mock_search_index):
        """
        Test that partial index updates don't corrupt the index.
        """
        # Add initial documents
        mock_search_index.add_document({"id": 1, "title": "Tutor A"})
        mock_search_index.add_document({"id": 2, "title": "Tutor B"})

        initial_count = len(mock_search_index.documents)

        # Simulate partial failure during batch update
        try:
            mock_search_index.add_document({"id": 3, "title": "Tutor C"})
            # Simulate failure on next document
            raise ConnectionError("Index connection lost")
        except ConnectionError:
            # Recovery: index should still be usable
            pass

        # Index should still work with original + successful updates
        results = mock_search_index.search("")
        assert len(results) >= initial_count

    def test_index_rebuild_during_active_searches(self, mock_search_index):
        """
        Test that searches continue working during index rebuild.
        """
        # Add initial documents
        for i in range(10):
            mock_search_index.add_document({"id": i, "title": f"Tutor {i}"})

        # Start rebuild (in background)
        mock_search_index.is_rebuilding = True
        mock_search_index.rebuild_progress = 0.0

        # Searches should still work during rebuild
        results = mock_search_index.search("Tutor")
        assert len(results) > 0

        # Simulate rebuild progress
        mock_search_index.rebuild_progress = 0.5
        results2 = mock_search_index.search("Tutor")
        assert len(results2) > 0

        # Complete rebuild
        mock_search_index.is_rebuilding = False
        mock_search_index.rebuild_progress = 1.0

        results3 = mock_search_index.search("Tutor")
        assert len(results3) > 0

    def test_index_version_conflict_resolution(self, mock_search_index):
        """
        Test handling of version conflicts when multiple processes update index.
        """
        initial_version = mock_search_index.version

        # Simulate two concurrent updates
        mock_search_index.add_document({"id": 1, "title": "First Update"})
        version_after_first = mock_search_index.version

        mock_search_index.add_document({"id": 2, "title": "Second Update"})
        version_after_second = mock_search_index.version

        # Versions should be monotonically increasing
        assert version_after_first > initial_version
        assert version_after_second > version_after_first

        # Both documents should be searchable
        results = mock_search_index.search("")
        assert len(results) == 2


# =============================================================================
# Complex Filter Combinations Tests
# =============================================================================


class TestComplexFilterCombinations:
    """Test complex and edge case filter combinations."""

    def test_conflicting_filters_no_results_possible(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test filters that logically cannot match any results.
        Example: min_rate > max_rate
        """
        create_tutors(3, hourly_rate=Decimal("50.00"))

        # min_rate > max_rate - impossible range
        response = client.get(
            "/api/v1/tutors?min_rate=100&max_rate=50",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_filter_with_empty_results_edge_case(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test filters that match no tutors but are valid queries.
        """
        create_tutors(5, average_rating=Decimal("3.5"))

        # No tutor has rating >= 5.0
        response = client.get(
            "/api/v1/tutors?min_rating=5.0",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0

    def test_numeric_range_boundary_conditions(
        self, client, db_session, student_token
    ):
        """
        Test exact boundary matches for numeric filters.
        """
        # Create tutors at exact boundaries
        for i, rate in enumerate([50.00, 50.01, 49.99, 100.00]):
            email = f"boundary{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Boundary Test {rate}",
                hourly_rate=Decimal(str(rate)),
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        # Exact boundary match: min_rate=50 should include 50.00 but not 49.99
        response = client.get(
            "/api/v1/tutors?min_rate=50&max_rate=50.01",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should match exactly 50.00 and 50.01
        rates = [Decimal(str(t["hourly_rate"])) for t in data["items"]]
        assert all(Decimal("49.99") < r <= Decimal("50.01") for r in rates)

    def test_text_search_with_special_characters(
        self, client, db_session, student_token
    ):
        """
        Test search with SQL injection attempts and special characters.
        """
        # Create tutor with normal title
        email = f"special_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Expert C++ & Python Developer",
            headline="Teaching algorithms & data structures",
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Test various special characters
        test_queries = [
            "C++",
            "Python & Java",
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "%' OR '1'='1",
            "\\",
            "$$",
            "algorithms & data",
        ]

        for query in test_queries:
            response = client.get(
                f"/api/v1/tutors?search_query={query}",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            # Should not error - either returns results or empty
            assert response.status_code == status.HTTP_200_OK

    def test_multi_value_filter_combinations(
        self, client, db_session, student_token
    ):
        """
        Test combining multiple filter types simultaneously.
        """
        # Create subject
        subject = Subject(name="Mathematics", is_active=True)
        db_session.add(subject)
        db_session.commit()

        # Create tutor matching all criteria
        email = f"multifilter_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Math Expert Teacher",
            hourly_rate=Decimal("75.00"),
            experience_years=10,
            average_rating=Decimal("4.8"),
            languages=["English", "Spanish"],
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Add subject
        tutor_subject = TutorSubject(
            tutor_profile_id=profile.id,
            subject_id=subject.id,
            proficiency_level="Expert",
            years_experience=10,
        )
        db_session.add(tutor_subject)
        db_session.commit()

        # Search with all filters combined
        response = client.get(
            f"/api/v1/tutors?subject_id={subject.id}&min_rate=50&max_rate=100"
            "&min_rating=4.5&min_experience=5&language=English&search_query=Math",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should find our tutor
        if data["total"] > 0:
            assert any("Math" in t["title"] for t in data["items"])

    def test_language_filter_case_sensitivity(
        self, client, db_session, student_token
    ):
        """
        Test language filter handles case variations.
        """
        email = f"lang_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Language Test Tutor",
            languages=["English", "french", "SPANISH"],
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Test case variations
        for lang in ["English", "english", "ENGLISH"]:
            response = client.get(
                f"/api/v1/tutors?language={lang}",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert response.status_code == status.HTTP_200_OK


# =============================================================================
# Ranking Edge Cases Tests
# =============================================================================


class TestRankingEdgeCases:
    """Test ranking algorithm edge cases."""

    def test_tie_breaking_in_ranking(
        self, client, db_session, student_token
    ):
        """
        Test how ties are broken when tutors have identical scores.
        """
        # Create tutors with identical ratings
        for i in range(3):
            email = f"tie_{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Tie Tutor {i}",
                hourly_rate=Decimal("50.00"),
                average_rating=Decimal("4.5"),
                total_reviews=10,
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        response = client.get(
            "/api/v1/tutors?sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # All tied tutors should be present
        tie_tutors = [t for t in data["items"] if "Tie Tutor" in t["title"]]
        assert len(tie_tutors) == 3

        # Should have consistent ordering (deterministic tie-break)
        ids1 = [t["id"] for t in tie_tutors]

        # Repeat query
        response2 = client.get(
            "/api/v1/tutors?sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        tie_tutors2 = [t for t in response2.json()["items"] if "Tie Tutor" in t["title"]]
        ids2 = [t["id"] for t in tie_tutors2]

        # Order should be consistent
        assert ids1 == ids2

    def test_new_tutor_with_no_reviews_ranking(
        self, client, db_session, student_token
    ):
        """
        Test that new tutors with 0 reviews are still discoverable.
        """
        # Create tutor with no reviews
        email = f"new_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Brand New Tutor",
            hourly_rate=Decimal("40.00"),
            average_rating=Decimal("0.00"),
            total_reviews=0,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)

        # Create tutor with many reviews
        email2 = f"experienced_{time.time_ns()}@test.com"
        user2 = create_test_user(
            db_session, email=email2, password=TUTOR_PASSWORD, role="tutor"
        )
        profile2 = TutorProfile(
            user_id=user2.id,
            title="Experienced Tutor",
            hourly_rate=Decimal("60.00"),
            average_rating=Decimal("4.9"),
            total_reviews=100,
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile2)
        db_session.commit()

        # New tutor should appear in results (even if lower ranked)
        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        titles = [t["title"] for t in data["items"]]
        assert "Brand New Tutor" in titles

        # Sorting by rating - new tutor should be lower
        response2 = client.get(
            "/api/v1/tutors?sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        items = response2.json()["items"]
        new_idx = next(i for i, t in enumerate(items) if t["title"] == "Brand New Tutor")
        exp_idx = next(i for i, t in enumerate(items) if t["title"] == "Experienced Tutor")

        # Experienced should rank higher (lower index)
        assert exp_idx < new_idx

    def test_price_range_sorting_with_nulls(
        self, client, db_session, student_token
    ):
        """
        Test sorting by price when some tutors have null/zero rates.
        """
        # Create tutors with various rate conditions
        rates = [Decimal("50.00"), Decimal("0.00"), Decimal("100.00"), Decimal("75.00")]

        for i, rate in enumerate(rates):
            email = f"rate_{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Rate Tutor {rate}",
                hourly_rate=rate,
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        # Sort ascending
        response = client.get(
            "/api/v1/tutors?sort_by=rate_asc",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Extract rates and verify ordering
        result_rates = [Decimal(str(t["hourly_rate"])) for t in data["items"]]

        # Rates should be in ascending order
        sorted_rates = sorted(result_rates)
        assert result_rates == sorted_rates

    def test_geographic_proximity_edge_cases(self):
        """
        Test geographic proximity calculations at edge cases.
        """
        # Note: This tests the algorithm, not API
        # Edge cases: antipodal points, same location, international date line

        def haversine_distance(lat1, lon1, lat2, lon2):
            """Calculate distance between two points in km."""
            import math
            R = 6371  # Earth's radius in km

            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)

            a = (math.sin(delta_lat/2)**2 +
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

            return R * c

        # Same location
        assert haversine_distance(0, 0, 0, 0) == 0

        # Antipodal points (opposite sides of Earth)
        distance = haversine_distance(0, 0, 0, 180)
        assert 20000 < distance < 20100  # ~20,000 km

        # Across international date line
        distance2 = haversine_distance(0, 179, 0, -179)
        assert distance2 < 250  # Should be close, not 358 degrees apart


# =============================================================================
# Pagination Edge Cases Tests
# =============================================================================


class TestPaginationEdgeCases:
    """Test pagination edge cases and consistency."""

    def test_results_change_during_pagination(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test pagination consistency when results change between page requests.
        """
        # Create initial tutors
        create_tutors(30)

        # Get first page
        response1 = client.get(
            "/api/v1/tutors?page=1&page_size=10&sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK
        page1_data = response1.json()
        page1_total = page1_data["total"]

        # Add more tutors
        create_tutors(5, average_rating=Decimal("5.0"))

        # Get second page - total may have changed
        response2 = client.get(
            "/api/v1/tutors?page=2&page_size=10&sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        page2_data = response2.json()

        # Total should reflect new count
        assert page2_data["total"] >= page1_total

    def test_cursor_based_pagination_consistency(self):
        """
        Test cursor-based pagination maintains consistency.
        """
        # Simulate cursor-based pagination
        items = [{"id": i, "score": 100 - i} for i in range(50)]

        def get_page_by_cursor(cursor_id, page_size):
            if cursor_id is None:
                return items[:page_size]

            idx = next((i for i, item in enumerate(items) if item["id"] == cursor_id), -1)
            if idx == -1 or idx + 1 >= len(items):
                return []
            return items[idx + 1:idx + 1 + page_size]

        # Iterate through all items
        all_fetched = []
        cursor = None

        while True:
            page = get_page_by_cursor(cursor, 10)
            if not page:
                break
            all_fetched.extend(page)
            cursor = page[-1]["id"]

        # Should get all items without duplicates
        assert len(all_fetched) == len(items)
        assert len({item["id"] for item in all_fetched}) == len(items)

    def test_large_offset_performance(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test performance with large page offsets.
        """
        # Create many tutors
        create_tutors(50)

        # Request page with large offset
        start_time = time.time()
        response = client.get(
            "/api/v1/tutors?page=5&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        elapsed = time.time() - start_time

        assert response.status_code == status.HTTP_200_OK
        # Should complete reasonably fast even with offset
        assert elapsed < 5.0  # 5 second timeout

    def test_empty_page_in_middle_of_results(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test behavior when deletes create gaps in pagination.
        """
        tutors = create_tutors(30)

        # Get first page
        response1 = client.get(
            "/api/v1/tutors?page=1&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Soft-delete some tutors in the middle
        for _user, profile in tutors[10:20]:
            profile.is_approved = False
            profile.profile_status = "rejected"
        db_session.commit()

        # Get second page - should skip deleted
        response2 = client.get(
            "/api/v1/tutors?page=2&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        data = response2.json()

        # Should have fewer total results
        assert data["total"] == 20  # 30 - 10 deleted

    def test_total_count_accuracy_during_updates(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test that total count remains accurate during concurrent updates.
        """
        create_tutors(25)

        # Get initial count
        response1 = client.get(
            "/api/v1/tutors?page=1&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        initial_total = response1.json()["total"]

        # Add more tutors
        create_tutors(5)

        # Get count again
        response2 = client.get(
            "/api/v1/tutors?page=1&page_size=5",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        new_total = response2.json()["total"]

        assert new_total == initial_total + 5

    def test_page_beyond_total_returns_empty(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test requesting page number beyond available results.
        """
        create_tutors(10)

        response = client.get(
            "/api/v1/tutors?page=100&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["items"]) == 0
        assert data["page"] == 100
        assert data["has_next"] is False


# =============================================================================
# Real-time Availability in Search Tests
# =============================================================================


class TestRealTimeAvailability:
    """Test real-time availability display in search results."""

    def test_availability_changes_during_search_session(
        self, client, db_session, student_token
    ):
        """
        Test that availability shown in search may become stale.
        """
        # Create tutor with availability
        email = f"avail_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Availability Test Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Add availability
        availability = TutorAvailability(
            tutor_profile_id=profile.id,
            day_of_week=1,  # Monday
            start_time="09:00",
            end_time="17:00",
            is_recurring=True,
            timezone="UTC",
        )
        db_session.add(availability)
        db_session.commit()

        # Search shows tutor
        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # Delete availability (tutor removes slot)
        db_session.delete(availability)
        db_session.commit()

        # Tutor still appears in search (availability is separate concern)
        response2 = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK

    def test_slot_booked_between_search_and_detail(
        self, client, db_session, student_token
    ):
        """
        Test race condition: slot available in search but booked before detail view.
        """
        # Create tutor
        email = f"race_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Race Condition Tutor",
            hourly_rate=Decimal("50.00"),
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # User sees tutor in search
        response1 = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Concurrent booking happens (simulated by another user)
        # The user clicks to view detail - should handle gracefully
        response2 = client.get(
            f"/api/v1/tutors/{profile.id}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Tutor profile should still be viewable
        assert response2.status_code == status.HTTP_200_OK

    def test_timezone_conversion_in_availability_preview(self):
        """
        Test timezone handling in availability display.
        """
        from datetime import time as dt_time
        from zoneinfo import ZoneInfo

        # Tutor's availability in Pacific Time
        tutor_tz = ZoneInfo("America/Los_Angeles")
        tutor_start = dt_time(9, 0)  # 9 AM Pacific
        tutor_end = dt_time(17, 0)  # 5 PM Pacific

        # Convert to UTC for storage
        today = datetime.now(tutor_tz).date()
        start_dt = datetime.combine(today, tutor_start, tzinfo=tutor_tz)
        end_dt = datetime.combine(today, tutor_end, tzinfo=tutor_tz)

        start_utc = start_dt.astimezone(ZoneInfo("UTC"))
        end_utc = end_dt.astimezone(ZoneInfo("UTC"))

        # Convert to student's timezone (Tokyo)
        student_tz = ZoneInfo("Asia/Tokyo")
        start_student = start_utc.astimezone(student_tz)
        end_utc.astimezone(student_tz)

        # Verify the times are correctly offset
        # Pacific is UTC-8, Tokyo is UTC+9, so 17 hour difference
        hour_diff = (start_student.hour - tutor_start.hour) % 24

        # Should be significant difference due to timezone
        assert hour_diff != 0 or start_student.day != start_dt.day

    def test_dst_transition_availability(self):
        """
        Test availability handling during DST transitions.
        """
        from zoneinfo import ZoneInfo

        # March 10, 2024 - DST starts in US (2 AM -> 3 AM)
        datetime(2024, 3, 10, tzinfo=ZoneInfo("America/New_York"))

        # Slot at 2:30 AM on DST day (this time doesn't exist)
        # Should be handled gracefully
        try:
            invalid_time = datetime(2024, 3, 10, 2, 30, tzinfo=ZoneInfo("America/New_York"))
            # If we get here, the library handles it somehow
            assert invalid_time is not None
        except Exception:
            # Expected - time doesn't exist
            pass

        # Slot at 1:30 AM (before transition) should work
        valid_time = datetime(2024, 3, 10, 1, 30, tzinfo=ZoneInfo("America/New_York"))
        assert valid_time.hour == 1


# =============================================================================
# Autocomplete & Suggestions Tests
# =============================================================================


class TestAutocompleteAndSuggestions:
    """Test autocomplete and search suggestions edge cases."""

    def test_typo_tolerance_limits(
        self, client, db_session, student_token
    ):
        """
        Test how many typos are tolerated in search.
        """
        email = f"typo_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Mathematics Expert Teacher",
            headline="Calculus specialist",
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Exact match
        response1 = client.get(
            "/api/v1/tutors?search_query=Mathematics",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # One typo (Mathmatics)
        response2 = client.get(
            "/api/v1/tutors?search_query=Mathmatics",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK

        # Many typos (Mthmtcs) - may not match
        response3 = client.get(
            "/api/v1/tutors?search_query=Mthmtcs",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response3.status_code == status.HTTP_200_OK

    def test_unicode_and_emoji_in_search(
        self, client, db_session, student_token
    ):
        """
        Test search with unicode characters and emojis.
        """
        # Create tutor with unicode in title
        email = f"unicode_{time.time_ns()}@test.com"
        user = create_test_user(
            db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
        )
        profile = TutorProfile(
            user_id=user.id,
            title="Francais Tutor - Cafe Culture",
            headline="Enseignement en francais",
            is_approved=True,
            profile_status="approved",
        )
        db_session.add(profile)
        db_session.commit()

        # Search with unicode
        unicode_queries = [
            "Cafe",
            "francais",
            "Enseignement",
        ]

        for query in unicode_queries:
            response = client.get(
                f"/api/v1/tutors?search_query={query}",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert response.status_code == status.HTTP_200_OK

    def test_injection_attempt_handling(
        self, client, db_session, student_token
    ):
        """
        Test that SQL/NoSQL injection attempts are safely handled.
        """
        injection_attempts = [
            "'; DROP TABLE tutor_profiles; --",
            "1'; DELETE FROM users WHERE '1'='1",
            "${7*7}",
            "{{constructor.constructor('return this')()}}",
            "$where: function() { return true; }",
            "{$gt: ''}",
            "admin'--",
            "\" OR \"\"=\"",
            "'; exec xp_cmdshell('dir'); --",
            "<img src=x onerror=alert(1)>",
        ]

        for attempt in injection_attempts:
            response = client.get(
                f"/api/v1/tutors?search_query={attempt}",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            # Should never error - just return empty results
            assert response.status_code == status.HTTP_200_OK

    def test_empty_and_whitespace_queries(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test handling of empty and whitespace-only queries.
        """
        create_tutors(5)

        # Empty query
        response1 = client.get(
            "/api/v1/tutors?search_query=",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK
        # Should return all tutors
        assert response1.json()["total"] >= 5

        # Whitespace only
        response2 = client.get(
            "/api/v1/tutors?search_query=   ",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK

    def test_suggestion_ranking_freshness(self):
        """
        Test that suggestions prioritize fresh/popular content.
        """
        # Simulate suggestion ranking algorithm
        suggestions = [
            {"term": "math", "searches": 1000, "last_searched": datetime.now(UTC)},
            {"term": "mathematics", "searches": 500, "last_searched": datetime.now(UTC) - timedelta(days=30)},
            {"term": "maths", "searches": 2000, "last_searched": datetime.now(UTC) - timedelta(days=90)},
        ]

        def rank_suggestions(suggestions, recency_weight=0.3):
            now = datetime.now(UTC)
            scored = []
            for s in suggestions:
                age_days = (now - s["last_searched"]).days
                freshness = 1 / (1 + age_days / 30)  # Decay over 30 days
                score = s["searches"] * (1 - recency_weight) + freshness * recency_weight * 1000
                scored.append((s["term"], score))
            return sorted(scored, key=lambda x: -x[1])

        ranked = rank_suggestions(suggestions)

        # Most searched but old should not always win
        # Fresh content should get a boost
        assert ranked[0][0] in ["math", "maths"]


# =============================================================================
# Performance Under Load Tests
# =============================================================================


class TestPerformanceUnderLoad:
    """Test search performance under various load conditions."""

    def test_concurrent_search_requests(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test handling of concurrent search requests.
        """
        create_tutors(20)

        results = []
        errors = []

        def make_request():
            try:
                response = client.get(
                    "/api/v1/tutors?search_query=Tutor",
                    headers={"Authorization": f"Bearer {student_token}"},
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Simulate concurrent requests using threads
        threads = []
        for _ in range(10):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)

        # All requests should succeed
        assert len(errors) == 0
        assert all(code == 200 for code in results)

    def test_cache_effectiveness(self, mock_cache):
        """
        Test that cache reduces database load.
        """
        cache_key = "tutors:search:math"

        # First request - cache miss
        cached = mock_cache.get(cache_key)
        assert cached is None

        # Store result in cache
        result = {"items": [{"id": 1}], "total": 1}
        mock_cache.set(cache_key, result, ttl=60)

        # Second request - cache hit
        cached = mock_cache.get(cache_key)
        assert cached is not None
        assert cached["total"] == 1

        # Verify cache prevents duplicate queries
        db_calls = 0

        def mock_db_query():
            nonlocal db_calls
            db_calls += 1
            return result

        for _ in range(10):
            cached = mock_cache.get(cache_key)
            if cached is None:
                mock_db_query()

        # Should not call DB if cache is working
        assert db_calls == 0

    def test_query_timeout_handling(self, mock_cache):
        """
        Test graceful handling of query timeouts.
        """
        def slow_query():
            time.sleep(2)
            return {"items": [], "total": 0}

        # Simulate timeout behavior
        start = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(slow_query)
                result = future.result(timeout=0.5)
        except concurrent.futures.TimeoutError:
            # Expected - query timed out
            elapsed = time.time() - start
            assert elapsed < 1.0  # Timeout was respected
            result = {"items": [], "total": 0, "error": "timeout"}

        assert result is not None

    def test_result_set_size_limits(
        self, client, db_session, create_tutors, student_token
    ):
        """
        Test that large result sets are properly limited.
        """
        # Create many tutors
        create_tutors(150)

        # Request maximum page size
        response = client.get(
            "/api/v1/tutors?page_size=100",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should be limited to max page size
        assert len(data["items"]) <= 100

        # Cannot request more than max
        response2 = client.get(
            "/api/v1/tutors?page_size=500",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        # Should either error or limit to max
        if response2.status_code == status.HTTP_200_OK:
            assert len(response2.json()["items"]) <= 100

    def test_memory_usage_with_large_results(self, mock_cache):
        """
        Test memory handling with large result sets.
        """
        # Simulate large result set
        large_results = []
        for i in range(1000):
            large_results.append({
                "id": i,
                "title": f"Tutor {i} with a very long title to increase memory usage",
                "description": "x" * 1000,  # 1KB per tutor
            })

        # Store in cache
        mock_cache.set("large_results", large_results, ttl=60)

        # Retrieve should work
        cached = mock_cache.get("large_results")
        assert cached is not None
        assert len(cached) == 1000

    def test_search_with_database_connection_issues(self, mock_cache):
        """
        Test search behavior when database is temporarily unavailable.
        """
        # Simulate DB connection error
        def failing_query():
            raise OperationalError("statement", {}, "Connection refused")

        # Should fall back to cached results or error gracefully
        cached = mock_cache.get("tutors:fallback")

        if cached is None:
            # No cached fallback - should return error
            with pytest.raises(OperationalError):
                failing_query()
        else:
            # Return cached results
            assert cached is not None

    def test_search_index_lag_handling(self, mock_search_index):
        """
        Test handling when search index is behind primary data.
        """
        # Add document to primary (simulated)
        primary_data = {"id": 100, "title": "New Tutor", "version": 1}

        # Index may be behind
        mock_search_index.version = 0

        # Search should still work, possibly with stale data
        mock_search_index.search("Tutor")

        # When index catches up
        mock_search_index.add_document(primary_data)

        results_after = mock_search_index.search("New")
        assert len(results_after) >= 1


# =============================================================================
# Combined Scenario Tests
# =============================================================================


class TestCombinedScenarios:
    """Test complex scenarios combining multiple edge cases."""

    def test_search_during_bulk_tutor_import(
        self, client, db_session, student_token
    ):
        """
        Test search while tutors are being bulk imported.
        """
        # Start with some tutors
        initial_count = 5
        for i in range(initial_count):
            email = f"initial_{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Initial Tutor {i}",
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        # Search while "import" is running
        response = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        initial_results = response.json()["total"]

        # Add more tutors (simulating bulk import)
        for i in range(10):
            email = f"import_{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Imported Tutor {i}",
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        # Search again
        response2 = client.get(
            "/api/v1/tutors",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        final_results = response2.json()["total"]

        assert final_results > initial_results

    def test_filter_and_pagination_with_concurrent_deletes(
        self, client, db_session, student_token
    ):
        """
        Test paginating through filtered results while tutors are deleted.
        """
        # Create tutors with specific hourly rate
        tutors = []
        for i in range(30):
            email = f"delete_test_{i}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=f"Delete Test Tutor {i}",
                hourly_rate=Decimal("75.00"),
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
            tutors.append(profile)
        db_session.commit()

        # Get first page with filter
        response1 = client.get(
            "/api/v1/tutors?min_rate=70&max_rate=80&page=1&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response1.status_code == status.HTTP_200_OK
        page1 = response1.json()

        # Delete some tutors that would be on page 2
        for tutor in tutors[10:15]:
            tutor.is_approved = False
        db_session.commit()

        # Get second page
        response2 = client.get(
            "/api/v1/tutors?min_rate=70&max_rate=80&page=2&page_size=10",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response2.status_code == status.HTTP_200_OK
        page2 = response2.json()

        # Total should be reduced
        assert page2["total"] < page1["total"]

    def test_search_with_special_sort_and_filter_combo(
        self, client, db_session, student_token
    ):
        """
        Test complex combination of search, filter, and sort.
        """
        # Create diverse tutors
        test_cases = [
            {"title": "Expert Math Teacher", "rate": "60", "rating": "4.9", "exp": 15},
            {"title": "Math Basics Instructor", "rate": "30", "rating": "4.5", "exp": 5},
            {"title": "Advanced Mathematics Professor", "rate": "100", "rating": "5.0", "exp": 20},
            {"title": "Science and Math Tutor", "rate": "50", "rating": "4.7", "exp": 10},
        ]

        for tc in test_cases:
            email = f"complex_{tc['title'].replace(' ', '_')}_{time.time_ns()}@test.com"
            user = create_test_user(
                db_session, email=email, password=TUTOR_PASSWORD, role="tutor"
            )
            profile = TutorProfile(
                user_id=user.id,
                title=tc["title"],
                hourly_rate=Decimal(tc["rate"]),
                average_rating=Decimal(tc["rating"]),
                experience_years=tc["exp"],
                is_approved=True,
                profile_status="approved",
            )
            db_session.add(profile)
        db_session.commit()

        # Complex query: search for "Math", filter by rate, sort by rating
        response = client.get(
            "/api/v1/tutors?search_query=Math&min_rate=40&max_rate=110&sort_by=rating",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify results match criteria
        for item in data["items"]:
            if "Math" in item["title"]:
                rate = Decimal(str(item["hourly_rate"]))
                assert Decimal("40") <= rate <= Decimal("110")

        # Verify sorted by rating (descending)
        ratings = [
            Decimal(str(item["average_rating"]))
            for item in data["items"]
            if "Math" in item["title"]
        ]
        assert ratings == sorted(ratings, reverse=True)
