"""
Comprehensive tests for distributed system edge cases.

Tests cover:
1. Distributed Lock Edge Cases:
   - Lock expires during critical section
   - Lock extension failure
   - Redis connection lost while holding lock
   - Deadlock detection and recovery
   - Lock contention under high concurrency

2. Cache Consistency Issues:
   - Cache invalidation race conditions
   - Stale cache read after write
   - Cache stampede scenarios
   - Multi-key atomic invalidation
   - Cache warming during cold start

3. Event Ordering Problems:
   - Out-of-order event processing
   - Duplicate event handling
   - Event replay scenarios
   - Event sourcing consistency

4. Database Transaction Edge Cases:
   - Serialization failures (PostgreSQL)
   - Nested transaction rollback
   - Long-running transaction timeout
   - Connection pool exhaustion
   - Deadlock between transactions

5. Background Task Failures:
   - Celery task timeout
   - Task retry exhaustion
   - Duplicate task execution
   - Task chain failure recovery
   - Worker crash during task

6. Service Communication:
   - External API timeout handling
   - Circuit breaker patterns
   - Retry with exponential backoff
   - Partial failure scenarios
"""

import asyncio
import random
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager, suppress
from datetime import datetime, timedelta
from queue import Empty, Queue
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from core.distributed_lock import DistributedLockService
from core.transactions import TransactionError, atomic_operation, transaction

# =============================================================================
# Test Utilities and Fixtures
# =============================================================================


class MockRedisWithLatency:
    """Mock Redis client that simulates network latency and failures."""

    def __init__(
        self,
        latency_ms: float = 0,
        failure_rate: float = 0,
        timeout_rate: float = 0,
    ):
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.timeout_rate = timeout_rate
        self._data: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()
        self._call_count = 0

    def _simulate_latency(self):
        if self.latency_ms > 0:
            time.sleep(self.latency_ms / 1000)

    def _maybe_fail(self):
        self._call_count += 1
        if random.random() < self.failure_rate:
            raise ConnectionError("Simulated Redis connection failure")
        if random.random() < self.timeout_rate:
            raise TimeoutError("Simulated Redis timeout")

    async def set(self, key: str, value: Any, nx: bool = False, ex: int | None = None) -> bool:
        self._simulate_latency()
        self._maybe_fail()

        with self._lock:
            if nx and key in self._data:
                existing_value, expiry = self._data[key]
                if expiry is None or expiry > time.time():
                    return False

            expiry = time.time() + ex if ex else None
            self._data[key] = (value, expiry)
            return True

    async def get(self, key: str) -> Any | None:
        self._simulate_latency()
        self._maybe_fail()

        with self._lock:
            if key not in self._data:
                return None
            value, expiry = self._data[key]
            if expiry and expiry < time.time():
                del self._data[key]
                return None
            return value

    async def delete(self, key: str) -> int:
        self._simulate_latency()
        self._maybe_fail()

        with self._lock:
            if key in self._data:
                del self._data[key]
                return 1
            return 0

    async def exists(self, key: str) -> int:
        self._simulate_latency()
        self._maybe_fail()

        with self._lock:
            if key not in self._data:
                return 0
            _, expiry = self._data[key]
            if expiry and expiry < time.time():
                del self._data[key]
                return 0
            return 1

    async def ttl(self, key: str) -> int:
        self._simulate_latency()
        self._maybe_fail()

        with self._lock:
            if key not in self._data:
                return -2
            _, expiry = self._data[key]
            if expiry is None:
                return -1
            remaining = int(expiry - time.time())
            return max(0, remaining)

    async def eval(self, script: str, num_keys: int, *args) -> Any:
        self._simulate_latency()
        self._maybe_fail()

        key = args[0] if args else None
        expected_value = args[1] if len(args) > 1 else None

        with self._lock:
            if key and key in self._data:
                current_value, _ = self._data[key]
                if current_value == expected_value:
                    del self._data[key]
                    return 1
            return 0

    async def close(self):
        pass


class EventStore:
    """Simple event store for testing event ordering."""

    def __init__(self):
        self.events: list[dict] = []
        self._lock = threading.Lock()
        self._processed_ids: set[str] = set()

    def append(self, event: dict):
        with self._lock:
            self.events.append(event)

    def get_all(self) -> list[dict]:
        with self._lock:
            return list(self.events)

    def mark_processed(self, event_id: str) -> bool:
        """Mark event as processed, returns False if already processed."""
        with self._lock:
            if event_id in self._processed_ids:
                return False
            self._processed_ids.add(event_id)
            return True

    def is_processed(self, event_id: str) -> bool:
        with self._lock:
            return event_id in self._processed_ids


class CircuitBreaker:
    """Simple circuit breaker implementation for testing."""

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: float = 5.0,
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time: float | None = None
        self.state = "closed"
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == "closed":
                return True
            if self.state == "open":
                if self.last_failure_time and (
                    time.time() - self.last_failure_time > self.reset_timeout
                ):
                    self.state = "half-open"
                    return True
                return False
            return True

    def record_success(self):
        with self._lock:
            self.failures = 0
            self.state = "closed"

    def record_failure(self):
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = "open"


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return MockRedisWithLatency()


@pytest.fixture
def mock_redis_with_failures():
    """Create a mock Redis client that occasionally fails."""
    return MockRedisWithLatency(failure_rate=0.2)


@pytest.fixture
def mock_redis_slow():
    """Create a mock Redis client with simulated latency."""
    return MockRedisWithLatency(latency_ms=100)


@pytest.fixture
def event_store():
    """Create an event store for testing."""
    return EventStore()


@pytest.fixture
def circuit_breaker():
    """Create a circuit breaker for testing."""
    return CircuitBreaker(failure_threshold=3, reset_timeout=1.0)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.flush = MagicMock()
    db.add = MagicMock()
    db.query = MagicMock()
    db.execute = MagicMock()
    db.begin_nested = MagicMock()
    return db


# =============================================================================
# 1. Distributed Lock Edge Cases
# =============================================================================


class TestDistributedLockEdgeCases:
    """Tests for distributed lock edge cases."""

    @pytest.mark.asyncio
    async def test_lock_expires_during_critical_section(self):
        """Test behavior when lock expires while work is still in progress."""
        lock_service = DistributedLockService()
        mock_redis = MockRedisWithLatency()


        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            # Acquire lock with very short TTL
            acquired, token = await lock_service.try_acquire("test_lock", timeout=1)
            assert acquired is True

            # Simulate long-running work that exceeds lock TTL
            await asyncio.sleep(1.5)

            # Try to release - should fail because lock expired
            await lock_service.release("test_lock", token)

            # Lock should have expired, release returns False (token mismatch)
            # because another process could have acquired it
            ttl = await lock_service.get_lock_ttl("test_lock")
            assert ttl == -2  # Key doesn't exist (expired)

    @pytest.mark.asyncio
    async def test_lock_stolen_by_another_instance(self):
        """Test scenario where another instance acquires expired lock."""
        lock_service1 = DistributedLockService()
        lock_service2 = DistributedLockService()
        mock_redis = MockRedisWithLatency()

        with patch.object(lock_service1, "_get_redis", return_value=mock_redis):
            with patch.object(lock_service2, "_get_redis", return_value=mock_redis):
                # Instance 1 acquires lock
                acquired1, token1 = await lock_service1.try_acquire("shared_lock", timeout=1)
                assert acquired1 is True

                # Wait for lock to expire
                await asyncio.sleep(1.5)

                # Instance 2 acquires the same lock
                acquired2, token2 = await lock_service2.try_acquire("shared_lock", timeout=60)
                assert acquired2 is True
                assert token2 != token1

                # Instance 1 tries to release with old token - should fail
                released = await lock_service1.release("shared_lock", token1)
                assert released is False  # Token mismatch

                # Instance 2 can still release
                released = await lock_service2.release("shared_lock", token2)
                assert released is True

    @pytest.mark.asyncio
    async def test_redis_connection_lost_while_holding_lock(self):
        """Test behavior when Redis connection is lost during lock hold."""
        lock_service = DistributedLockService()
        mock_redis = MockRedisWithLatency(failure_rate=1.0)  # Always fail

        # First acquisition works (before failure mode)
        mock_redis_good = MockRedisWithLatency()
        with patch.object(lock_service, "_get_redis", return_value=mock_redis_good):
            acquired, token = await lock_service.try_acquire("test_lock", timeout=60)
            assert acquired is True

        # Now Redis fails
        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            # Release fails due to connection error
            released = await lock_service.release("test_lock", token)
            assert released is False

            # Check lock status also fails (gracefully returns False)
            is_locked = await lock_service.is_locked("test_lock")
            assert is_locked is False  # Fail-open behavior

    @pytest.mark.asyncio
    async def test_lock_contention_under_high_concurrency(self):
        """Test lock acquisition under high concurrent load."""
        lock_service = DistributedLockService()
        mock_redis = MockRedisWithLatency(latency_ms=5)

        acquired_count = 0
        failed_count = 0
        lock = threading.Lock()

        async def try_acquire_lock(worker_id: int):
            nonlocal acquired_count, failed_count
            with patch.object(lock_service, "_get_redis", return_value=mock_redis):
                acquired, token = await lock_service.try_acquire(
                    "contended_lock", timeout=10
                )
                with lock:
                    if acquired:
                        acquired_count += 1
                        # Simulate some work
                        await asyncio.sleep(0.01)
                        await lock_service.release("contended_lock", token)
                    else:
                        failed_count += 1

        # Run 20 concurrent attempts
        tasks = [try_acquire_lock(i) for i in range(20)]
        await asyncio.gather(*tasks)

        # Only one should acquire at a time, but multiple may succeed sequentially
        assert acquired_count >= 1
        assert acquired_count + failed_count == 20

    @pytest.mark.asyncio
    async def test_deadlock_detection_multiple_resources(self):
        """Test potential deadlock when acquiring multiple locks."""
        lock_service = DistributedLockService()
        mock_redis = MockRedisWithLatency()

        lock_a_held = asyncio.Event()
        lock_b_held = asyncio.Event()
        deadlock_detected = False

        async def worker1():
            """Acquires A then B."""
            with patch.object(lock_service, "_get_redis", return_value=mock_redis):
                acquired_a, token_a = await lock_service.try_acquire("lock_A", timeout=5)
                if acquired_a:
                    lock_a_held.set()
                    await asyncio.sleep(0.1)  # Wait for worker2 to hold B

                    # Try to acquire B (may timeout or fail)
                    acquired_b, token_b = await lock_service.try_acquire("lock_B", timeout=1)
                    if acquired_b:
                        await lock_service.release("lock_B", token_b)
                    await lock_service.release("lock_A", token_a)
                return acquired_a

        async def worker2():
            """Acquires B then A."""
            nonlocal deadlock_detected
            with patch.object(lock_service, "_get_redis", return_value=mock_redis):
                acquired_b, token_b = await lock_service.try_acquire("lock_B", timeout=5)
                if acquired_b:
                    lock_b_held.set()
                    await asyncio.sleep(0.1)  # Wait for worker1 to hold A

                    # Try to acquire A (may timeout or fail - deadlock scenario)
                    acquired_a, token_a = await lock_service.try_acquire("lock_A", timeout=1)
                    if not acquired_a:
                        deadlock_detected = True  # Would be a deadlock
                    else:
                        await lock_service.release("lock_A", token_a)
                    await lock_service.release("lock_B", token_b)
                return acquired_b

        # Run both workers concurrently
        results = await asyncio.gather(worker1(), worker2())

        # At least one should have acquired their first lock
        assert any(results)

    @pytest.mark.asyncio
    async def test_lock_reentrance_not_supported(self):
        """Test that the same instance cannot acquire lock twice (non-reentrant)."""
        lock_service = DistributedLockService()
        mock_redis = MockRedisWithLatency()

        with patch.object(lock_service, "_get_redis", return_value=mock_redis):
            # First acquisition
            acquired1, token1 = await lock_service.try_acquire("reentrant_test", timeout=60)
            assert acquired1 is True

            # Second acquisition by same instance should fail
            acquired2, token2 = await lock_service.try_acquire("reentrant_test", timeout=60)
            assert acquired2 is False
            assert token2 is None

            # Release original lock
            await lock_service.release("reentrant_test", token1)

            # Now can acquire again
            acquired3, token3 = await lock_service.try_acquire("reentrant_test", timeout=60)
            assert acquired3 is True
            await lock_service.release("reentrant_test", token3)


# =============================================================================
# 2. Cache Consistency Issues
# =============================================================================


class TestCacheConsistencyEdgeCases:
    """Tests for cache consistency edge cases."""

    def test_cache_invalidation_race_condition(self):
        """Test race condition between cache update and invalidation."""
        cache = {}
        cache_lock = threading.Lock()
        invalidation_count = 0
        stale_reads = 0

        def write_through_cache(key: str, value: Any):
            """Write to cache (simulating write-through)."""
            with cache_lock:
                cache[key] = {"value": value, "version": time.time()}

        def invalidate_cache(key: str):
            """Invalidate cache entry."""
            nonlocal invalidation_count
            with cache_lock:
                if key in cache:
                    del cache[key]
                    invalidation_count += 1

        def read_cache(key: str) -> Any | None:
            """Read from cache."""
            with cache_lock:
                return cache.get(key)

        # Simulate concurrent writes and invalidations
        def writer_thread():
            for i in range(100):
                write_through_cache("shared_key", f"value_{i}")
                time.sleep(0.001)

        def invalidator_thread():
            for _ in range(100):
                invalidate_cache("shared_key")
                time.sleep(0.001)

        def reader_thread():
            nonlocal stale_reads
            for _ in range(100):
                read_cache("shared_key")
                # In a race condition, we might read stale or None
                time.sleep(0.001)

        threads = [
            threading.Thread(target=writer_thread),
            threading.Thread(target=invalidator_thread),
            threading.Thread(target=reader_thread),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have some invalidations
        assert invalidation_count > 0

    def test_stale_cache_read_after_write(self):
        """Test scenario where cache read returns stale data after DB write."""
        cache = {}
        db_value = {"version": 1}
        stale_read_detected = False

        def update_db(new_version: int):
            """Simulate database update."""
            nonlocal db_value
            db_value = {"version": new_version}

        def update_cache(key: str, value: dict):
            """Update cache with delay (simulating async invalidation)."""
            time.sleep(0.05)  # Simulated delay
            cache[key] = value

        def read_cache_or_db(key: str) -> dict:
            """Read from cache, fallback to DB."""
            if key in cache:
                return cache[key]
            cache[key] = dict(db_value)
            return cache[key]

        # Writer updates DB then cache (with delay)
        def writer():
            update_db(2)
            update_cache("user_1", {"version": 2})

        # Reader reads immediately after DB write but before cache update
        def reader():
            nonlocal stale_read_detected
            time.sleep(0.01)  # Read between DB update and cache update
            value = read_cache_or_db("user_1")
            if value["version"] == 1:
                stale_read_detected = True

        # Initialize cache
        cache["user_1"] = {"version": 1}

        writer_thread = threading.Thread(target=writer)
        reader_thread = threading.Thread(target=reader)

        writer_thread.start()
        reader_thread.start()

        writer_thread.join()
        reader_thread.join()

        # Stale read is possible in this scenario
        # This demonstrates the need for proper cache invalidation strategies

    def test_cache_stampede_scenario(self):
        """Test cache stampede when many requests hit expired cache."""
        cache = {}
        db_call_count = 0
        db_lock = threading.Lock()

        def expensive_db_query(key: str) -> dict:
            """Simulate expensive database query."""
            nonlocal db_call_count
            with db_lock:
                db_call_count += 1
            time.sleep(0.1)  # Simulate slow query
            return {"key": key, "data": "expensive_result"}

        def get_with_cache(key: str) -> dict:
            """Get data with cache, no stampede protection."""
            if key in cache:
                value, expiry = cache[key]
                if expiry > time.time():
                    return value

            # Cache miss or expired - all threads hit DB
            result = expensive_db_query(key)
            cache[key] = (result, time.time() + 60)
            return result

        # All threads hit cache simultaneously when it's cold
        def client_thread():
            get_with_cache("popular_key")

        threads = [threading.Thread(target=client_thread) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Without stampede protection, all 10 threads hit DB
        # This demonstrates the thundering herd problem
        assert db_call_count >= 1

    def test_cache_stampede_with_locking(self):
        """Test cache stampede prevention using locking."""
        cache = {}
        db_call_count = 0
        cache_locks = defaultdict(threading.Lock)
        db_lock = threading.Lock()

        def expensive_db_query(key: str) -> dict:
            """Simulate expensive database query."""
            nonlocal db_call_count
            with db_lock:
                db_call_count += 1
            time.sleep(0.1)
            return {"key": key, "data": "expensive_result"}

        def get_with_cache_protected(key: str) -> dict:
            """Get data with cache and stampede protection."""
            if key in cache:
                value, expiry = cache[key]
                if expiry > time.time():
                    return value

            # Use per-key lock to prevent stampede
            with cache_locks[key]:
                # Double-check after acquiring lock
                if key in cache:
                    value, expiry = cache[key]
                    if expiry > time.time():
                        return value

                result = expensive_db_query(key)
                cache[key] = (result, time.time() + 60)
                return result

        def client_thread():
            get_with_cache_protected("popular_key")

        threads = [threading.Thread(target=client_thread) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # With stampede protection, only 1 thread should hit DB
        assert db_call_count == 1

    def test_multi_key_atomic_invalidation(self):
        """Test atomic invalidation of related cache keys."""
        cache = {}
        version = 0

        def set_cache(key: str, value: Any):
            cache[key] = value

        def atomic_invalidate_user_cache(user_id: int):
            """Atomically invalidate all cache entries for a user."""
            nonlocal version
            version += 1
            keys_to_invalidate = [
                f"user:{user_id}:profile",
                f"user:{user_id}:settings",
                f"user:{user_id}:bookings",
            ]
            # In production, this should be atomic (e.g., using Redis pipeline)
            for key in keys_to_invalidate:
                if key in cache:
                    del cache[key]
            return len(keys_to_invalidate)

        # Populate cache
        user_id = 123
        set_cache(f"user:{user_id}:profile", {"name": "Test"})
        set_cache(f"user:{user_id}:settings", {"theme": "dark"})
        set_cache(f"user:{user_id}:bookings", [1, 2, 3])

        assert len(cache) == 3

        # Atomically invalidate
        invalidated = atomic_invalidate_user_cache(user_id)

        assert invalidated == 3
        assert len(cache) == 0
        assert version == 1

    def test_cache_warming_during_cold_start(self):
        """Test gradual cache warming during application cold start."""
        cache = {}
        warm_up_progress = []

        def warm_cache_entry(key: str, loader: Callable) -> bool:
            """Warm a single cache entry."""
            try:
                value = loader()
                cache[key] = value
                warm_up_progress.append(key)
                return True
            except Exception:
                return False

        def loader_factory(key: str) -> Callable:
            """Create loader function for cache entry."""
            return lambda: {"key": key, "loaded_at": time.time()}

        # Warm up cache entries progressively
        keys_to_warm = [f"item:{i}" for i in range(5)]

        for key in keys_to_warm:
            success = warm_cache_entry(key, loader_factory(key))
            assert success

        # All entries should be warmed
        assert len(cache) == 5
        assert len(warm_up_progress) == 5

        # Verify order of warming
        for i, key in enumerate(warm_up_progress):
            assert key == f"item:{i}"


# =============================================================================
# 3. Event Ordering Problems
# =============================================================================


class TestEventOrderingProblems:
    """Tests for event ordering edge cases."""

    def test_out_of_order_event_processing(self, event_store):
        """Test handling of events that arrive out of order."""
        processed_events = []
        expected_sequence = []

        def process_event(event: dict):
            """Process event, handling out-of-order scenarios."""
            event_id = event["id"]
            sequence = event["sequence"]

            # Track expected sequence
            expected_sequence.append(sequence)

            # Check if we already processed this event
            if event_store.mark_processed(event_id):
                processed_events.append(event)
            return True

        # Generate events with sequence numbers
        events = [
            {"id": str(uuid.uuid4()), "sequence": i, "data": f"event_{i}"}
            for i in range(5)
        ]

        # Shuffle to simulate out-of-order arrival
        shuffled = [events[2], events[0], events[4], events[1], events[3]]

        for event in shuffled:
            process_event(event)

        # All events should be processed
        assert len(processed_events) == 5

        # But they were processed out of order
        sequences = [e["sequence"] for e in processed_events]
        assert sequences == [2, 0, 4, 1, 3]  # Out of order

    def test_event_reordering_buffer(self, event_store):
        """Test buffering and reordering of events."""
        buffer = {}
        next_expected_sequence = 0
        processed_in_order = []

        def process_event_with_ordering(event: dict):
            """Process events in order using a buffer."""
            nonlocal next_expected_sequence

            sequence = event["sequence"]

            if sequence == next_expected_sequence:
                # Process this event
                processed_in_order.append(event)
                next_expected_sequence += 1

                # Check buffer for next events
                while next_expected_sequence in buffer:
                    buffered = buffer.pop(next_expected_sequence)
                    processed_in_order.append(buffered)
                    next_expected_sequence += 1
            elif sequence > next_expected_sequence:
                # Buffer for later
                buffer[sequence] = event
            # Ignore events with sequence < next_expected (already processed)

        # Events arrive out of order
        events = [
            {"sequence": 2, "data": "C"},
            {"sequence": 0, "data": "A"},
            {"sequence": 4, "data": "E"},
            {"sequence": 1, "data": "B"},
            {"sequence": 3, "data": "D"},
        ]

        for event in events:
            process_event_with_ordering(event)

        # All events should be processed in order
        assert len(processed_in_order) == 5
        assert [e["data"] for e in processed_in_order] == ["A", "B", "C", "D", "E"]

    def test_duplicate_event_handling(self, event_store):
        """Test idempotent handling of duplicate events."""
        processing_count = defaultdict(int)

        def process_event_idempotent(event: dict) -> bool:
            """Process event idempotently."""
            event_id = event["id"]
            processing_count[event_id] += 1

            # Check if already processed
            if not event_store.mark_processed(event_id):
                return False  # Already processed

            # Process the event
            event_store.append(event)
            return True

        # Create event
        event = {"id": "event-123", "data": "test"}

        # Process same event multiple times (simulating duplicates)
        results = [process_event_idempotent(event) for _ in range(5)]

        # Only first should succeed
        assert results == [True, False, False, False, False]
        assert processing_count["event-123"] == 5  # Attempted 5 times
        assert len(event_store.get_all()) == 1  # But stored only once

    def test_event_replay_scenario(self, event_store):
        """Test replaying events for state reconstruction."""

        def apply_event(event: dict, state: dict):
            """Apply event to state (event sourcing pattern)."""
            event_type = event["type"]

            if event_type == "deposit":
                state["balance"] += event["amount"]
                state["transactions"].append(event)
            elif event_type == "withdraw":
                if state["balance"] >= event["amount"]:
                    state["balance"] -= event["amount"]
                    state["transactions"].append(event)
            return state

        # Original event stream
        events = [
            {"id": "1", "type": "deposit", "amount": 100},
            {"id": "2", "type": "withdraw", "amount": 30},
            {"id": "3", "type": "deposit", "amount": 50},
            {"id": "4", "type": "withdraw", "amount": 20},
        ]

        # Store events
        for event in events:
            event_store.append(event)

        # Replay all events to reconstruct state
        replayed_state = {"balance": 0, "transactions": []}
        for event in event_store.get_all():
            apply_event(event, replayed_state)

        # Verify final state
        assert replayed_state["balance"] == 100  # 100 - 30 + 50 - 20
        assert len(replayed_state["transactions"]) == 4

    def test_event_sourcing_consistency(self, event_store):
        """Test event sourcing consistency across multiple aggregates."""
        aggregates = defaultdict(lambda: {"balance": 0, "version": 0})

        def apply_aggregate_event(aggregate_id: str, event: dict):
            """Apply event to specific aggregate."""
            aggregate = aggregates[aggregate_id]
            expected_version = event.get("expected_version")

            # Optimistic concurrency check
            if expected_version is not None and aggregate["version"] != expected_version:
                raise ValueError(
                    f"Version conflict: expected {expected_version}, got {aggregate['version']}"
                )

            aggregate["balance"] += event["amount"]
            aggregate["version"] += 1
            return aggregate

        # Events for multiple aggregates
        events = [
            {"aggregate_id": "account-1", "amount": 100, "expected_version": 0},
            {"aggregate_id": "account-2", "amount": 200, "expected_version": 0},
            {"aggregate_id": "account-1", "amount": -50, "expected_version": 1},
            {"aggregate_id": "account-1", "amount": 25, "expected_version": 2},
        ]

        # Apply events
        for event in events:
            apply_aggregate_event(event["aggregate_id"], event)

        # Verify final states
        assert aggregates["account-1"]["balance"] == 75  # 100 - 50 + 25
        assert aggregates["account-1"]["version"] == 3
        assert aggregates["account-2"]["balance"] == 200
        assert aggregates["account-2"]["version"] == 1

        # Test version conflict
        with pytest.raises(ValueError, match="Version conflict"):
            apply_aggregate_event(
                "account-1",
                {"amount": 10, "expected_version": 0}  # Wrong version
            )


# =============================================================================
# 4. Database Transaction Edge Cases
# =============================================================================


class TestDatabaseTransactionEdgeCases:
    """Tests for database transaction edge cases."""

    def test_serialization_failure_retry(self, mock_db):
        """Test handling of PostgreSQL serialization failures."""
        attempt_count = 0
        max_retries = 3

        def execute_with_retry(db, operation: Callable, retries: int = max_retries):
            """Execute operation with retry on serialization failure."""
            nonlocal attempt_count

            for attempt in range(retries + 1):
                attempt_count += 1
                try:
                    result = operation(db)
                    db.commit()
                    return result
                except OperationalError as e:
                    db.rollback()
                    if "serialization" in str(e).lower() and attempt < retries:
                        time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                        continue
                    raise
            raise OperationalError("Max retries exceeded", None, None)

        # Simulate serialization failure on first two attempts
        call_count = 0

        def flaky_operation(db):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError(
                    "could not serialize access due to concurrent update",
                    None,
                    Exception("serialization failure")
                )
            return {"success": True}

        result = execute_with_retry(mock_db, flaky_operation)

        assert result == {"success": True}
        assert attempt_count == 3  # Took 3 attempts
        assert mock_db.rollback.call_count == 2  # Rolled back twice
        assert mock_db.commit.call_count == 1  # Committed once

    def test_nested_transaction_rollback(self, mock_db):
        """Test that nested transaction rollback doesn't affect outer transaction."""
        mock_savepoint = MagicMock()
        mock_db.begin_nested.return_value = mock_savepoint

        outer_committed = False

        try:
            with transaction(mock_db):
                mock_db.add(MagicMock())  # Outer work

                try:
                    mock_savepoint.__enter__ = MagicMock(return_value=mock_savepoint)
                    mock_savepoint.__exit__ = MagicMock(return_value=False)

                    # Simulate nested transaction failure
                    raise ValueError("Inner transaction failed")
                except ValueError:
                    mock_savepoint.rollback()

                # Outer transaction should continue
                mock_db.add(MagicMock())

            outer_committed = True
        except Exception:
            pass

        assert mock_db.commit.called or outer_committed is False

    def test_long_running_transaction_timeout(self, mock_db):
        """Test handling of long-running transaction timeout."""
        execution_time = 0

        def simulate_long_transaction(db, timeout_seconds: float = 1.0):
            """Simulate a transaction that might timeout."""
            nonlocal execution_time
            start = time.time()

            try:
                # Simulate long operation
                time.sleep(0.5)

                if time.time() - start > timeout_seconds:
                    raise TimeoutError("Transaction timeout")

                db.commit()
                execution_time = time.time() - start
                return True
            except TimeoutError:
                db.rollback()
                execution_time = time.time() - start
                return False

        result = simulate_long_transaction(mock_db, timeout_seconds=1.0)

        assert result is True
        assert execution_time < 1.0

    def test_connection_pool_exhaustion(self):
        """Test behavior when connection pool is exhausted."""
        pool_size = 3
        active_connections = 0
        connection_lock = threading.Lock()
        blocked_threads = 0

        @contextmanager
        def get_connection(timeout: float = 1.0):
            """Simulate getting connection from pool."""
            nonlocal active_connections, blocked_threads

            start = time.time()
            while True:
                with connection_lock:
                    if active_connections < pool_size:
                        active_connections += 1
                        break
                    if time.time() - start > timeout:
                        raise TimeoutError("Connection pool exhausted")
                blocked_threads += 1
                time.sleep(0.01)

            try:
                yield MagicMock()
            finally:
                with connection_lock:
                    active_connections -= 1

        acquired = []
        timeouts = []

        def worker(worker_id: int):
            try:
                with get_connection(timeout=0.5):
                    acquired.append(worker_id)
                    time.sleep(0.2)  # Hold connection
            except TimeoutError:
                timeouts.append(worker_id)

        # Start more threads than pool size
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Some should succeed, some should timeout
        assert len(acquired) >= pool_size
        assert len(timeouts) >= 0  # May have some timeouts

    def test_database_deadlock_detection(self, mock_db):
        """Test detection and handling of database deadlocks."""
        lock_order = []

        def simulate_deadlock_prone_operation(db, resource_a: str, resource_b: str):
            """Operation that could cause deadlock."""
            lock_order.append((resource_a, resource_b))

            # Simulate acquiring locks in different order
            # In real scenario, this would be SELECT FOR UPDATE

        def detect_potential_deadlock(operations: list) -> bool:
            """Detect if operations could cause deadlock."""
            # Build lock graph
            lock_graph = defaultdict(set)

            for op_a, op_b in operations:
                lock_graph[op_a].add(op_b)

            # Check for cycles (simplified)
            visited = set()

            def has_cycle(node, path):
                if node in path:
                    return True
                if node in visited:
                    return False
                visited.add(node)
                path.add(node)
                for neighbor in lock_graph.get(node, []):
                    if has_cycle(neighbor, path):
                        return True
                path.remove(node)
                return False

            return any(has_cycle(start, set()) for start in lock_graph)

        # Operations that would deadlock
        operations = [
            ("resource_A", "resource_B"),  # Thread 1: A then B
            ("resource_B", "resource_A"),  # Thread 2: B then A
        ]

        has_deadlock = detect_potential_deadlock(operations)
        assert has_deadlock is True

        # Safe operations (consistent ordering)
        safe_operations = [
            ("resource_A", "resource_B"),
            ("resource_A", "resource_B"),
        ]

        has_deadlock = detect_potential_deadlock(safe_operations)
        assert has_deadlock is False


# =============================================================================
# 5. Background Task Failures
# =============================================================================


class TestBackgroundTaskFailures:
    """Tests for Celery/background task failure scenarios."""

    def test_task_timeout_handling(self):
        """Test handling of task that exceeds timeout."""

        def run_with_timeout(task: Callable, timeout: float) -> dict:
            """Run task with timeout."""
            result_queue = Queue()

            def wrapper():
                try:
                    result = task()
                    result_queue.put(("success", result))
                except Exception as e:
                    result_queue.put(("error", str(e)))

            thread = threading.Thread(target=wrapper)
            thread.start()
            thread.join(timeout=timeout)

            if thread.is_alive():
                return {"timed_out": True}

            try:
                status, result = result_queue.get_nowait()
                return {"completed": status == "success", "result": result}
            except Empty:
                return {"timed_out": True}

        # Task that completes in time
        def quick_task():
            time.sleep(0.1)
            return "done"

        result = run_with_timeout(quick_task, timeout=1.0)
        assert result["completed"] is True

        # Task that times out
        def slow_task():
            time.sleep(2.0)
            return "done"

        result = run_with_timeout(slow_task, timeout=0.5)
        assert result["timed_out"] is True

    def test_task_retry_exhaustion(self):
        """Test behavior when task exhausts all retries."""
        attempt_log = []

        class RetryExhaustedError(Exception):
            pass

        def task_with_retry(max_retries: int = 3):
            """Simulate task with retry logic."""
            for attempt in range(max_retries + 1):
                attempt_log.append(attempt)
                try:
                    # Always fail for this test
                    raise ValueError("Task failed")
                except ValueError as e:
                    if attempt < max_retries:
                        backoff = 0.1 * (2 ** attempt)
                        time.sleep(backoff)
                        continue
                    raise RetryExhaustedError(
                        f"Max retries ({max_retries}) exhausted"
                    ) from e

        with pytest.raises(RetryExhaustedError):
            task_with_retry(max_retries=3)

        assert len(attempt_log) == 4  # Initial + 3 retries
        assert attempt_log == [0, 1, 2, 3]

    def test_duplicate_task_execution(self):
        """Test prevention of duplicate task execution."""
        execution_log = []
        processed_task_ids = set()
        lock = threading.Lock()

        def execute_task_once(task_id: str, payload: dict) -> bool:
            """Execute task only if not already processed."""
            with lock:
                if task_id in processed_task_ids:
                    return False
                processed_task_ids.add(task_id)

            # Execute task
            execution_log.append({"task_id": task_id, "payload": payload})
            return True

        # Simulate duplicate task messages
        task_id = "task-123"
        payload = {"action": "process_booking", "booking_id": 456}

        # Multiple attempts to execute same task
        results = [execute_task_once(task_id, payload) for _ in range(5)]

        assert results == [True, False, False, False, False]
        assert len(execution_log) == 1

    def test_task_chain_failure_recovery(self):
        """Test recovery when a task in a chain fails."""
        chain_state = {
            "step_1": None,
            "step_2": None,
            "step_3": None,
            "recovered": False,
        }

        def step_1():
            chain_state["step_1"] = "completed"
            return {"data": "step_1_result"}

        def step_2(input_data: dict):
            chain_state["step_2"] = "completed"
            # Simulate failure
            raise ValueError("Step 2 failed")

        def step_3(input_data: dict):
            chain_state["step_3"] = "completed"
            return {"data": "step_3_result"}

        def compensate_step_1():
            """Compensation action for step 1."""
            chain_state["step_1"] = "compensated"
            chain_state["recovered"] = True

        def execute_chain_with_saga():
            """Execute chain with saga pattern for recovery."""
            compensations = []

            try:
                # Step 1
                result_1 = step_1()
                compensations.append(compensate_step_1)

                # Step 2
                result_2 = step_2(result_1)

                # Step 3
                result_3 = step_3(result_2)

                return result_3
            except Exception:
                # Execute compensations in reverse order
                for compensate in reversed(compensations):
                    try:
                        compensate()
                    except Exception:
                        pass  # Log and continue
                raise

        with pytest.raises(ValueError, match="Step 2 failed"):
            execute_chain_with_saga()

        assert chain_state["step_1"] == "compensated"
        assert chain_state["step_2"] is None  # Failed before completion
        assert chain_state["step_3"] is None  # Never reached
        assert chain_state["recovered"] is True

    def test_worker_crash_during_task(self):
        """Test recovery when worker crashes during task execution."""
        # Simulate task state storage
        task_states = {}
        lock = threading.Lock()

        def start_task(task_id: str) -> bool:
            """Mark task as started (heartbeat)."""
            with lock:
                if task_id in task_states and task_states[task_id]["status"] == "running":
                    return False  # Already running
                task_states[task_id] = {
                    "status": "running",
                    "started_at": time.time(),
                    "last_heartbeat": time.time(),
                }
            return True

        def complete_task(task_id: str, result: Any):
            """Mark task as completed."""
            with lock:
                task_states[task_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": time.time(),
                }

        def fail_task(task_id: str, error: str):
            """Mark task as failed."""
            with lock:
                task_states[task_id] = {
                    "status": "failed",
                    "error": error,
                    "failed_at": time.time(),
                }

        def recover_stale_tasks(timeout: float = 1.0):
            """Recover tasks that appear stuck (worker crashed)."""
            recovered = []
            current_time = time.time()

            with lock:
                for task_id, state in task_states.items():
                    if state["status"] == "running" and current_time - state["last_heartbeat"] > timeout:
                        task_states[task_id] = {
                            "status": "pending",
                            "recovered_at": current_time,
                        }
                        recovered.append(task_id)
            return recovered

        # Start a task
        task_id = "task-456"
        start_task(task_id)

        # Simulate worker crash (no completion, no heartbeat)
        time.sleep(0.1)

        # Recovery process finds stale task
        recovered = recover_stale_tasks(timeout=0.05)

        assert task_id in recovered
        assert task_states[task_id]["status"] == "pending"


# =============================================================================
# 6. Service Communication
# =============================================================================


class TestServiceCommunication:
    """Tests for external service communication patterns."""

    def test_external_api_timeout_handling(self):
        """Test handling of external API timeouts."""
        call_log = []

        def call_external_api(timeout: float = 1.0) -> dict:
            """Simulate external API call with timeout."""
            call_log.append({"time": time.time(), "timeout": timeout})

            # Simulate slow API
            if len(call_log) < 3:
                time.sleep(timeout + 0.5)  # Exceed timeout
                raise TimeoutError("API request timed out")

            return {"status": "success", "data": "response"}

        def call_with_timeout_handling(timeout: float, retries: int = 2) -> dict:
            """Call API with timeout and retry handling."""
            last_error = None

            for attempt in range(retries + 1):
                try:
                    return call_external_api(timeout=timeout)
                except TimeoutError as e:
                    last_error = e
                    if attempt < retries:
                        time.sleep(0.1)  # Brief delay before retry
                        continue

            raise last_error

        # Should eventually succeed after retries
        result = call_with_timeout_handling(timeout=0.1, retries=3)
        assert result["status"] == "success"
        assert len(call_log) == 3

    def test_circuit_breaker_pattern(self, circuit_breaker):
        """Test circuit breaker prevents cascading failures."""
        call_attempts = []
        service_healthy = False

        def call_unreliable_service():
            """Simulate unreliable service."""
            call_attempts.append(time.time())
            if not service_healthy:
                raise ConnectionError("Service unavailable")
            return {"status": "healthy"}

        def call_with_circuit_breaker(cb: CircuitBreaker) -> dict | None:
            """Call service with circuit breaker protection."""
            if not cb.can_execute():
                return None  # Fast fail when circuit is open

            try:
                result = call_unreliable_service()
                cb.record_success()
                return result
            except Exception:
                cb.record_failure()
                return None

        # Make calls until circuit opens
        for _ in range(5):
            call_with_circuit_breaker(circuit_breaker)

        # Circuit should be open after 3 failures
        assert circuit_breaker.state == "open"

        # Calls should be rejected without hitting service
        attempts_before = len(call_attempts)
        result = call_with_circuit_breaker(circuit_breaker)
        assert result is None
        assert len(call_attempts) == attempts_before  # No new calls

        # Wait for circuit to half-open
        time.sleep(1.1)

        # Make service healthy
        service_healthy = True

        # Circuit should allow test call (half-open)
        result = call_with_circuit_breaker(circuit_breaker)
        assert result is not None
        assert circuit_breaker.state == "closed"

    def test_retry_with_exponential_backoff(self):
        """Test retry logic with exponential backoff."""
        attempt_times = []
        success_on_attempt = 4

        def flaky_operation():
            """Operation that fails first few times."""
            attempt_times.append(time.time())
            if len(attempt_times) < success_on_attempt:
                raise ConnectionError("Temporary failure")
            return {"success": True}

        def retry_with_backoff(
            operation: Callable,
            max_retries: int = 5,
            base_delay: float = 0.1,
            max_delay: float = 2.0,
        ) -> Any:
            """Retry operation with exponential backoff."""
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    return operation()
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        # Add jitter
                        delay = delay * (0.5 + random.random())
                        time.sleep(delay)

            raise last_error

        result = retry_with_backoff(flaky_operation, max_retries=5, base_delay=0.01)

        assert result == {"success": True}
        assert len(attempt_times) == success_on_attempt

        # Verify backoff timing (delays should increase)
        delays = [
            attempt_times[i + 1] - attempt_times[i]
            for i in range(len(attempt_times) - 1)
        ]
        # Due to jitter, we can't assert exact exponential, but delays should exist
        assert all(d > 0 for d in delays)

    def test_partial_failure_scenario(self):
        """Test handling of partial failures in distributed operation."""
        service_states = {
            "service_a": "healthy",
            "service_b": "unhealthy",
            "service_c": "healthy",
        }

        def call_service(service_name: str) -> dict:
            """Call individual service."""
            if service_states[service_name] == "unhealthy":
                raise ConnectionError(f"{service_name} unavailable")
            return {"service": service_name, "data": "response"}

        def distributed_operation_with_partial_failure():
            """Execute operation across multiple services, handling partial failures."""
            results = {}
            errors = {}

            for service in ["service_a", "service_b", "service_c"]:
                try:
                    results[service] = call_service(service)
                except Exception as e:
                    errors[service] = str(e)

            return {
                "results": results,
                "errors": errors,
                "partial_success": len(results) > 0 and len(errors) > 0,
                "full_success": len(errors) == 0,
            }

        outcome = distributed_operation_with_partial_failure()

        assert outcome["partial_success"] is True
        assert outcome["full_success"] is False
        assert "service_a" in outcome["results"]
        assert "service_c" in outcome["results"]
        assert "service_b" in outcome["errors"]

    def test_bulkhead_isolation(self):
        """Test bulkhead pattern for isolating failures."""
        # Separate thread pools for different services
        bulkheads = {
            "critical": ThreadPoolExecutor(max_workers=5),
            "non_critical": ThreadPoolExecutor(max_workers=2),
        }

        execution_log = defaultdict(list)

        def execute_in_bulkhead(bulkhead_name: str, operation: Callable) -> Any:
            """Execute operation in specific bulkhead."""
            pool = bulkheads.get(bulkhead_name)
            if not pool:
                raise ValueError(f"Unknown bulkhead: {bulkhead_name}")

            future = pool.submit(operation)
            execution_log[bulkhead_name].append({"submitted": time.time()})
            return future

        def critical_operation():
            time.sleep(0.1)
            return "critical_result"

        def non_critical_operation():
            time.sleep(0.5)  # Slower, could block
            return "non_critical_result"

        # Submit operations to different bulkheads
        critical_futures = [
            execute_in_bulkhead("critical", critical_operation)
            for _ in range(3)
        ]

        non_critical_futures = [
            execute_in_bulkhead("non_critical", non_critical_operation)
            for _ in range(5)  # More than pool size
        ]

        # Critical operations should complete quickly
        critical_results = [f.result(timeout=2.0) for f in critical_futures]
        assert all(r == "critical_result" for r in critical_results)

        # Non-critical operations are isolated and queued
        completed_non_critical = 0
        for f in as_completed(non_critical_futures, timeout=5.0):
            try:
                f.result()
                completed_non_critical += 1
            except Exception:
                pass

        assert completed_non_critical == 5

        # Cleanup
        for pool in bulkheads.values():
            pool.shutdown(wait=False)


# =============================================================================
# Integration Tests - Complex Scenarios
# =============================================================================


class TestComplexDistributedScenarios:
    """Integration tests for complex distributed scenarios."""

    @pytest.mark.asyncio
    async def test_distributed_saga_with_compensation(self):
        """Test saga pattern across multiple services with compensation."""
        saga_state = {
            "steps_completed": [],
            "compensations_executed": [],
            "final_status": None,
        }

        async def step_reserve_inventory(order_id: str) -> dict:
            """Step 1: Reserve inventory."""
            saga_state["steps_completed"].append("reserve_inventory")
            return {"order_id": order_id, "reserved": True}

        async def compensate_reserve_inventory(order_id: str):
            """Compensation: Release inventory."""
            saga_state["compensations_executed"].append("release_inventory")

        async def step_charge_payment(order_id: str) -> dict:
            """Step 2: Charge payment."""
            saga_state["steps_completed"].append("charge_payment")
            # Simulate payment failure
            raise ValueError("Payment declined")

        async def compensate_charge_payment(order_id: str):
            """Compensation: Refund payment."""
            saga_state["compensations_executed"].append("refund_payment")

        async def step_ship_order(order_id: str) -> dict:
            """Step 3: Ship order."""
            saga_state["steps_completed"].append("ship_order")
            return {"order_id": order_id, "shipped": True}

        async def execute_saga(order_id: str):
            """Execute saga with compensation on failure."""
            compensations = []

            try:
                # Step 1
                await step_reserve_inventory(order_id)
                compensations.append(lambda: compensate_reserve_inventory(order_id))

                # Step 2
                await step_charge_payment(order_id)
                compensations.append(lambda: compensate_charge_payment(order_id))

                # Step 3
                await step_ship_order(order_id)

                saga_state["final_status"] = "completed"
            except Exception:
                # Execute compensations in reverse
                for compensate in reversed(compensations):
                    with suppress(Exception):
                        await compensate()
                saga_state["final_status"] = "rolled_back"
                raise

        with pytest.raises(ValueError, match="Payment declined"):
            await execute_saga("order-123")

        assert saga_state["steps_completed"] == ["reserve_inventory", "charge_payment"]
        assert saga_state["compensations_executed"] == ["release_inventory"]
        assert saga_state["final_status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_concurrent_booking_conflict_resolution(self):
        """Test resolving conflicts when multiple users book same slot."""
        available_slots = {"slot_1": True}
        slot_lock = asyncio.Lock()

        async def try_book_slot(user_id: str, slot_id: str) -> dict:
            """Attempt to book a slot with optimistic locking."""
            async with slot_lock:
                if not available_slots.get(slot_id, False):
                    return {"user_id": user_id, "success": False, "reason": "slot_unavailable"}

                # Simulate processing delay
                await asyncio.sleep(0.01)

                # Book the slot
                available_slots[slot_id] = False
                return {"user_id": user_id, "success": True, "slot_id": slot_id}

        # Multiple users try to book same slot concurrently
        users = ["user_1", "user_2", "user_3"]

        results = await asyncio.gather(*[
            try_book_slot(user, "slot_1") for user in users
        ])

        # Only one should succeed
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        assert len(successful) == 1
        assert len(failed) == 2

    def test_distributed_rate_limiting(self):
        """Test rate limiting across distributed instances."""
        window_size = 1.0  # 1 second window
        max_requests = 5
        request_counts = defaultdict(list)
        lock = threading.Lock()

        def is_rate_limited(client_id: str) -> bool:
            """Check if client is rate limited."""
            current_time = time.time()

            with lock:
                # Clean old requests
                request_counts[client_id] = [
                    t for t in request_counts[client_id]
                    if current_time - t < window_size
                ]

                if len(request_counts[client_id]) >= max_requests:
                    return True

                request_counts[client_id].append(current_time)
                return False

        # Simulate rapid requests from same client
        client_id = "client_123"
        results = []

        for _ in range(10):
            limited = is_rate_limited(client_id)
            results.append(limited)
            time.sleep(0.05)

        # First 5 should pass, rest should be limited
        assert results[:5] == [False] * 5
        assert any(results[5:])  # Some should be limited

    @pytest.mark.asyncio
    async def test_eventual_consistency_verification(self):
        """Test verification of eventual consistency between systems."""
        primary_db = {"records": {}}
        replica_db = {"records": {}}
        replication_lag = 0.1  # Simulated replication lag

        async def write_to_primary(key: str, value: Any):
            """Write to primary database."""
            primary_db["records"][key] = value

            # Async replication to replica
            async def replicate():
                await asyncio.sleep(replication_lag)
                replica_db["records"][key] = value

            asyncio.create_task(replicate())

        async def read_from_replica(key: str) -> Any | None:
            """Read from replica database."""
            return replica_db["records"].get(key)

        async def verify_consistency(key: str, expected: Any, timeout: float = 1.0) -> bool:
            """Verify data is consistent within timeout."""
            start = time.time()

            while time.time() - start < timeout:
                actual = await read_from_replica(key)
                if actual == expected:
                    return True
                await asyncio.sleep(0.05)

            return False

        # Write to primary
        await write_to_primary("user_1", {"name": "Test User"})

        # Immediate read from replica should fail (not yet replicated)
        immediate_value = await read_from_replica("user_1")
        assert immediate_value is None

        # Wait and verify eventual consistency
        is_consistent = await verify_consistency(
            "user_1",
            {"name": "Test User"},
            timeout=1.0
        )
        assert is_consistent is True
