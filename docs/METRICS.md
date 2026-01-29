# Success Metrics

**Last Updated**: 2026-01-29

---

## North Star Metric

**Weekly Active Learners (WAL)**: Students who complete at least one session per week

**Target**: 100 WAL by end of Phase 1 (Week 12)

---

## Key Performance Indicators (KPIs)

### Business Metrics

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **Weekly Active Learners** | Students with 1+ completed sessions/week | 100 | TBD | - |
| **Weekly Active Tutors** | Tutors with 1+ completed sessions/week | 20 | TBD | - |
| **Booking Conversion Rate** | Confirmed bookings / booking requests | 70% | TBD | - |
| **Session Completion Rate** | Completed sessions / confirmed bookings | 90% | TBD | - |
| **Tutor Approval Rate** | Approved tutors / tutor applications | 60% | TBD | - |

### Revenue Metrics

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **Gross Merchandise Value (GMV)** | Total value of all bookings | $10K/month | TBD | - |
| **Net Revenue** | GMV × Commission Rate | $1.5K/month | TBD | - |
| **Average Session Value** | GMV / Total Sessions | $40 | TBD | - |
| **Package Purchase Rate** | Users who buy packages / active users | 30% | TBD | - |

### Engagement Metrics

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **Student Retention (30-day)** | Students active after 30 days | 50% | TBD | - |
| **Tutor Retention (30-day)** | Tutors active after 30 days | 70% | TBD | - |
| **Messages per Booking** | Average messages exchanged | 5+ | TBD | - |
| **Review Rate** | Sessions with reviews / completed sessions | 40% | TBD | - |
| **Average Rating** | Mean of all session ratings | 4.5+ | TBD | - |

---

## Technical Metrics

### Performance

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **API P50 Response Time** | 50th percentile latency | <100ms | TBD | - |
| **API P95 Response Time** | 95th percentile latency | <500ms | TBD | - |
| **API P99 Response Time** | 99th percentile latency | <1000ms | TBD | - |
| **Page Load Time (LCP)** | Largest Contentful Paint | <2.5s | TBD | - |
| **Time to Interactive (TTI)** | Page becomes interactive | <3.5s | TBD | - |

### Reliability

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **Uptime** | % time service is available | 99.5% | TBD | - |
| **Error Rate** | % of requests returning 5xx | <1% | TBD | - |
| **Deployment Success Rate** | % of deployments without rollback | 95% | TBD | - |
| **Mean Time to Recovery (MTTR)** | Average incident resolution time | <1 hour | TBD | - |

### Quality

| Metric | Definition | Target | Current | Status |
|--------|------------|--------|---------|--------|
| **Backend Test Coverage** | % of code covered by tests | 80% | ~60% | 🟡 |
| **Frontend Test Coverage** | % of code covered by tests | 70% | ~40% | 🟡 |
| **Critical Bug Count** | Open P0/P1 bugs | 0 | TBD | - |
| **Security Vulnerabilities** | Known CVEs in dependencies | 0 critical | TBD | - |

---

## Funnel Metrics

### Student Journey

```
Landing Page Visit
        ↓ (Target: 30% conversion)
Sign Up
        ↓ (Target: 50% conversion)
First Tutor Search
        ↓ (Target: 40% conversion)
First Booking Request
        ↓ (Target: 70% conversion)
First Completed Session
        ↓ (Target: 50% conversion)
Second Booking (Retention)
```

| Stage | Conversion Target | Current | Status |
|-------|-------------------|---------|--------|
| Visit → Sign Up | 30% | TBD | - |
| Sign Up → First Search | 50% | TBD | - |
| Search → First Booking | 40% | TBD | - |
| Booking → Completed | 70% | TBD | - |
| First → Second Session | 50% | TBD | - |

### Tutor Journey

```
Tutor Application
        ↓ (Target: 60% approval)
Profile Approved
        ↓ (Target: 80% completion)
Profile Complete
        ↓ (Target: 70% availability)
Availability Set
        ↓ (Target: 50% booking)
First Booking Received
        ↓ (Target: 90% confirmation)
First Session Completed
```

| Stage | Conversion Target | Current | Status |
|-------|-------------------|---------|--------|
| Apply → Approved | 60% | TBD | - |
| Approved → Profile Complete | 80% | TBD | - |
| Complete → Availability Set | 70% | TBD | - |
| Available → First Booking | 50% | TBD | - |
| Booking → First Session | 90% | TBD | - |

---

## Tracking Implementation

### Backend Events

Events tracked via audit logging (`backend/core/audit.py`):

```python
# User Events
USER_SIGNUP = "user.signup"
USER_LOGIN = "user.login"
USER_LOGOUT = "user.logout"

# Tutor Events
TUTOR_APPLICATION = "tutor.application"
TUTOR_APPROVED = "tutor.approved"
TUTOR_AVAILABILITY_SET = "tutor.availability_set"

# Booking Events
BOOKING_REQUESTED = "booking.requested"
BOOKING_CONFIRMED = "booking.confirmed"
BOOKING_COMPLETED = "booking.completed"
BOOKING_CANCELLED = "booking.cancelled"

# Payment Events
PAYMENT_INITIATED = "payment.initiated"
PAYMENT_COMPLETED = "payment.completed"
PAYMENT_REFUNDED = "payment.refunded"

# Package Events
PACKAGE_PURCHASED = "package.purchased"
PACKAGE_SESSION_USED = "package.session_used"
```

### Frontend Events

Events to track via analytics (e.g., Mixpanel, Amplitude):

```typescript
// Page Views
PAGE_VIEW_LANDING = "page.landing"
PAGE_VIEW_SEARCH = "page.search"
PAGE_VIEW_TUTOR_PROFILE = "page.tutor_profile"
PAGE_VIEW_BOOKING = "page.booking"

// User Actions
SEARCH_PERFORMED = "search.performed"
FILTER_APPLIED = "filter.applied"
TUTOR_FAVORITED = "tutor.favorited"
BOOKING_STARTED = "booking.started"
BOOKING_SUBMITTED = "booking.submitted"

// Engagement
MESSAGE_SENT = "message.sent"
REVIEW_SUBMITTED = "review.submitted"
```

### Database Queries

Key queries for metrics calculation:

```sql
-- Weekly Active Learners
SELECT COUNT(DISTINCT student_id)
FROM bookings
WHERE session_state = 'completed'
  AND completed_at >= NOW() - INTERVAL '7 days';

-- Booking Conversion Rate
SELECT
  COUNT(CASE WHEN session_state = 'confirmed' THEN 1 END)::float /
  COUNT(*) * 100 as conversion_rate
FROM bookings
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Average Session Value
SELECT AVG(price_amount)
FROM bookings
WHERE session_state = 'completed'
  AND payment_state = 'captured';
```

---

## Dashboards

### Owner Dashboard (Existing)

Location: `/owner` route

Displays:
- Revenue metrics (GMV, Net Revenue, Commission)
- Booking counts and completion rates
- Tutor performance metrics
- Growth trends

### Metrics Dashboard (To Build)

Location: `/admin/metrics` (proposed)

Should display:
- Real-time KPI tracking
- Funnel visualization
- Historical trends
- Alert thresholds

---

## Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | >0.5% | >1% | Page on-call |
| P95 Response Time | >500ms | >1000ms | Page on-call |
| Uptime (hourly) | <99.9% | <99% | Page on-call |
| Failed Payments | >5% | >10% | Alert finance |
| Booking Completion | <85% | <80% | Review UX |

---

## Reporting Cadence

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| Daily Standup Metrics | Daily | Engineering | Errors, performance, deployments |
| Weekly Business Review | Weekly | Leadership | KPIs, funnel, revenue |
| Monthly Metrics Deep Dive | Monthly | All Teams | Trends, insights, recommendations |
| Quarterly OKR Review | Quarterly | Company | Goal progress, adjustments |

---

## Related Documents

- [Project Status](./project_status.md) - Current progress
- [Launch Checklist](./LAUNCH_CHECKLIST.md) - Pre-launch verification
- [Architecture](./architecture.md) - System design
