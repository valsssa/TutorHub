# ADR-006: APScheduler for Background Jobs

## Status

Accepted

## Date

2026-01-29

## Context

EduStream requires background job processing for automated booking state transitions:
- Expire pending booking requests after 24 hours
- Automatically start sessions at scheduled start time
- Automatically end sessions after end time plus grace period
- Send reminder notifications before sessions

Key forces at play:
- **Simplicity**: MVP stage requires minimal operational complexity
- **Single process**: Modular monolith architecture favors in-process scheduling
- **Job characteristics**: Jobs are lightweight, periodic polling operations
- **Reliability**: Jobs must be idempotent to handle restarts gracefully
- **Concurrency**: Must handle race conditions with API operations

## Decision

We will use **APScheduler** (Advanced Python Scheduler) with AsyncIOScheduler for background job processing.

Configuration:
- Scheduler runs in-process with the FastAPI application
- Uses FastAPI lifespan context manager for startup/shutdown
- Jobs use IntervalTrigger for periodic execution
- Each job type limited to max_instances=1 to prevent overlap

Job schedule:
```python
expire_requests:   every 5 minutes  # REQUESTED → EXPIRED
start_sessions:    every 1 minute   # SCHEDULED → ACTIVE
end_sessions:      every 1 minute   # ACTIVE → ENDED
```

Race condition handling:
- Jobs use SELECT FOR UPDATE with NOWAIT for row-level locking
- State machine transitions are idempotent (success if already in target state)
- Each booking processed in its own transaction to minimize lock contention
- Failed locks are skipped and retried on next interval

## Consequences

### Positive

- **Operational simplicity**: No separate worker process or message broker
- **Zero additional infrastructure**: Runs within existing FastAPI process
- **Easy debugging**: Jobs visible in application logs
- **Fast iteration**: Add/modify jobs with code changes only
- **Pythonic**: Native async/await support, integrates with SQLAlchemy

### Negative

- **Single point of failure**: If application crashes, jobs stop
- **No distributed execution**: Cannot scale jobs across multiple workers
- **No job persistence**: Scheduled jobs lost on restart
- **Limited visibility**: No built-in dashboard for job monitoring
- **No retry with backoff**: Must implement custom retry logic

### Neutral

- Jobs are stateless polling operations, so persistence not critical
- Idempotency ensures missed jobs catch up on restart
- Interval-based scheduling means brief outages don't cause data inconsistency

## Alternatives Considered

### Option A: Celery with Redis

Distributed task queue with separate worker processes.

**Pros:**
- Battle-tested at scale
- Built-in retry and dead-letter queues
- Job persistence and monitoring (Flower)
- Horizontal scaling of workers

**Cons:**
- Requires Redis or RabbitMQ infrastructure
- Separate worker process to deploy and monitor
- More complex debugging (distributed logs)
- Overkill for current job volume

**Why not chosen:** Infrastructure overhead not justified at MVP scale. Documented as migration path for future scaling.

### Option B: Database-backed Job Queue (e.g., pgqueue)

Store jobs in PostgreSQL, workers poll the database.

**Pros:**
- Uses existing database
- Job persistence built-in
- Transactional job creation

**Cons:**
- Polling overhead on database
- Custom implementation effort
- Less mature than dedicated solutions

**Why not chosen:** APScheduler simpler for current needs; Celery better long-term option.

### Option C: Cron Jobs

External cron triggering HTTP endpoints.

**Pros:**
- Simple, widely understood
- Works with any language

**Cons:**
- External dependency on host cron
- Harder to manage in containers
- No native Python integration
- Separate configuration to maintain

**Why not chosen:** Doesn't integrate cleanly with Docker deployment.

### Option D: Cloud-native (AWS Lambda, Cloud Tasks)

Serverless scheduled functions.

**Pros:**
- Auto-scaling
- Managed infrastructure
- Pay-per-execution

**Cons:**
- Vendor lock-in
- Cold starts add latency
- Requires database connectivity setup
- More complex local development

**Why not chosen:** Adds deployment complexity; doesn't fit self-hosted model.

## Migration Path to Celery

When scaling requires distributed job processing:

1. **Add Celery infrastructure**: Redis/RabbitMQ, Celery worker container
2. **Create task wrappers**: Convert APScheduler jobs to Celery tasks
3. **Parallel running period**: Run both systems to verify parity
4. **Cutover**: Disable APScheduler jobs, rely on Celery beat
5. **Remove APScheduler**: Clean up deprecated code

Triggers for migration:
- Job execution time exceeds polling interval
- Need for job persistence across restarts
- Multiple application instances requiring coordination
- Requirement for manual job triggering or admin dashboard

## References

- Implementation: `backend/core/scheduler.py`
- Booking jobs: `backend/modules/bookings/jobs.py`
- State machine: `backend/modules/bookings/domain/state_machine.py`
- APScheduler documentation: https://apscheduler.readthedocs.io/
