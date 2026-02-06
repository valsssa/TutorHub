# Business Context & Requirements

## 1. Core Problem Statement

EduStream addresses the **fragmented tutoring discovery and transaction problem**:

- Students struggle to find qualified tutors matching their needs
- Scheduling sessions across timezones is error-prone
- Payment handling lacks trust and security
- Quality assurance is inconsistent across platforms

## 2. Solution Overview

A two-sided marketplace that provides:

- Tutor discovery with search, filtering, and quality signals
- Session booking with conflict resolution and state management
- Secure payment facilitation via Stripe Connect
- Real-time communication (WebSocket messaging)
- Quality assurance through reviews and tutor vetting

## 3. Target Users & Workflows

### 3.1 Student (Primary User)

**Critical Workflows**:
1. Search tutors by subject, availability, price, rating
2. Book session with package or pay-per-session
3. Attend session via integrated video link
4. Leave review after completion

**Success Metrics**:
- Time to first booking
- Repeat booking rate
- Session completion rate

### 3.2 Tutor (Supply Side)

**Critical Workflows**:
1. Create and submit profile for approval
2. Set availability and pricing
3. Accept/decline booking requests
4. Conduct sessions and track earnings

**Success Metrics**:
- Profile approval time
- Request-to-confirmation rate
- Average response time
- Monthly earnings

### 3.3 Admin (Platform Operations)

**Critical Workflows**:
1. Review and approve tutor applications
2. Handle disputes and complaints
3. Monitor platform health metrics
4. Manage user accounts

**Success Metrics**:
- Tutor approval turnaround time
- Dispute resolution time
- Platform uptime

### 3.4 Owner (Business Analytics)

**Critical Workflows**:
1. View revenue and growth dashboards
2. Monitor marketplace health
3. Adjust commission tiers
4. Track key performance indicators

**Success Metrics**:
- Gross Merchandise Value (GMV)
- Platform take rate
- User growth rates

## 4. Business Model

### Revenue Model

Platform commission on each transaction (tiered based on tutor lifetime earnings):

| Tier | Lifetime Revenue | Platform Fee |
|------|------------------|--------------|
| Starter | $0 - $999 | 20% |
| Growth | $1,000 - $4,999 | 15% |
| Pro | $5,000+ | 10% |

### Unit Economics

- Average session value: $40-80
- Average platform fee: $8-12 per session
- Target sessions per tutor: 20+/month

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target | Current |
|--------|--------|---------|
| API Response P50 | < 100ms | ~80ms |
| API Response P95 | < 300ms | ~200ms |
| Page Load Time | < 2s | ~1.5s |
| WebSocket Latency | < 100ms | ~50ms |

### 5.2 Availability

| Metric | Target | Current |
|--------|--------|---------|
| Uptime | 99.5% | 99%+ (limited data) |
| Planned Maintenance | < 1hr/month | As needed |
| Recovery Time | < 15min | Manual intervention |

### 5.3 Scalability

| Metric | Current | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| Concurrent Users | 100 | 1,000 | 10,000 |
| Monthly Active Users | 500 | 5,000 | 50,000 |
| Sessions/Month | 1,000 | 10,000 | 100,000 |

### 5.4 Security

- PCI DSS compliance via Stripe delegation
- GDPR-compatible data handling
- OWASP Top 10 protection
- Role-based access control
- Audit logging for sensitive operations

### 5.5 Data Retention

| Data Type | Retention | Justification |
|-----------|-----------|---------------|
| Financial records | 7 years | Tax/legal compliance |
| User accounts | Until deletion request | GDPR compliance |
| Session logs | 2 years | Dispute resolution |
| Audit logs | 5 years | Security/compliance |

## 6. Constraints & Assumptions

### Technical Constraints

- Must run on Docker-based infrastructure
- PostgreSQL as primary database (existing investment)
- Python/TypeScript expertise in team
- Limited DevOps resources (single engineer operations)

### Business Constraints

- MVP budget constraints
- Time to market priority
- Small initial team (< 5 engineers)
- US-first launch (Stripe availability)

### Assumptions

- Users have stable internet for video sessions
- Tutors can manage their own schedules
- Email is primary communication channel
- Desktop-first usage (mobile secondary)

## 7. Success Criteria

### MVP Launch (Current Phase)

- [ ] 100+ registered tutors
- [ ] 50+ completed sessions
- [ ] < 5% cancellation rate
- [ ] Zero payment failures
- [ ] 4.0+ average platform rating

### Growth Phase (6 months)

- [ ] 1,000+ monthly active users
- [ ] $50,000+ monthly GMV
- [ ] < 3% cancellation rate
- [ ] 95%+ session completion rate
- [ ] Mobile app launched

### Scale Phase (18 months)

- [ ] 10,000+ monthly active users
- [ ] $500,000+ monthly GMV
- [ ] Multi-region deployment
- [ ] Group sessions feature
- [ ] AI-powered matching
