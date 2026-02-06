# EduStream Master TODO Index

**Last Updated**: 2026-01-29
**Based On**: Architecture Docs + Product Vision Plan

## Quick Links

| Phase | Focus | Timeline | Status |
|-------|-------|----------|--------|
| [Phase 0](./TODO_PHASE_0_STABILIZATION.md) | Stabilization & Bug Fixes | Weeks 1-4 | 🔴 Not Started |
| [Phase 1](./TODO_PHASE_1_MVP_LAUNCH.md) | MVP Launch & User Acquisition | Weeks 5-12 | 🔴 Not Started |
| [Phase 2](./TODO_PHASE_2_SCALE.md) | V1 Scale & AI Matching | Weeks 13-26 | 🔴 Not Started |
| [Phase 3](./TODO_PHASE_3_EXPANSION.md) | Mobile & Expansion | Weeks 27-52 | 🔴 Not Started |
| [Technical Debt](./TODO_TECHNICAL_DEBT.md) | Ongoing Tech Debt Register | Continuous | 🟡 In Progress |

## Priority Legend

- 🔴 **P0 (Critical)**: Blocking launch or causing data loss
- 🟠 **P1 (High)**: Significant impact on user experience
- 🟡 **P2 (Medium)**: Important but not blocking
- 🟢 **P3 (Low)**: Nice to have, can defer

## Current Focus (90-Day Priority)

Based on the product vision: **Launch and acquire users + Operational stability**

### Week 1-4: Stabilization
- [ ] Fix all P0/P1 bugs
- [ ] Increase test coverage to 80%
- [ ] Load test for 100 concurrent users
- [ ] Set up error monitoring (Sentry)
- [ ] Document runbooks

### Week 5-8: Launch Prep
- [ ] Recruit 500 tutors
- [ ] Optimize landing page
- [ ] Implement SEO fundamentals
- [ ] Set up email automation
- [ ] Configure analytics pipeline

### Week 9-13: Growth
- [ ] Soft launch to beta users
- [ ] Launch referral program
- [ ] A/B test checkout flow
- [ ] Address top user feedback

## Success Metrics

| Metric | Phase 0 | Phase 1 | Phase 2 |
|--------|---------|---------|---------|
| Test Coverage | 80% | 80% | 85% |
| Uptime | 99% | 99.5% | 99.9% |
| Active Tutors | - | 500 | 5,000 |
| Active Students | - | 2,000 | 20,000 |
| GMV | - | $50K | $500K |

## Architecture Gaps to Address

From `docs/architecture/09-future-evolution.md`:

### High Priority Tech Debt
1. **API Versioning** - No version prefix on endpoints
2. **APScheduler** - In-process, jobs lost on restart
3. **Single-region** - No failover capability
4. **Test Coverage** - Some modules untested

### Medium Priority Tech Debt
1. **Feature Flags** - All-or-nothing releases
2. **Distributed Tracing** - No OpenTelemetry
3. **Frontend Cache** - Manual invalidation
4. **Alembic Migration** - Manual SQL files

## File Organization

```
docs/
├── TODO_MASTER.md              # This file - index
├── TODO_PHASE_0_STABILIZATION.md   # Immediate fixes
├── TODO_PHASE_1_MVP_LAUNCH.md      # Launch readiness
├── TODO_PHASE_2_SCALE.md           # Growth features
├── TODO_PHASE_3_EXPANSION.md       # Advanced features
├── TODO_TECHNICAL_DEBT.md          # Ongoing debt register
├── PRODUCT_VISION_AND_PLAN.md      # Full product vision
└── architecture/                    # System architecture docs
    ├── 01-business-context.md
    ├── ...
    └── 09-future-evolution.md
```
