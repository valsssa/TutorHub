# Technical Debt Register

**Last Updated**: 2026-01-29
**Source**: `docs/architecture/09-future-evolution.md` + ongoing discoveries

---

## Priority Matrix

```
                    HIGH IMPACT
                         │
    API Versioning  ●    │    ● Single-region
                         │
    APScheduler     ●    │    ● Test Coverage
LOW EFFORT ───────────────┼─────────────── HIGH EFFORT
                         │
    Feature Flags   ●    │    ● Distributed Tracing
                         │
    ADR Docs        ●    │    ● Load Testing
                         │
                    LOW IMPACT
```

---

## High Priority (Address This Quarter)

### 1. API Versioning
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: High
**Risk if Ignored**: Breaking changes affect all clients

**Current State**:
- Endpoints use `/api/bookings` without version prefix
- No deprecation headers
- No version negotiation

**Target State**:
- All endpoints prefixed with `/api/v1/`
- Deprecation headers for old endpoints
- Clear migration path for clients

**Implementation**:
```python
# Phase 1: Add versioned routes (parallel)
app.include_router(bookings_router, prefix="/api/bookings")      # Old
app.include_router(bookings_router, prefix="/api/v1/bookings")   # New

# Phase 2: Update clients to v1

# Phase 3: Deprecate unversioned (log warnings)
@app.middleware("http")
async def deprecation_warning(request, call_next):
    if request.url.path.startswith("/api/") and "/v1/" not in request.url.path:
        logger.warning(f"Deprecated API call: {request.url.path}")
    return await call_next(request)

# Phase 4: Remove unversioned routes
```

**Files to Modify**:
- `backend/main.py`
- All routers in `backend/modules/*/`
- `frontend/lib/api.ts`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 2. APScheduler → Celery Migration
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: High
**Risk if Ignored**: Jobs lost on restart, no visibility, no retry logic

**Current State**:
- APScheduler runs in-process with backend
- Jobs lost if backend restarts during execution
- No job queue, no retry, no monitoring

**Target State**:
- Celery workers with Redis broker
- Persistent job queue
- Retry logic with exponential backoff
- Flower monitoring dashboard

**Implementation**:
```python
# Current (APScheduler)
scheduler.add_job(expire_requests, 'interval', minutes=5)

# Target (Celery)
@celery_app.task(bind=True, max_retries=3)
def expire_requests(self):
    try:
        # ... task logic
    except Exception as exc:
        self.retry(exc=exc, countdown=60)

celery_app.conf.beat_schedule = {
    'expire-requests': {
        'task': 'tasks.expire_requests',
        'schedule': crontab(minute='*/5'),
    },
}
```

**Files to Modify**:
- `backend/core/scheduler.py` → `backend/core/celery.py`
- `backend/modules/bookings/jobs.py`
- `docker-compose.yml` (add Celery worker, beat)

**New Files**:
- `backend/core/celery.py`
- `backend/tasks/`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 3. Single-Region → Multi-Region Preparation
**Status**: 🟡 Planning
**Effort**: High
**Impact**: High
**Risk if Ignored**: Extended downtime risk, no failover

**Current State**:
- Single VM deployment
- No geographic redundancy
- Manual recovery

**Target State (Phase 2)**:
- Kubernetes in single region with multi-AZ
- Read replicas for PostgreSQL
- CDN for static assets

**Target State (Phase 3)**:
- Multi-region Kubernetes
- Cross-region database replication
- Global load balancer

**Preparation Steps**:
1. [ ] Externalize session state to Redis
2. [ ] Ensure all timestamps are UTC
3. [ ] Test read replica queries
4. [ ] Document data residency requirements
5. [ ] Set up infrastructure-as-code (Terraform)

**Files to Modify**:
- `docker-compose.yml` → `kubernetes/`
- `backend/core/database.py`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 4. Test Coverage Improvement
**Status**: 🟡 In Progress
**Effort**: High
**Impact**: High
**Risk if Ignored**: Regression bugs, deployment fear

**Current State**:
- Backend: ~60% coverage
- Frontend: ~40% coverage
- Some critical paths untested

**Target State**:
- Backend: 80% coverage
- Frontend: 70% coverage
- All critical paths tested

**Priority Test Areas**:
1. [ ] Booking state machine (all transitions)
2. [ ] Payment flow (auth, capture, refund)
3. [ ] Authentication (login, OAuth, token expiry)
4. [ ] Tutor approval workflow
5. [ ] Package purchase and usage

**Files to Create**:
- `backend/tests/test_state_machine_comprehensive.py`
- `backend/tests/test_payment_flow.py`
- `frontend/__tests__/`

**Assigned**: [ ]
**Target Date**: [ ]

---

## Medium Priority (Plan for Next Quarter)

### 5. Feature Flags System
**Status**: 🔴 Not Started
**Effort**: Low
**Impact**: Medium
**Risk if Ignored**: Risky deployments, all-or-nothing releases

**Current State**:
- No feature flags
- All features released to all users
- No gradual rollout capability

**Target State**:
- Simple Redis-backed feature flags
- User/percentage targeting
- Admin UI for flag management

**Implementation Options**:
- LaunchDarkly (SaaS, cost)
- Unleash (self-hosted)
- Custom Redis-based (simple)

**Files to Create**:
- `backend/core/feature_flags.py`
- `frontend/lib/featureFlags.ts`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 6. Distributed Tracing
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: Medium
**Risk if Ignored**: Hard to debug at scale

**Current State**:
- No correlation IDs
- Logs not linked across services
- No trace visualization

**Target State**:
- OpenTelemetry integration
- Correlation IDs in all requests
- Jaeger/Tempo for visualization

**Implementation**:
```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

**Files to Create**:
- `backend/core/tracing.py`
- `docker-compose.yml` (add Jaeger)

**Assigned**: [ ]
**Target Date**: [ ]

---

### 7. Frontend Cache Improvements
**Status**: 🔴 Not Started
**Effort**: Low
**Impact**: Medium
**Risk if Ignored**: Stale data bugs

**Current State**:
- Manual cache invalidation
- No consistent pattern
- Some stale data issues

**Target State**:
- Automatic invalidation on mutations
- SWR/React Query integration
- Clear cache patterns

**Files to Modify**:
- `frontend/lib/api.ts`
- `frontend/hooks/useApi.ts`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 8. Alembic Migration Tooling
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: Medium
**Risk if Ignored**: Migration errors, manual process

**Current State**:
- Manual SQL files in `database/migrations/`
- No rollback support
- No version tracking in code

**Target State**:
- Alembic for Python migrations
- Auto-generated migrations
- Rollback capability

**Files to Create**:
- `backend/alembic/`
- `backend/alembic.ini`

**Assigned**: [ ]
**Target Date**: [ ]

---

## Low Priority (Nice to Have)

### 9. Architecture Decision Records
**Status**: 🟡 Partial
**Effort**: Low
**Impact**: Low
**Risk if Ignored**: Onboarding friction, lost context

**Current State**:
- 5 ADRs exist in `docs/architecture/decisions/`
- Many decisions undocumented

**Target State**:
- ADRs for all major decisions
- Template in use
- New decisions documented

**ADRs to Create**:
- [ ] ADR-006: APScheduler for Background Jobs
- [ ] ADR-007: Next.js for Frontend
- [ ] ADR-008: MinIO for Object Storage
- [ ] ADR-009: Brevo for Email
- [ ] ADR-010: Booking State Machine Design

**Files Location**: `docs/architecture/decisions/`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 10. Runbook Automation
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: Low
**Risk if Ignored**: Slow incident response

**Current State**:
- Manual runbook procedures
- Human execution required

**Target State**:
- Scripted runbooks
- One-click execution
- Audit trail

**Files to Create**:
- `scripts/runbooks/`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 11. Load Testing Suite
**Status**: 🔴 Not Started
**Effort**: Medium
**Impact**: Medium
**Risk if Ignored**: Unknown capacity limits

**Current State**:
- No load tests
- Unknown breaking points
- No performance baseline

**Target State**:
- Locust/k6 test suite
- Performance baseline documented
- CI/CD integration

**Files to Create**:
- `tests/load/locustfile.py`
- `docs/PERFORMANCE_BASELINE.md`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 12. Dependency Updates
**Status**: 🟡 Ongoing
**Effort**: Low
**Impact**: Low (unless security vuln)
**Risk if Ignored**: Security vulnerabilities

**Current State**:
- Some outdated packages
- No automated updates

**Target State**:
- Dependabot/Renovate enabled
- Monthly update cycle
- Security updates immediate

**Configuration**:
- `.github/dependabot.yml`

**Assigned**: [ ]
**Target Date**: [ ]

---

## Debt Payoff Schedule

| Quarter | Items | Effort |
|---------|-------|--------|
| Q1 2026 | API Versioning, Test Coverage, Feature Flags | High |
| Q2 2026 | APScheduler→Celery, Distributed Tracing, Load Testing | High |
| Q3 2026 | Multi-region prep, Alembic, Cache improvements | Medium |
| Q4 2026 | ADRs, Runbook automation, Dependencies | Low |

---

## Tracking

### How to Add New Debt

1. Add entry to this file with template below
2. Assess priority using impact/effort matrix
3. Assign owner if known
4. Link to related issues/PRs

### Template

```markdown
### N. [Title]
**Status**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete
**Effort**: Low | Medium | High
**Impact**: Low | Medium | High
**Risk if Ignored**: [Description]

**Current State**:
- [Bullet points]

**Target State**:
- [Bullet points]

**Files to Modify**:
- [File paths]

**Assigned**: [ ]
**Target Date**: [ ]
```

---

## Related Documents

- [Future Evolution](./architecture/09-future-evolution.md) - Original debt register
- [Scalability & Operations](./architecture/08-scalability-operations.md) - Infrastructure debt
- [Security & Reliability](./architecture/07-security-reliability.md) - Security debt
