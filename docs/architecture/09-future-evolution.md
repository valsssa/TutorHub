# Future Evolution & Technical Debt

## 1. Likely Future Requirements

### High Probability (Next 6-12 Months)

| Requirement | Complexity | Preparation Needed |
|-------------|------------|-------------------|
| Mobile Apps | High | API already mobile-ready |
| Multi-language UI | Medium | i18n infrastructure needed |
| Payment disputes | Medium | Dispute state machine exists |
| Tutor analytics | Low | Metrics infrastructure exists |
| Email templates | Low | Brevo templates ready |

### Medium Probability (12-24 Months)

| Requirement | Complexity | Preparation Needed |
|-------------|------------|-------------------|
| Group Sessions | High | Schema changes, booking logic redesign |
| Subscription Model | Medium | Payment model extension |
| AI Tutor Matching | High | Data pipeline for ML |
| Referral Program | Medium | Tracking infrastructure |
| Mobile push notifications | Medium | FCM/APNs integration |

### Low Probability (Future Consideration)

| Requirement | Complexity | Notes |
|-------------|------------|-------|
| Video Recording | Medium | Storage cost concerns |
| White-label / Multi-tenant | Very High | Major architecture change |
| Marketplace Expansion | Very High | Different verticals |
| Blockchain Credentials | High | Trend dependent |

## 2. Intentionally Deferred Decisions

### Architecture Decisions

| Decision | Reason for Deferral | Revisit When |
|----------|---------------------|--------------|
| Microservices | Ops overhead > benefit | Team > 5 or scale > 10K MAU |
| Event Sourcing | Complexity not justified | Audit needs exceed logging |
| GraphQL | REST sufficient | Mobile app complex needs |
| Multi-region | Cost and complexity | Users span continents |
| Kubernetes | Docker Compose sufficient | Need auto-scaling |

### Feature Decisions

| Feature | Reason for Deferral | Revisit When |
|---------|---------------------|--------------|
| Offline mode | Web-first MVP | Mobile app launch |
| Real-time video | Zoom integration works | Cost/control tradeoff |
| Custom domains | Not B2B yet | Enterprise customers |
| API rate tiers | Single tier sufficient | Partner API program |

## 3. Change Impact Analysis

### Easy to Change (Low Coupling)

| Component | Why Easy | Example Changes |
|-----------|----------|-----------------|
| UI Components | Isolated React | New button styles |
| Email Templates | Brevo abstraction | New notification types |
| Rate Limits | Configuration only | Adjust thresholds |
| Pricing Tiers | Database + config | New commission levels |
| Notification Types | Template-based | New notification categories |

### Medium Difficulty (Module Boundaries)

| Component | Challenges | Mitigation |
|-----------|------------|------------|
| New Lesson Types | Schema + state machine | Extend existing enums |
| Payment Providers | Need adapter pattern | Abstract interface exists |
| OAuth Providers | Pattern established | Follow existing OAuth flow |
| New User Roles | Pervasive checks | Role hierarchy supports |
| API Versioning | Not started | Add `/api/v1/` prefix |

### Hard to Change (Core Domain)

| Component | Why Hard | Risk Mitigation |
|-----------|----------|-----------------|
| Booking State Machine | Core business logic | Extensive test coverage |
| User Role System | Pervasive checks | Additive changes only |
| Payment Flow | Stripe integration | Stripe handles edge cases |
| Database Schema | 45+ tables, relationships | Careful migration planning |
| Authentication | Security critical | Don't reinvent, use standards |

## 4. Technical Debt Register

### High Priority (Should Address Soon)

| Item | Description | Effort | Risk if Ignored |
|------|-------------|--------|-----------------|
| API Versioning | No version prefix on endpoints | Medium | Breaking changes affect all clients |
| APScheduler | In-process, jobs lost on restart | Medium | Missed state transitions |
| Single-region | No failover capability | High | Extended downtime risk |
| Test Coverage | Some modules untested | Medium | Regression bugs |

### Medium Priority (Plan for Next Quarter)

| Item | Description | Effort | Risk if Ignored |
|------|-------------|--------|-----------------|
| Feature Flags | All-or-nothing releases | Low | Risky deployments |
| Distributed Tracing | No OpenTelemetry | Medium | Hard to debug at scale |
| Frontend Cache | Manual invalidation | Low | Stale data bugs |
| Alembic Migration | Manual SQL files | Medium | Migration errors |

### Low Priority (Nice to Have)

| Item | Description | Effort | Risk if Ignored |
|------|-------------|--------|-----------------|
| ADR Documentation | Decisions not recorded | Low | Onboarding friction |
| Runbook Automation | Manual procedures | Medium | Slow incident response |
| Load Testing | No performance baseline | Medium | Unknown capacity limits |
| Dependency Updates | Some outdated packages | Low | Security vulnerabilities |

### Debt Payoff Priority Matrix

```
                    HIGH IMPACT
                         |
    API Versioning  *    |    * Single-region
                         |
    APScheduler     *    |    * Test Coverage
LOW EFFORT ---------------+--------------- HIGH EFFORT
                         |
    Feature Flags   *    |    * Distributed Tracing
                         |
    ADR Docs        *    |    * Load Testing
                         |
                    LOW IMPACT
```

## 5. Exit Strategies

### Technology Exit Paths

| Current | Exit To | Effort | Trigger |
|---------|---------|--------|---------|
| PostgreSQL | MySQL/CockroachDB | High | Extreme scale needs |
| APScheduler | Celery + Redis | Low-Medium | Job reliability issues |
| MinIO | AWS S3 | Low | S3-compatible API |
| Stripe | Adyen/PayPal | Medium | Regional expansion |
| FastAPI | Django | High | Framework limitations |
| Next.js | Remix | Medium-High | SSR performance |

### Vendor Lock-in Assessment

| Vendor | Lock-in Level | Exit Difficulty | Mitigation |
|--------|---------------|-----------------|------------|
| Stripe | Medium | Medium | Payment abstraction layer exists |
| Google OAuth | Low | Low | Standard OAuth, multi-provider |
| Zoom | Low | Low | Meeting links are URLs |
| Brevo | Low | Low | Standard email API |
| PostgreSQL | Low | Medium | Standard SQL |

## 6. Recommended Improvements

### Immediate (Next Sprint)

1. **Add API Versioning**
   ```python
   # Change: /api/bookings -> /api/v1/bookings
   app.include_router(bookings_router, prefix="/api/v1")
   ```

2. **Implement Health Dashboard**
   - Add Prometheus metrics
   - Create Grafana dashboard

3. **Document ADRs**
   - Record existing decisions
   - Template for future decisions

### Short-term (Next Month)

1. **Migrate to Celery**
   - Replace APScheduler
   - Add Redis as broker
   - Implement retry logic

2. **Add Feature Flags**
   - Simple database-backed flags
   - Gradual rollout capability

3. **Improve Test Coverage**
   - Target 80% backend coverage
   - Add E2E for critical paths

### Medium-term (Next Quarter)

1. **Multi-region Preparation**
   - Read replica setup
   - CDN configuration
   - Session externalization

2. **OpenTelemetry Integration**
   - Distributed tracing
   - Correlation IDs

3. **Performance Baseline**
   - Load testing suite
   - Performance monitoring

## 7. Migration Guides

### APScheduler to Celery Migration

```python
# Current (APScheduler)
scheduler.add_job(expire_requests, 'interval', minutes=5)

# Target (Celery)
@celery_app.task
def expire_requests():
    ...

celery_app.conf.beat_schedule = {
    'expire-requests': {
        'task': 'tasks.expire_requests',
        'schedule': crontab(minute='*/5'),
    },
}
```

### API Versioning Migration

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

## 8. Architecture Decision Records

### Location

ADRs are stored in `docs/architecture/decisions/`

### Template

```markdown
# ADR-XXX: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR-YYY

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
What other options were evaluated?
```

### Initial ADRs to Create

1. ADR-001: Modular Monolith Architecture
2. ADR-002: Four-Field Booking State Machine
3. ADR-003: PostgreSQL as Primary Database
4. ADR-004: JWT Authentication Strategy
5. ADR-005: Stripe Connect for Payments
6. ADR-006: APScheduler for Background Jobs
7. ADR-007: Next.js for Frontend

## 9. Success Metrics

### Technical Health

| Metric | Current | Target (6mo) | Target (12mo) |
|--------|---------|--------------|---------------|
| Test Coverage | ~60% | 80% | 90% |
| API Latency P95 | 200ms | 150ms | 100ms |
| Deploy Frequency | Weekly | Daily | Multiple/day |
| MTTR | 4 hours | 1 hour | 30 min |
| Error Rate | 0.5% | 0.2% | 0.1% |

### Platform Health

| Metric | Current | Target (6mo) | Target (12mo) |
|--------|---------|--------------|---------------|
| Uptime | 99% | 99.5% | 99.9% |
| Session Completion | 85% | 90% | 95% |
| Payment Success | 98% | 99% | 99.5% |
| Cancellation Rate | 5% | 4% | 3% |
