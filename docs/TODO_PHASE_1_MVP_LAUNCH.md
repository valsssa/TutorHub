# Phase 1: MVP Launch & User Acquisition

**Timeline**: Weeks 5-12
**Goal**: Launch to first users, acquire 500 tutors and 2000 students, process $50K GMV
**Dependencies**: Phase 0 complete

---

## Week 5-6: Tutor Recruitment & Supply

### 🔴 P0 - Critical

- [ ] **Launch tutor recruitment campaign**
  - Create landing page for tutors
  - Set up paid ads (LinkedIn, Facebook)
  - Outreach to tutoring communities
  - Target: 500 tutors by Week 8
  - Files: New marketing pages

- [ ] **Improve tutor onboarding flow**
  - Streamline profile creation (target: <10 min)
  - Add progress indicators
  - Implement draft saving
  - Files: `frontend/app/tutor/onboarding/`, `frontend/app/tutor/profile/`

- [ ] **Create tutor onboarding content**
  - Welcome email sequence (3 emails)
  - Video tutorials for profile setup
  - Best practices guide
  - Create: `docs/TUTOR_GUIDE.md`

### 🟠 P1 - High Priority

- [ ] **Set up tutor support channel**
  - Dedicated Slack/Discord for tutors
  - FAQ for common questions
  - Office hours schedule
  - Document process

- [ ] **Implement tutor referral bonus**
  - $25 for referring another tutor
  - Tracking infrastructure
  - Files: New referral module

- [ ] **Optimize tutor approval workflow**
  - Admin notification on new submissions
  - Approval checklist
  - Target: <24hr approval time
  - Files: `backend/modules/admin/`

### 🟡 P2 - Medium Priority

- [ ] **Add tutor success metrics dashboard**
  - Response time tracking
  - Booking acceptance rate
  - Earnings history
  - Files: `frontend/app/tutor/earnings/`

---

## Week 6-7: Landing Page & SEO

### 🔴 P0 - Critical

- [ ] **Optimize landing page for conversion**
  - A/B test hero copy
  - Add testimonials/social proof
  - Improve CTA visibility
  - Target: 3% visitor-to-signup conversion
  - Files: `frontend/app/page.tsx`

- [ ] **Implement SEO fundamentals**
  - Meta tags for all pages
  - Structured data (JSON-LD)
  - Sitemap generation
  - robots.txt optimization
  - Files: `frontend/app/layout.tsx`, `frontend/public/`

- [ ] **Create subject-specific landing pages**
  - Top 10 subjects (Math, Science, English, etc.)
  - Subject-specific copy
  - Tutor showcase per subject
  - Target keywords: "[subject] tutoring online"
  - Create: `frontend/app/subjects/[subject]/`

### 🟠 P1 - High Priority

- [ ] **Set up Google Search Console**
  - Verify domain
  - Submit sitemap
  - Monitor indexing
  - Track search performance

- [ ] **Set up Google Analytics 4**
  - Event tracking setup
  - Conversion goals
  - Funnel visualization
  - Files: `frontend/lib/analytics.ts`

- [ ] **Create blog/content section**
  - SEO-focused articles
  - Study tips content
  - Subject guides
  - Create: `frontend/app/blog/`

### 🟡 P2 - Medium Priority

- [ ] **Implement city-specific pages**
  - "[City] tutoring" targeting
  - Local SEO optimization
  - Create: `frontend/app/locations/[city]/`

---

## Week 7-8: Email Automation & Notifications

### 🔴 P0 - Critical

- [ ] **Implement welcome email sequence (3 emails)**
  - Day 0: Welcome + getting started
  - Day 2: Feature highlights
  - Day 5: Book first session CTA
  - Files: `backend/modules/notifications/`, Brevo templates

- [ ] **Implement booking reminder emails**
  - 24h before session
  - 1h before session
  - Include join link prominently
  - Files: `backend/modules/notifications/service.py`

- [ ] **Implement post-session follow-up**
  - Review request
  - Rebook suggestion
  - Tutor recommendation
  - Files: `backend/modules/notifications/`

### 🟠 P1 - High Priority

- [ ] **Set up transactional email templates**
  - Booking confirmed
  - Booking cancelled
  - Payment receipt
  - Payout notification
  - Files: Brevo templates

- [ ] **Implement winback email sequence**
  - Day 7: Soft touch
  - Day 14: Incentive ($10 credit)
  - Day 30: Final push
  - Files: `backend/modules/notifications/`

- [ ] **Add email preference management**
  - Unsubscribe handling
  - Frequency preferences
  - Category opt-outs
  - Files: `frontend/app/settings/notifications/`

### 🟡 P2 - Medium Priority

- [ ] **Implement tutor-specific notifications**
  - New booking request alert
  - Earnings milestone
  - Profile views weekly digest
  - Files: `backend/modules/notifications/`

---

## Week 8: Analytics Pipeline Setup

### 🔴 P0 - Critical

- [ ] **Implement event tracking**
  - User events (signup, login, profile update)
  - Search events (query, filters, results)
  - Booking events (initiated, completed, cancelled)
  - Payment events (success, failure)
  - Files: `frontend/lib/analytics.ts`, `backend/core/events.py`

- [ ] **Set up funnel dashboards**
  - Acquisition funnel
  - Activation funnel
  - Booking funnel
  - Tool: Metabase/Looker

- [ ] **Configure alerting**
  - Error rate alerts
  - Payment failure alerts
  - Conversion drop alerts
  - Tool: Grafana/PagerDuty

### 🟠 P1 - High Priority

- [ ] **Create weekly report template**
  - Key metrics summary
  - Funnel performance
  - Top issues
  - Create: `docs/WEEKLY_REPORT_TEMPLATE.md`

- [ ] **Set up cohort tracking**
  - Weekly signup cohorts
  - Retention by cohort
  - LTV by acquisition channel

### 🟡 P2 - Medium Priority

- [ ] **Implement UTM tracking**
  - Campaign attribution
  - Source tracking
  - Files: `frontend/lib/analytics.ts`

---

## Week 9-10: Soft Launch

### 🔴 P0 - Critical

- [ ] **Launch to beta users (500)**
  - Invite via email
  - Monitor metrics daily
  - Set up feedback channel
  - Rapid bug triage

- [ ] **Set up daily monitoring routine**
  - Check error rates
  - Review user feedback
  - Monitor payment success
  - Track conversion rates

- [ ] **Rapid bug fix process**
  - Triage within 2 hours
  - P0 fix within 24 hours
  - Daily hotfix deploy if needed

### 🟠 P1 - High Priority

- [ ] **Gather user feedback**
  - In-app feedback widget
  - Post-booking survey
  - NPS survey (Day 7)
  - Files: New feedback components

- [ ] **Set up user interviews**
  - Schedule 5-10 user calls
  - Document insights
  - Prioritize feedback

- [ ] **Monitor and fix top complaints**
  - Track issue frequency
  - Prioritize by impact
  - Quick iterations

### 🟡 P2 - Medium Priority

- [ ] **A/B test onboarding variants**
  - Test different welcome flows
  - Test CTA copy
  - Measure activation rate

---

## Week 10-11: Marketing Push

### 🔴 P0 - Critical

- [ ] **Launch social media campaigns**
  - Paid ads (Facebook, Instagram)
  - Target: Students, Parents
  - Budget: Defined per channel
  - Track CAC

- [ ] **Begin content marketing**
  - Publish 2 blog posts/week
  - Social media content
  - Video content (YouTube, TikTok)

### 🟠 P1 - High Priority

- [ ] **Influencer outreach**
  - Identify education influencers
  - Partnership proposals
  - Track referral codes

- [ ] **PR for launch**
  - Press release
  - Media kit
  - Journalist outreach

- [ ] **Community building**
  - Student communities (Reddit, Discord)
  - Parent groups
  - Education forums

### 🟡 P2 - Medium Priority

- [ ] **Partnership outreach**
  - Schools and universities
  - Learning centers
  - Corporate training

---

## Week 11-12: Referral Program

### 🔴 P0 - Critical

- [ ] **Implement basic referral system**
  - Unique referral codes
  - $10 credit for referrer
  - $10 credit for referee
  - Files: New `backend/modules/referrals/`

- [ ] **Referral tracking infrastructure**
  - Attribution tracking
  - Fraud detection
  - Payout management
  - Files: Database schema, API endpoints

- [ ] **Referral UI**
  - Share referral link
  - Track referrals
  - View rewards
  - Files: `frontend/app/referral/`

### 🟠 P1 - High Priority

- [ ] **Referral email campaign**
  - Announce program to existing users
  - Reminder emails
  - Success stories

- [ ] **Social sharing integration**
  - One-click share to social
  - Pre-filled messages
  - Files: `frontend/components/`

### 🟡 P2 - Medium Priority

- [ ] **Referral leaderboard**
  - Top referrers display
  - Monthly rewards
  - Gamification

---

## Week 12: Optimization & Review

### 🔴 P0 - Critical

- [ ] **Analyze funnel drop-offs**
  - Identify biggest leaks
  - Prioritize fixes
  - A/B test solutions

- [ ] **A/B test checkout flow**
  - Payment method options
  - Pricing display
  - Trust signals
  - Files: `frontend/components/ModernBookingModal.tsx`

### 🟠 P1 - High Priority

- [ ] **Optimize tutor search ranking**
  - Factor in response time
  - Factor in completion rate
  - Boost new tutors initially
  - Files: `backend/modules/tutors/`

- [ ] **Address top user complaints**
  - Compile feedback
  - Prioritize by frequency
  - Ship fixes

- [ ] **Compile Phase 1 learnings**
  - What worked
  - What didn't
  - Recommendations for Phase 2
  - Create: `docs/PHASE_1_RETROSPECTIVE.md`

### 🟡 P2 - Medium Priority

- [ ] **Plan Phase 2 priorities**
  - AI matching requirements
  - Scale infrastructure needs
  - Team hiring needs

---

## Definition of Done (Phase 1)

- [ ] 500 active tutors
- [ ] 2,000 registered students
- [ ] $50K GMV processed
- [ ] <2% error rate
- [ ] NPS >30
- [ ] 85%+ session completion rate
- [ ] <5% cancellation rate
- [ ] Referral program launched
- [ ] Email automation active
- [ ] Analytics tracking complete

---

## New Files to Create

| File | Purpose |
|------|---------|
| `docs/TUTOR_GUIDE.md` | Tutor onboarding content |
| `frontend/app/subjects/[subject]/` | Subject landing pages |
| `frontend/app/blog/` | Blog/content section |
| `frontend/app/locations/[city]/` | City landing pages |
| `frontend/lib/analytics.ts` | Analytics tracking |
| `docs/WEEKLY_REPORT_TEMPLATE.md` | Report template |
| `backend/modules/referrals/` | Referral system |
| `frontend/app/referral/` | Referral UI |
| `docs/PHASE_1_RETROSPECTIVE.md` | Phase 1 learnings |

---

## Related Architecture Docs

- [Business Context](./architecture/01-business-context.md) - Success criteria
- [Scalability & Operations](./architecture/08-scalability-operations.md) - Monitoring setup
- [Future Evolution](./architecture/09-future-evolution.md) - Referral program prep
