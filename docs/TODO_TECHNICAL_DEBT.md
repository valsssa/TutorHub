# Technical Debt Register

**Last Updated**: 2026-01-29
**Source**: `docs/architecture/09-future-evolution.md` + ongoing discoveries

---

## Priority Matrix

```
                    HIGH IMPACT
                         │
    ✅ API Versioning    │    ● Single-region
         DONE            │
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
**Status**: 🟢 COMPLETE ✅
**Completed**: 2026-01-29
**Effort**: Medium
**Impact**: High

**What Was Done**:
- ✅ All endpoints now use `/api/v1/` prefix
- ✅ 25+ module routers updated to remove `/api/` prefix
- ✅ Centralized versioning in `main.py` with `API_V1_PREFIX = "/api/v1"`
- ✅ Frontend updated: `lib/api.ts`, `lib/api/auth.ts`, components, tests
- ✅ OpenAPI documentation updated with versioned servers
- ✅ Documentation updated: `CLAUDE.md`, `modules/README.md`

**Files Modified**:
- `backend/main.py` - Centralized versioning
- All routers in `backend/modules/*/`
- `frontend/lib/api.ts`, `frontend/lib/api/auth.ts`
- `frontend/components/TimeSlotPicker.tsx`, `TutorProfileView.tsx`, `ModernBookingModal.tsx`
- `frontend/e2e/auth-flow.spec.ts`, `frontend/__tests__/integration/favorites-integration.test.ts`

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

**Progress**:
- [x] ✅ Booking state machine tests (comprehensive - 700+ lines)
- [ ] Payment flow tests
- [ ] Authentication tests
- [ ] Tutor approval workflow tests
- [ ] Package purchase and usage tests

**Files Created**:
- ✅ `backend/modules/bookings/tests/test_state_machine.py` (expanded)

**Files to Create**:
- `backend/tests/test_payment_flow.py`
- `frontend/__tests__/`

**Assigned**: [ ]
**Target Date**: [ ]

---

## Medium Priority (Plan for Next Quarter)

### 5. Feature Flags System
**Status**: 🟢 COMPLETE ✅
**Completed**: 2026-01-29
**Effort**: Low
**Impact**: Medium

**What Was Done**:
- ✅ Simple Redis-backed feature flags with caching
- ✅ User/percentage targeting (consistent hashing)
- ✅ Allowlist and denylist support
- ✅ Admin API for flag management
- ✅ Frontend React hooks and components
- ✅ Default flags initialization on startup

**Files Created**:
- `backend/core/feature_flags.py` - Core feature flags system
- `backend/modules/admin/feature_flags_router.py` - Admin API endpoints
- `frontend/lib/featureFlags.ts` - Frontend client and hooks

**Features**:
- FeatureState: disabled, enabled, percentage, allowlist, denylist
- Local caching (60s TTL) to reduce Redis calls
- Consistent percentage rollouts per user
- React hooks: `useFeatureFlag`, `useFeatureFlags`
- `FeatureFlagGuard` component for conditional rendering
- Default flags: new_booking_flow, ai_tutor_matching, instant_booking, video_sessions, group_sessions

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
**Status**: 🟡 Partial
**Effort**: Medium
**Impact**: Low
**Risk if Ignored**: Slow incident response

**Current State**:
- ✅ Manual runbook procedures created
- Human execution required

**Target State**:
- Scripted runbooks
- One-click execution
- Audit trail

**Progress**:
- ✅ Runbooks created (`docs/runbooks/`)
- [ ] Scripts for automation

**Files to Create**:
- `scripts/runbooks/`

**Assigned**: [ ]
**Target Date**: [ ]

---

### 11. Load Testing Suite
**Status**: 🟢 COMPLETE ✅
**Completed**: 2026-01-29
**Effort**: Medium
**Impact**: Medium

**What Was Done**:
- ✅ Locust test suite with user behavior simulation
- ✅ Multiple user types (anonymous, student, tutor)
- ✅ Success criteria defined (P95 <500ms, Error <1%)
- ✅ Test scenarios (normal, peak, stress, soak)
- ✅ CI/CD integration instructions
- ✅ Documentation for running tests

**Files Created**:
- `tests/load/locustfile.py` - Main test suite
- `tests/load/README.md` - Usage documentation

**Test Endpoints**:
- Health check, browse tutors, search tutors
- View tutor profile, view subjects, view reviews
- User-specific: bookings, wallet, packages, notifications

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

## Debt Payoff Progress

| Item | Status | Completed |
|------|--------|-----------|
| API Versioning | ✅ Complete | 2026-01-29 |
| Test Coverage (State Machine) | ✅ Partial | 2026-01-29 |
| Runbooks | ✅ Complete | 2026-01-29 |
| Feature Flags | ✅ Complete | 2026-01-29 |
| Load Testing | ✅ Complete | 2026-01-29 |
| APScheduler→Celery | 🔴 Not Started | - |
| Distributed Tracing | 🔴 Not Started | - |
| Multi-region prep | 🔴 Not Started | - |
| Alembic | 🔴 Not Started | - |

---

## Debt Payoff Schedule

| Quarter | Items | Status |
|---------|-------|--------|
| Q1 2026 | API Versioning, Test Coverage, Feature Flags | 🟢 3/3 Complete |
| Q2 2026 | APScheduler→Celery, Distributed Tracing, Load Testing | 🟡 1/3 Complete |
| Q3 2026 | Multi-region prep, Alembic, Cache improvements | 🔴 Not Started |
| Q4 2026 | ADRs, Runbook automation, Dependencies | 🟡 Partial |

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
