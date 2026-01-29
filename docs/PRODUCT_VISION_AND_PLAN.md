# EduStream: Complete Product Vision & Implementation Plan

**Document Version**: 1.0
**Created**: January 2026
**Status**: Strategic Blueprint

---

## Table of Contents

1. [Vision & North Star](#1-vision--north-star)
2. [Product Strategy](#2-product-strategy)
3. [Product Scope](#3-product-scope)
4. [End-to-End User Journeys](#4-end-to-end-user-journeys)
5. [System Design](#5-system-design)
6. [UX/UI Direction](#6-uxui-direction)
7. [Engineering Execution Plan](#7-engineering-execution-plan)
8. [Team & Operations](#8-team--operations)
9. [Quality Plan](#9-quality-plan)
10. [Analytics & Experimentation](#10-analytics--experimentation)
11. [Risks & Hard Problems](#11-risks--hard-problems)
12. [Final Deliverables](#12-final-deliverables)

---

## 1. Vision & North Star

### One-Sentence Vision

**EduStream democratizes access to quality education by connecting learners worldwide with affordable, vetted tutors—making personalized learning accessible to everyone regardless of geography or income.**

### 10-Year North Star Narrative

By 2036, EduStream is the world's largest tutoring marketplace, facilitating over 100 million tutoring sessions annually across 150+ countries. We've fundamentally changed how people access education:

- A student in rural Nebraska learns Mandarin from a native speaker in Beijing
- A parent in Lagos finds an affordable math tutor from India for their child
- A professional in London upskills with a Silicon Valley engineer
- A retiree in Melbourne teaches history to curious minds worldwide

The platform has become the "Airbnb of tutoring"—a trusted, global network where knowledge flows freely across borders, creating economic opportunity for tutors in emerging markets while providing affordable, quality education to learners everywhere.

### Success Metrics (3 Measurable Outcomes)

| Metric | Year 1 | Year 3 | Year 10 |
|--------|--------|--------|---------|
| **Annual GMV** | $5M | $100M | $10B |
| **Active Tutors** | 5,000 | 100,000 | 5M |
| **Session Completion Rate** | 85% | 92% | 95% |

---

## 2. Product Strategy

### 2.1 Target Personas (Jobs-to-be-Done)

#### Persona 1: Sarah, the Overwhelmed Parent (K-12)
- **Demographics**: 38, suburban US, household income $85K, two kids (ages 10, 14)
- **Job**: "Help my kids succeed academically without breaking the bank or driving across town"
- **Pain Points**:
  - Local tutoring is $60-100/hour
  - Kids have different schedules and subjects
  - Can't verify tutor quality
- **Success Criteria**: Affordable tutoring (<$30/hr), schedule flexibility, visible progress
- **Platform Behavior**: Books via mobile, monitors progress, manages both kids' accounts

#### Persona 2: Marcus, the Ambitious University Student
- **Demographics**: 21, UK university, limited budget, studying Computer Science
- **Job**: "Pass my exams and build skills that get me hired"
- **Pain Points**:
  - University tutoring is scarce and expensive
  - Peers can't explain concepts well
  - Needs flexible scheduling around classes
- **Success Criteria**: Affordable rates, instant availability, practical career advice
- **Platform Behavior**: Books same-day sessions, uses packages for cost savings, leaves detailed reviews

#### Persona 3: Priya, the Career Changer
- **Demographics**: 34, India-based, transitioning from finance to data science
- **Job**: "Learn practical skills from industry professionals who've done what I want to do"
- **Pain Points**:
  - MOOCs feel impersonal
  - Bootcamps are expensive and time-consuming
  - Needs guidance, not just content
- **Success Criteria**: Learn from practitioners, flexible pacing, portfolio-ready projects
- **Platform Behavior**: Long-term relationship with 2-3 tutors, weekly sessions, career mentorship

#### Persona 4: David, the Emerging Market Tutor
- **Demographics**: 28, Philippines, former teacher, excellent English, $800/month local salary
- **Job**: "Earn a living wage teaching what I love to students who value my expertise"
- **Pain Points**:
  - Local tutoring pays $5/hour
  - No access to wealthy students
  - Platform fees on competitors are 30%+
- **Success Criteria**: $20-40/hour rates, steady bookings, low platform fees
- **Platform Behavior**: Optimizes profile, responds quickly, builds long-term student relationships

#### Persona 5: Jennifer, the Premium Tutor
- **Demographics**: 45, US-based, PhD in Mathematics, 20 years teaching experience
- **Job**: "Maximize my earnings while controlling my schedule"
- **Pain Points**:
  - Wyzant takes 25% of every session
  - Administrative burden of scheduling
  - Inconsistent student quality
- **Success Criteria**: Higher take-home earnings, premium positioning, quality students
- **Platform Behavior**: Charges premium rates, offers packages, auto-confirms trusted students

#### Persona 6: Chen, the Institution Administrator
- **Demographics**: 52, corporate L&D director at Fortune 500, manages training budget
- **Job**: "Provide personalized learning to employees without building internal infrastructure"
- **Pain Points**:
  - Generic training doesn't work
  - Building tutoring programs is expensive
  - Need reporting and compliance
- **Success Criteria**: Measurable skill improvement, easy administration, cost efficiency
- **Platform Behavior**: (Future) Enterprise dashboard, bulk purchases, SSO integration

### 2.2 Value Propositions per Persona

| Persona | Primary Value Prop | Secondary Value Props |
|---------|-------------------|----------------------|
| **Sarah (Parent)** | Affordable quality tutoring from $15/hr | Schedule flexibility, progress tracking, verified tutors |
| **Marcus (Student)** | Instant access to expert help | Package discounts, peer recommendations, 24/7 availability |
| **Priya (Career Changer)** | Learn from industry practitioners | Mentorship beyond tutoring, flexible pacing |
| **David (EM Tutor)** | 3-4x local rates, global market access | Low 10-20% fees, instant payouts, profile visibility |
| **Jennifer (Premium Tutor)** | Lower fees than competitors | Quality students, scheduling control, reputation building |
| **Chen (Enterprise)** | Personalized L&D at scale | Reporting, compliance, vendor consolidation |

### 2.3 Competitive Advantage Moat

**Primary Moat: Pricing Arbitrage + Network Effects**

1. **Supply-Side Cost Advantage**
   - Recruit excellent tutors from emerging markets (Philippines, India, Eastern Europe, Latin America)
   - These tutors earn 3-4x local wages at rates 50% below US tutors
   - Lower operational costs = sustainable low pricing

2. **Commission Structure Lock-In**
   - 20% → 15% → 10% tiered commission rewards loyal tutors
   - Competitors charge 25-33% flat
   - Tutors optimize for EduStream as their primary platform

3. **Cross-Border Network Effects**
   - More EM tutors → lower prices → more students → more demand for EM tutors
   - Geographic diversity = 24/7 availability
   - Language diversity = native speakers for language learning

4. **Data Moat (Future)**
   - Session recordings for quality assurance
   - Learning outcome tracking for AI matching
   - Tutor performance data for recommendations

**Secondary Moats:**
- **Brand**: "The affordable tutoring platform"
- **Workflow Lock-In**: Packages, long-term relationships, progress history
- **Distribution**: SEO for "affordable [subject] tutoring," affiliate partnerships with schools

### 2.4 Positioning Statement

> **For students and parents seeking quality education support**, EduStream is the **global tutoring marketplace** that **connects learners with affordable, vetted tutors worldwide**. Unlike **Wyzant and Preply** who charge premium rates and high fees, we **leverage global talent to offer quality tutoring at half the price** while paying tutors more through our **lower commission structure**.

### 2.5 Pricing & Packaging

#### Commission Model (Current)
| Tutor Lifetime Earnings | Platform Fee | Tutor Keeps |
|------------------------|--------------|-------------|
| $0 - $999 | 20% | 80% |
| $1,000 - $4,999 | 15% | 85% |
| $5,000+ | 10% | 90% |

**Rationale**:
- New tutors subsidize platform growth (20%)
- Successful tutors get rewarded for loyalty (10%)
- Still lower than Wyzant (25%) and Preply (33%) at all tiers

#### Student-Side Pricing
- **Pay-per-session**: Tutor sets rate, student pays session + platform fee
- **Packages**: 5/10/20 session bundles with 5-15% discount, optional expiration
- **Wallet Credits**: Pre-loaded balance for faster checkout

#### Future Monetization Options (Not for Launch)
- **Tutor Boost**: $20/month for homepage visibility, analytics, badges
- **Enterprise Tier**: Custom pricing for B2B contracts
- **Featured Listings**: Sponsored placement in search results

---

## 3. Product Scope

### 3.1 Feature Map: Everything We Would Build

#### CORE PLATFORM FEATURES

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **Tutor Search & Discovery** | As a student, I can find tutors matching my subject, budget, schedule, and preferences | Search-to-booking conversion >5% | Full-text search, availability indexing | Filter complexity, slow queries |
| **Booking Flow** | As a student, I can book a session with clear pricing and instant confirmation | Booking completion rate >70% | Availability, payments | Timezone confusion, payment failures |
| **4-Field Booking State Machine** | As a platform, I can track session lifecycle, outcome, payment, and disputes independently | Dispute resolution <48hrs | APScheduler, PostgreSQL | State inconsistency, edge cases |
| **Tutor Profile Management** | As a tutor, I can showcase my expertise with subjects, education, certifications, and pricing | Profile completion >80% for active tutors | MinIO (files), verification workflow | Incomplete profiles, fake credentials |
| **Availability System** | As a tutor, I can set recurring availability and blackout periods | Double-booking rate <0.1% | Timezone handling, conflict detection | Timezone bugs, availability drift |
| **Package System** | As a student, I can purchase session bundles with volume discounts | Package adoption >30% of revenue | Expiration tracking, session counting | Unused session disputes |
| **Real-time Messaging** | As a user, I can communicate with counterparties before/after sessions | Message response rate <4hrs | WebSocket, Redis pub/sub | Spam, inappropriate content |
| **Review System** | As a student, I can review completed sessions | Review submission rate >40% | Booking completion trigger | Fake reviews, retaliation |
| **Payment Processing** | As a platform, I can process payments, hold funds, and release to tutors | Payment success rate >98% | Stripe integration | Chargebacks, fraud |
| **Tutor Payouts** | As a tutor, I can withdraw earnings to my bank account | Payout delivery <3 business days | Stripe Connect | Compliance, failed transfers |
| **Notification System** | As a user, I receive timely alerts about bookings, messages, and reminders | Email open rate >25% | Brevo integration, scheduling | Email deliverability, spam |
| **Admin Dashboard** | As an admin, I can manage users, resolve disputes, and monitor platform health | Dispute resolution <24hrs | RBAC, audit logging | Admin abuse, data access |

#### GROWTH FEATURES

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **AI Tutor Matching** | As a student, I get personalized tutor recommendations based on my goals | Matched booking conversion +20% vs search | ML pipeline, user profiles, session data | Cold start, filter bubbles |
| **Referral Program** | As a user, I can earn credits by referring friends | Referred user activation >40% | Referral tracking, fraud detection | Referral fraud, gaming |
| **SEO Landing Pages** | As a platform, I rank for "[subject] tutoring" searches | Organic traffic +50% YoY | Content generation, keyword research | Algorithm changes |
| **Affiliate Program** | As a partner, I can earn commission driving users to EduStream | Affiliate revenue >10% of new users | Attribution tracking, payout system | Fraud, brand misuse |
| **Tutor Onboarding Funnel** | As a platform, I convert tutor signups to active tutors | Tutor activation >50% | Profile wizard, verification | High drop-off, low quality |
| **Student Activation Flow** | As a platform, I convert signups to first booking | First booking within 7 days >30% | Onboarding emails, incentives | Low intent, price sensitivity |
| **Social Proof Widgets** | As a marketing channel, I display reviews/stats on partner sites | Widget click-through >2% | Public API, embeddable components | Performance, brand control |

#### RETENTION FEATURES

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **Favorite Tutors** | As a student, I can save and quickly rebook my preferred tutors | Repeat booking rate >60% | User preferences | Limited discovery |
| **Progress Tracking** | As a student, I can see my learning journey and goals | Goal completion >40% | Session notes, milestones | Tutor adoption, data entry |
| **Session Notes (Tutor)** | As a tutor, I can track student progress and preferences privately | Notes usage >70% of active tutors | Secure storage | Privacy concerns |
| **Rebooking Nudges** | As a platform, I remind students to continue their learning | Nudge-to-booking conversion >10% | Notification scheduling | Notification fatigue |
| **Package Expiration Alerts** | As a student, I'm reminded to use sessions before they expire | Unused session rate <10% | Expiration tracking | User frustration |
| **Learning Streaks** | As a student, I'm motivated by maintaining consistent learning | Weekly active rate +15% | Gamification logic | Gimmicky perception |
| **Tutor Badges/Achievements** | As a tutor, I earn recognition for quality and milestones | Badge display rate >80% of profiles | Achievement logic | Badge inflation |

#### TRUST & SAFETY / MODERATION

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **Tutor Verification** | As a platform, I verify tutor identity and credentials | Verified tutor rate >90% | Document upload, manual review | Verification backlog, false docs |
| **Background Checks** | As a platform, I screen tutors for safety (K-12 focus) | Background check pass rate >99% | Third-party provider (Checkr) | Cost, international coverage |
| **Content Moderation** | As a platform, I detect and remove harmful content | Harmful content removal <1hr | AI moderation, human review | False positives, scale |
| **Dispute Resolution** | As a platform, I fairly resolve student-tutor conflicts | Student satisfaction >80% on disputes | Dispute workflow, evidence collection | Bias, complexity |
| **Fraud Detection** | As a platform, I detect fake reviews, payment fraud, account abuse | Fraud loss <0.5% of GMV | ML models, rule engine | False positives |
| **Report System** | As a user, I can report concerning behavior | Report response <24hrs | Report queue, prioritization | Abuse of reporting |
| **Session Recording (Opt-in)** | As a platform, I enable recording for quality/safety | Recording adoption >30% | Cloud storage, consent flow | Privacy laws, storage costs |

#### ADMIN & OPERATIONS TOOLING

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **User Management Console** | As an admin, I can search, view, edit, and suspend users | Admin task completion <5min | Search, audit logging | Data exposure |
| **Booking Operations** | As an admin, I can view, modify, and resolve booking issues | Manual intervention <1% of bookings | Override permissions | Misuse |
| **Financial Dashboard** | As finance, I can track revenue, payouts, and reconciliation | Reconciliation accuracy 100% | Accounting integration | Errors |
| **Tutor Approval Queue** | As an admin, I can review and approve tutor applications | Approval time <24hrs | Review workflow | Backlog |
| **Support Ticket System** | As support, I can manage customer inquiries | First response <4hrs | Ticketing integration (Zendesk) | Volume spikes |
| **Audit Log Viewer** | As compliance, I can review all admin actions | Audit completeness 100% | Immutable logging | Performance |

#### ANALYTICS & EXPERIMENTATION PLATFORM

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **Event Tracking Pipeline** | As product, I can track all user actions | Event coverage >95% of features | Event taxonomy, data warehouse | Data quality |
| **Funnel Analytics** | As product, I can visualize conversion funnels | Insight-to-action <1 week | BI tooling (Metabase/Looker) | Dashboard sprawl |
| **A/B Testing Framework** | As product, I can run controlled experiments | Experiment velocity >2/week | Feature flags, stats engine | Under-powered tests |
| **Real-time Dashboards** | As ops, I can monitor platform health live | Alert-to-response <15min | Grafana, Prometheus | Alert fatigue |
| **Cohort Analysis** | As growth, I can track retention by acquisition cohort | Cohort retention insights monthly | Data modeling | Attribution complexity |

#### INTEGRATIONS ECOSYSTEM

| Feature | User Story | Success Metric | Dependencies | Risks |
|---------|------------|----------------|--------------|-------|
| **Google Calendar Sync** | As a user, I see sessions in my calendar automatically | Calendar sync adoption >60% | OAuth, Calendar API | Token expiration |
| **Zoom Integration** | As a user, I join sessions via Zoom seamlessly | Video session join rate >95% | Zoom API | Rate limits, API changes |
| **Stripe Connect** | As a tutor, I receive payouts to my bank account | Payout success rate >99% | Stripe Connect | Compliance |
| **Google Meet/Teams** | As a user, I can choose my preferred video platform | Platform coverage >90% of users | Additional OAuth flows | Integration maintenance |
| **LMS Integrations** | As an institution, I connect EduStream to our LMS | (Future) Enterprise sales | LTI, custom APIs | Complexity |
| **Public API** | As a developer, I can build on EduStream | (Future) Ecosystem growth | API versioning, rate limits | Security |

---

### 3.2 What Already Exists (Current State)

#### Fully Implemented
- Core booking flow with 4-field state machine
- Tutor profiles with subjects, education, certifications, pricing options
- Availability and blackout management
- Package system with expiration
- Real-time WebSocket messaging with attachments
- Review system with rating aggregation
- Stripe payments and Connect payouts
- Commission tiers (20%/15%/10%)
- Admin and Owner dashboards
- Google Calendar and Zoom integrations
- Email notifications (Brevo)
- Rate limiting and security headers
- Soft delete and audit logging

#### Partially Implemented
- Multi-currency (DB ready, UI limited)
- Localization (structure ready, translations missing)
- Search (full-text on tutor profiles, basic filters)

#### Not Yet Built
- AI tutor matching
- Parent dashboard for K-12
- Mobile apps
- Referral program
- Background checks
- Session recording
- A/B testing framework

---

## 4. End-to-End User Journeys

### 4.1 Journey 1: New User Onboarding (Student)

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Landing Page (/)
├─ Hero: "Quality tutoring from $15/hr"
├─ Search bar with subject autocomplete
├─ Featured tutors carousel
└─ [Sign Up] / [Browse Tutors]
                                     → page_view: landing

Registration (/register)
├─ Email/password OR Google OAuth
├─ First name, last name
├─ Role selection (Student)
├─ Timezone auto-detection
└─ [Create Account]
                                     → user_registered {method, role}
                                     → email_sent: welcome

Email Verification
├─ Check inbox prompt
├─ Verification link
└─ Success confirmation
                                     → email_verified

Profile Setup (/settings/account)
├─ Avatar upload (optional)
├─ Bio (optional)
├─ Learning goals (optional)
├─ Preferred subjects (optional)
└─ [Save & Continue]
                                     → profile_updated {fields}

First Session CTA
├─ "Book your first session" banner
├─ Recommended tutors based on goals
└─ $5 credit for first booking
                                     → onboarding_cta_shown

Dashboard (/dashboard)
├─ Empty state: "Find your first tutor"
├─ Quick search by subject
├─ Suggested tutors
└─ Upcoming sessions (empty)
                                     → dashboard_viewed {is_new_user: true}
```

**Activation Criteria**: User completes first booking within 7 days

---

### 4.2 Journey 2: Activation (First "Aha Moment")

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Tutor Search (/tutors)
├─ Subject filter (required)
├─ Price range slider ($10-$100/hr)
├─ Availability filter (day/time)
├─ Rating filter (4+, 4.5+)
├─ Language filter
├─ Sort: Rating / Price / Experience
└─ Tutor cards with:
    ├─ Photo, name, headline
    ├─ Subjects, rating, reviews count
    ├─ Hourly rate, response time
    └─ [View Profile]
                                     → search_performed {filters, results_count}

Tutor Profile (/tutors/[id])
├─ Full bio and video intro
├─ Education and certifications
├─ Subject expertise with proficiency
├─ Pricing options (hourly/packages)
├─ Availability calendar preview
├─ Reviews with ratings breakdown
├─ [Book Session] CTA (sticky)
└─ [Message] option
                                     → tutor_profile_viewed {tutor_id}

Booking Modal
├─ Step 1: Select pricing option
│   ├─ Single session
│   └─ Package (5/10/20 sessions)
├─ Step 2: Select date & time slot
│   ├─ Calendar week view
│   └─ Available slots highlighted
├─ Step 3: Session details
│   ├─ Topic/subject
│   └─ Goals for session (optional)
├─ Step 4: Payment
│   ├─ Card details (Stripe Elements)
│   ├─ Promo code field
│   └─ Price breakdown (rate + fee)
└─ [Confirm Booking]
                                     → booking_initiated {tutor_id, pricing}
                                     → checkout_started {amount}

Confirmation Screen
├─ "Booking Request Sent!"
├─ Session details summary
├─ "Tutor will confirm within 24hrs"
├─ Calendar add buttons
├─ [View Dashboard]
└─ [Book Another]
                                     → booking_created {booking_id, status: REQUESTED}
                                     → notification_sent: booking_request (tutor)
                                     → payment_authorized {amount}

Tutor Confirms (Background)
                                     → booking_confirmed {booking_id}
                                     → notification_sent: booking_confirmed (student)
                                     → calendar_event_created {provider}

Session Join (/bookings)
├─ Upcoming sessions card
├─ Countdown timer
├─ [Join Session] button (active at start_time - 5min)
├─ Session details and notes
└─ Tutor contact button
                                     → session_join_clicked {booking_id}
                                     → session_started {booking_id}

Post-Session
├─ "How was your session?" prompt
├─ Star rating (1-5)
├─ Written review (optional)
├─ [Submit Review]
└─ Rebook suggestion
                                     → session_ended {booking_id, outcome: COMPLETED}
                                     → review_prompt_shown
                                     → review_submitted {rating}

"AHA MOMENT"
├─ First positive session completed
├─ Student sees value in 1:1 learning
├─ Receives follow-up email with notes
└─ Prompted to rebook
                                     → aha_moment_achieved {user_id, days_to_aha}
```

**Aha Moment Definition**: Student completes first session with rating >= 4

---

### 4.3 Journey 3: Core Transaction Flow (Booking a Package)

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Trigger: Student has completed 2+ sessions with same tutor

Rebooking CTA (Email/Dashboard)
├─ "Continue learning with [Tutor]"
├─ Package discount highlight
└─ [Book Package]
                                     → rebook_nudge_sent {tutor_id, sessions_completed}

Package Selection (/tutors/[id]/book)
├─ Package options comparison
│   ├─ 5 sessions: 5% off ($X/session)
│   ├─ 10 sessions: 10% off ($Y/session)
│   └─ 20 sessions: 15% off ($Z/session)
├─ Validity period shown (90/180/365 days)
├─ Price breakdown
└─ [Select Package]
                                     → package_viewed {tutor_id, package_options}

Checkout
├─ Package summary
├─ Total price (discounted)
├─ Saved vs individual sessions
├─ Payment method
│   ├─ Saved card
│   ├─ New card
│   └─ Wallet balance
└─ [Purchase Package]
                                     → package_checkout_started {package_id, amount}
                                     → payment_captured {type: package}

Confirmation
├─ "Package Purchased!"
├─ Sessions remaining: X
├─ Expires: [date]
├─ [Schedule First Session]
└─ Package appears in /packages
                                     → package_purchased {package_id, sessions, amount}
                                     → decision_recorded {type: package_purchase}

Session Scheduling (from Package)
├─ Select from available slots
├─ No additional payment required
├─ Session details
└─ [Book Session]
                                     → session_booked_from_package {package_id, sessions_remaining}
                                     → package_sessions_decremented

Package Management (/packages)
├─ Active packages list
├─ Sessions used/remaining
├─ Expiration countdown
├─ Booking history per package
└─ [Book Session] per package
                                     → packages_page_viewed

Expiration Warning (7 days before)
├─ Email: "X sessions expiring soon"
├─ Dashboard banner
└─ [Use Sessions]
                                     → package_expiring_alert {package_id, days_left}
```

---

### 4.4 Journey 4: Support / Dispute Flow

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Trigger: Something goes wrong with a session

Issue Identification
├─ Tutor no-show
├─ Student no-show
├─ Technical issues
├─ Quality concerns
└─ Billing dispute
                                     → issue_type_identified

Reporting (Booking Details Page)
├─ [Report Issue] button
├─ Issue category selection
├─ Description text field
├─ Evidence upload (optional)
│   ├─ Screenshots
│   └─ Messages
└─ [Submit Report]
                                     → dispute_filed {booking_id, reason}
                                     → booking_dispute_state: OPEN
                                     → notification_sent: dispute_filed (admin, counterparty)

Auto-Resolution (Tutor No-Show)
├─ System detects no-show
├─ Automatic full refund initiated
├─ Notification to student
└─ Strike added to tutor
                                     → no_show_detected {type: tutor}
                                     → auto_refund_initiated
                                     → tutor_strike_added
                                     → dispute_state: RESOLVED_REFUNDED

Manual Review Required
├─ Admin notification
├─ Review queue entry
└─ Assigned to support agent
                                     → dispute_escalated {priority}

Admin Investigation (/admin/disputes/[id])
├─ Booking details
├─ Message history
├─ Session recording (if available)
├─ Both parties' statements
├─ Similar past disputes
└─ Resolution options
                                     → dispute_investigated {admin_id}

Resolution Decision
├─ Full refund to student
├─ Partial refund (split)
├─ No refund (ruled in tutor's favor)
├─ Resolution notes
└─ [Apply Resolution]
                                     → dispute_resolved {resolution, amount}
                                     → notification_sent: dispute_resolved (student, tutor)

Follow-up
├─ Satisfaction survey
├─ Appeal option (within 7 days)
└─ Relationship recovery (if possible)
                                     → dispute_satisfaction_survey
                                     → dispute_appeal_window_opened
```

**Resolution SLA**:
- Auto-resolvable (no-show): <5 minutes
- Simple disputes: <24 hours
- Complex disputes: <48 hours

---

### 4.5 Journey 5: Power User Flow (Active Tutor)

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Daily Routine Start

Tutor Dashboard (/tutor/dashboard)
├─ Today's sessions (timeline view)
├─ Pending booking requests
├─ Unread messages indicator
├─ Earnings snapshot (week/month)
├─ Response time status
└─ Quick actions
                                     → tutor_dashboard_viewed

Booking Request Management
├─ New request notification (email + app)
├─ Request details:
│   ├─ Student profile
│   ├─ Requested time
│   ├─ Topic/notes
│   └─ Student's past reviews
├─ [Accept] / [Decline]
├─ Decline requires reason
└─ Auto-confirm for trusted students
                                     → booking_request_actioned {action, response_time}
                                     → tutor_response_logged

Pre-Session Preparation
├─ Session details review
├─ Student notes (private)
│   ├─ Learning goals
│   ├─ Previous session notes
│   └─ Preferences
├─ Materials preparation
└─ [Start Session] at time
                                     → session_prep_viewed {booking_id}

Session Execution
├─ Join Zoom/Meet link
├─ Session timer
├─ Quick notes during session
└─ End session
                                     → video_session_joined
                                     → session_in_progress
                                     → session_ended

Post-Session Admin
├─ Session notes entry
├─ Topics covered
├─ Homework assigned
├─ Next steps
└─ [Save Notes]
                                     → tutor_notes_saved {booking_id}

End of Day

Earnings Check (/tutor/earnings)
├─ Today's earnings
├─ Pending balance
├─ Available for withdrawal
├─ Commission tier progress
├─ Transaction history
└─ [Request Payout]
                                     → earnings_page_viewed
                                     → payout_requested {amount}

Weekly Routine

Schedule Management (/tutor/schedule-manager)
├─ Weekly availability editor
├─ Add/remove time blocks
├─ Blackout periods for vacation
├─ Timezone display
└─ [Save Schedule]
                                     → availability_updated

Performance Review
├─ Booking acceptance rate
├─ Completion rate
├─ Average rating trend
├─ Response time metrics
├─ Student retention rate
└─ Recommendations for improvement
                                     → tutor_metrics_viewed

Profile Optimization
├─ Review competitor profiles
├─ Update bio/headline
├─ Add new certifications
├─ Adjust pricing
└─ Request verification badges
                                     → profile_updated {fields}
```

---

### 4.6 Journey 6: Churn Prevention / Winback Flow

```
TOUCHPOINTS                          BACKEND EVENTS
═══════════════════════════════════════════════════════════════

Churn Signal Detection

├─ No login in 14 days
├─ No booking in 30 days
├─ Cancelled last session
├─ Left negative review
└─ Abandoned checkout
                                     → churn_risk_detected {score, signals}

Re-engagement Campaign (Email)

Day 7 (Soft Touch)
├─ Subject: "We miss you, [Name]!"
├─ Recommended tutors
├─ New tutors in your subjects
└─ No discount
                                     → winback_email_sent {day: 7}

Day 14 (Incentive)
├─ Subject: "Come back with $10 credit"
├─ Credit automatically applied
├─ Expires in 7 days
└─ Featured tutors
                                     → winback_credit_issued {amount: 10}

Day 30 (Final Push)
├─ Subject: "Last chance: $15 credit expiring"
├─ Success stories
├─ Platform updates since last visit
└─ Clear CTA
                                     → winback_email_sent {day: 30}

Return Visit

Landing with Context
├─ Personalized "Welcome back"
├─ Previous tutor available
├─ Credit balance shown
├─ Easy rebook flow
└─ [Continue Learning]
                                     → returning_user_detected {days_absent}

Friction Reduction
├─ Saved payment method
├─ Previous preferences loaded
├─ Tutor already selected
└─ One-click rebook
                                     → rebook_started {is_winback: true}

Successful Reactivation
├─ Session booked
├─ Confirmation email
├─ Credit applied
└─ Entered back into retention loop
                                     → user_reactivated {days_inactive, trigger}

Unsuccessful Winback

Day 60+
├─ Move to dormant segment
├─ Quarterly digest only
├─ Survey: "Why did you leave?"
└─ Keep data for future return
                                     → user_marked_dormant
                                     → churn_survey_sent
```

---

## 5. System Design (Production-Grade)

### 5.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              INTERNET                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EDGE / CDN LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Cloudflare  │  │   WAF &     │  │  DDoS       │  │   SSL/TLS   │    │
│  │    CDN      │  │  Bot Mgmt   │  │ Protection  │  │ Termination │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐    ┌─────────────────────────────────────┐
│       FRONTEND CLUSTER      │    │         API GATEWAY                  │
│  ┌───────────────────────┐  │    │  ┌─────────────────────────────┐    │
│  │   Next.js 15 (SSR)    │  │    │  │  Kong / AWS API Gateway     │    │
│  │   - App Router        │  │    │  │  - Rate Limiting            │    │
│  │   - React 18          │  │    │  │  - Auth Validation          │    │
│  │   - Server Components │  │    │  │  - Request Routing          │    │
│  └───────────────────────┘  │    │  │  - API Versioning           │    │
│  Kubernetes: 3-10 pods      │    │  └─────────────────────────────┘    │
└─────────────────────────────┘    └─────────────────────────────────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          BACKEND SERVICES                                │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   AUTH      │  │  BOOKING    │  │   PAYMENT   │  │  MESSAGING  │    │
│  │  SERVICE    │  │  SERVICE    │  │   SERVICE   │  │   SERVICE   │    │
│  │             │  │             │  │             │  │             │    │
│  │ - JWT/OAuth │  │ - State     │  │ - Stripe    │  │ - WebSocket │    │
│  │ - Sessions  │  │   Machine   │  │ - Payouts   │  │ - Redis PS  │    │
│  │ - RBAC      │  │ - Scheduler │  │ - Refunds   │  │ - History   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   TUTOR     │  │  SEARCH &   │  │NOTIFICATION │  │   ADMIN     │    │
│  │  SERVICE    │  │  MATCHING   │  │   SERVICE   │  │   SERVICE   │    │
│  │             │  │             │  │             │  │             │    │
│  │ - Profiles  │  │ - Full-text │  │ - Email     │  │ - User Mgmt │    │
│  │ - Avail.    │  │ - AI Match  │  │ - Push      │  │ - Analytics │    │
│  │ - Packages  │  │ - Filters   │  │ - In-app    │  │ - Audit     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                                          │
│  FastAPI + Uvicorn | Kubernetes: 5-20 pods | Horizontal Pod Autoscaler  │
└─────────────────────────────────────────────────────────────────────────┘
                    │               │               │
    ┌───────────────┼───────────────┼───────────────┼───────────────┐
    ▼               ▼               ▼               ▼               ▼
┌────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Redis  │    │PostgreSQL│    │  MinIO   │    │ ML Infra │    │ External │
│Cluster │    │  (RDS)   │    │  (S3)    │    │          │    │   APIs   │
│        │    │          │    │          │    │          │    │          │
│- Cache │    │- Primary │    │- Avatars │    │- Feature │    │- Stripe  │
│- PubSub│    │- Read    │    │- Attach. │    │  Store   │    │- Brevo   │
│- Queue │    │  Replica │    │- Docs    │    │- Model   │    │- Zoom    │
│        │    │- Backups │    │          │    │  Serving │    │- Google  │
└────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 5.2 Services/Modules List

| Service | Responsibility | Tech Stack | Scale Target |
|---------|---------------|------------|--------------|
| **Auth Service** | User registration, login, OAuth, JWT management, RBAC | FastAPI, JWT, bcrypt | 1000 auth/sec |
| **Booking Service** | Session lifecycle, state machine, scheduling, conflicts | FastAPI, APScheduler, PostgreSQL | 100 bookings/sec |
| **Payment Service** | Checkout, authorization, capture, refunds, payouts | FastAPI, Stripe SDK | 50 payments/sec |
| **Messaging Service** | Real-time chat, WebSocket, message storage, attachments | FastAPI, WebSocket, Redis Pub/Sub | 10K concurrent connections |
| **Tutor Service** | Profile management, availability, packages, metrics | FastAPI, PostgreSQL | 500 profile updates/sec |
| **Search Service** | Full-text search, filters, AI matching recommendations | FastAPI, PostgreSQL FTS, ML model | 200 searches/sec |
| **Notification Service** | Email, push, in-app, scheduling, preferences | FastAPI, Brevo, Redis Queue | 1000 notifications/sec |
| **Admin Service** | User management, dispute resolution, analytics | FastAPI, PostgreSQL | 10 admins concurrent |
| **Analytics Service** | Event collection, aggregation, reporting | FastAPI, ClickHouse/BigQuery | 10K events/sec |

### 5.3 Data Model: Key Entities

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CORE ENTITIES                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────┐       1:1        ┌──────────────────┐       1:N       ┌──────────────┐
│   USER   │─────────────────▶│  TUTOR_PROFILE   │────────────────▶│TUTOR_SUBJECT │
│          │                  │                  │                 │              │
│ id       │                  │ id               │                 │ id           │
│ email    │                  │ user_id (FK)     │                 │ tutor_id(FK) │
│ role     │                  │ headline         │                 │ subject_id   │
│ password │                  │ bio              │                 │ proficiency  │
│ currency │       1:1        │ hourly_rate      │       1:N       │ years_exp    │
│ timezone │─────────────────▶│ is_approved      │────────────────▶└──────────────┘
└──────────┘                  │ avg_rating       │
     │                        │ stripe_account   │       1:N       ┌──────────────┐
     │                        └──────────────────┘────────────────▶│PRICING_OPTION│
     │                                 │                           │              │
     │       1:1        ┌──────────────┘                           │ id           │
     │                  │                                          │ tutor_id(FK) │
     ▼                  ▼                                          │ title        │
┌──────────────┐  ┌──────────────────┐       1:N       ┌──────────│ price        │
│STUDENT_PROFILE│  │ TUTOR_AVAIL     │────────────────▶│ BLACKOUT │ duration     │
│              │  │                  │                 │          │ validity_days│
│ id           │  │ id               │                 └──────────└──────────────┘
│ user_id (FK) │  │ tutor_id (FK)    │
│ credit_bal   │  │ day_of_week      │
│ interests    │  │ start_time       │
│ goals        │  │ end_time         │
└──────────────┘  └──────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        TRANSACTION ENTITIES                              │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────────────────┐
                    │              BOOKING                  │
                    │                                       │
                    │ id                                    │
                    │ tutor_profile_id (FK)                │
                    │ student_id (FK)                       │
                    │ subject_id (FK)                       │
                    │ start_time, end_time                  │
                    │ ─────────────────────────────────────│
                    │ session_state    [REQUESTED→ENDED]   │
                    │ session_outcome  [COMPLETED/NO_SHOW] │
                    │ payment_state    [PENDING→CAPTURED]  │
                    │ dispute_state    [NONE→RESOLVED]     │
                    │ ─────────────────────────────────────│
                    │ rate_cents, currency                  │
                    │ platform_fee_cents                    │
                    │ tutor_earnings_cents                  │
                    │ pricing_option_id (FK, optional)      │
                    │ package_id (FK, optional)             │
                    └──────────────────────────────────────┘
                         │            │           │
           ┌─────────────┘            │           └─────────────┐
           ▼                          ▼                         ▼
    ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
    │   PAYMENT    │          │    REVIEW    │          │   MESSAGE    │
    │              │          │              │          │              │
    │ id           │          │ id           │          │ id           │
    │ booking_id   │          │ booking_id   │          │ booking_id   │
    │ student_id   │          │ tutor_id     │          │ sender_id    │
    │ amount_cents │          │ student_id   │          │ recipient_id │
    │ status       │          │ rating (1-5) │          │ message      │
    │ stripe_id    │          │ comment      │          │ is_read      │
    └──────────────┘          └──────────────┘          └──────────────┘
           │
           ▼
    ┌──────────────┐
    │    REFUND    │
    │              │
    │ id           │
    │ payment_id   │
    │ amount_cents │
    │ reason       │
    └──────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         PACKAGE ENTITIES                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐       1:N       ┌──────────────────────┐
│  PRICING_OPTION  │────────────────▶│   STUDENT_PACKAGE    │
│                  │                 │                      │
│ id               │                 │ id                   │
│ tutor_id         │                 │ student_id (FK)      │
│ title            │                 │ tutor_id (FK)        │
│ sessions_included│                 │ pricing_option_id    │
│ price            │                 │ sessions_purchased   │
│ validity_days    │                 │ sessions_remaining   │
└──────────────────┘                 │ sessions_used        │
                                     │ purchase_price       │
                                     │ expires_at           │
                                     │ status               │
                                     └──────────────────────┘
```

### 5.4 API Design: Major Endpoints

```yaml
# Authentication
POST   /api/auth/register         # Create account
POST   /api/auth/login            # Get JWT token
POST   /api/auth/logout           # Invalidate token
GET    /api/auth/me               # Get current user
POST   /api/auth/refresh          # Refresh JWT
POST   /api/auth/password/reset   # Request password reset
POST   /api/auth/password/change  # Change password
GET    /api/auth/oauth/google     # Google OAuth callback

# Tutors
GET    /api/tutors                # Search tutors (paginated, filterable)
GET    /api/tutors/{id}           # Get tutor profile
POST   /api/tutors                # Create tutor profile (tutor only)
PATCH  /api/tutors/{id}           # Update tutor profile
GET    /api/tutors/{id}/availability  # Get availability slots
PUT    /api/tutors/{id}/availability  # Update availability
GET    /api/tutors/{id}/reviews   # Get tutor reviews
GET    /api/tutors/{id}/packages  # Get pricing options

# Bookings
GET    /api/bookings              # List user's bookings
POST   /api/bookings              # Create booking request
GET    /api/bookings/{id}         # Get booking details
POST   /api/bookings/{id}/confirm # Tutor confirms booking
POST   /api/bookings/{id}/decline # Tutor declines booking
POST   /api/bookings/{id}/cancel  # Cancel booking
POST   /api/bookings/{id}/reschedule  # Request reschedule
POST   /api/bookings/{id}/no-show # Mark no-show
POST   /api/bookings/{id}/dispute # File dispute

# Packages
GET    /api/packages              # List user's packages
POST   /api/packages              # Purchase package
GET    /api/packages/{id}         # Get package details

# Payments
POST   /api/payments/checkout     # Create Stripe checkout session
GET    /api/payments/{id}         # Get payment status
POST   /api/payments/{id}/refund  # Request refund
GET    /api/payments/wallet       # Get wallet balance
POST   /api/payments/wallet/topup # Add wallet credit

# Payouts (Tutor)
GET    /api/payouts               # List payout history
POST   /api/payouts               # Request payout
GET    /api/payouts/balance       # Get available balance

# Messages
GET    /api/messages/threads      # List message threads
GET    /api/messages/threads/{id} # Get thread messages
POST   /api/messages              # Send message
PATCH  /api/messages/{id}/read    # Mark as read
WS     /api/messages/ws           # WebSocket connection

# Reviews
POST   /api/reviews               # Submit review
GET    /api/reviews/{id}          # Get review
PATCH  /api/reviews/{id}          # Update review

# Notifications
GET    /api/notifications         # List notifications
PATCH  /api/notifications/{id}/read  # Mark as read
PUT    /api/notifications/preferences  # Update preferences

# Admin
GET    /api/admin/users           # List users
GET    /api/admin/users/{id}      # Get user details
PATCH  /api/admin/users/{id}      # Update user
GET    /api/admin/bookings        # List all bookings
GET    /api/admin/disputes        # List open disputes
POST   /api/admin/disputes/{id}/resolve  # Resolve dispute
GET    /api/admin/analytics       # Platform metrics

# Owner
GET    /api/owner/dashboard       # Financial dashboard
GET    /api/owner/revenue         # Revenue breakdown
GET    /api/owner/tutors/performance  # Tutor performance
```

### 5.5 Eventing System

```yaml
# Event Bus: Redis Streams (current) → Kafka (future scale)

Topics:
  user.events:
    - user.registered {user_id, email, role, method}
    - user.verified {user_id}
    - user.deactivated {user_id, reason}
    - user.role_changed {user_id, old_role, new_role}

  booking.events:
    - booking.requested {booking_id, tutor_id, student_id, amount}
    - booking.confirmed {booking_id, confirmed_at}
    - booking.declined {booking_id, reason}
    - booking.cancelled {booking_id, cancelled_by, reason}
    - booking.started {booking_id}
    - booking.ended {booking_id, outcome}
    - booking.expired {booking_id}

  payment.events:
    - payment.authorized {payment_id, booking_id, amount}
    - payment.captured {payment_id, amount}
    - payment.failed {payment_id, error}
    - payment.refunded {payment_id, refund_id, amount}
    - payout.requested {payout_id, tutor_id, amount}
    - payout.completed {payout_id}

  package.events:
    - package.purchased {package_id, student_id, tutor_id, sessions}
    - package.session_used {package_id, booking_id, remaining}
    - package.expiring {package_id, expires_at}
    - package.expired {package_id}

  notification.events:
    - notification.scheduled {notification_id, user_id, type}
    - notification.sent {notification_id, channel}
    - notification.opened {notification_id}
    - notification.clicked {notification_id}

  dispute.events:
    - dispute.filed {booking_id, filed_by, reason}
    - dispute.escalated {booking_id, priority}
    - dispute.resolved {booking_id, resolution}
```

### 5.6 Real-time Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      WEBSOCKET ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

Client                    Load Balancer              Backend Pods
  │                            │                          │
  │  WS Connection Request     │                          │
  │───────────────────────────▶│                          │
  │                            │   Sticky Session         │
  │                            │──────────────────────────▶│
  │                            │                          │
  │◀───────────────────────────┼──────────────────────────│
  │  Connection Established    │                          │
  │                            │                          │
  │                            │                          │
  │  Send Message              │                          │
  │───────────────────────────▶│─────────────────────────▶│
  │                            │                          │
  │                            │      ┌───────────────────┼───────────┐
  │                            │      │  Redis Pub/Sub    │           │
  │                            │      │                   │           │
  │                            │      │  Channel:         │           │
  │                            │      │  user:{user_id}   │           │
  │                            │      │                   │           │
  │                            │      │  Publish message  │           │
  │                            │      │  to recipient's   │           │
  │                            │      │  channel          │           │
  │                            │      └───────────────────┼───────────┘
  │                            │                          │
  │  Receive Message           │                          │
  │◀───────────────────────────┼──────────────────────────│
  │                            │                          │

Message Types:
  - message.new        # New chat message
  - message.read       # Read receipt
  - message.typing     # Typing indicator
  - booking.update     # Booking state change
  - notification.new   # New notification
```

### 5.7 Search Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SEARCH ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────┘

Current: PostgreSQL Full-Text Search (GIN index on tsvector)

Fields Indexed:
  - tutor_profiles.title (Weight A)
  - tutor_profiles.headline (Weight B)
  - tutor_profiles.bio (Weight C)
  - tutor_profiles.description (Weight D)

Query Flow:
  1. User enters search term
  2. Apply filters (subject, price, rating, availability)
  3. Full-text search with ts_rank
  4. Sort by relevance + rating
  5. Paginate results

Future: Elasticsearch/OpenSearch (at scale)
  - Real-time indexing via event bus
  - Faceted search (subjects, languages, certifications)
  - Geo-search for local tutors
  - Typo tolerance and suggestions
  - Personalized ranking (ML)
```

### 5.8 Notification Strategy

```yaml
Channels:
  email:
    provider: Brevo (Sendinblue)
    templates:
      - welcome
      - booking_request
      - booking_confirmed
      - booking_reminder (24h, 1h)
      - session_completed
      - review_prompt
      - package_expiring
      - winback_series
    rate_limit: 100/hour per user

  push:
    provider: Firebase Cloud Messaging (future)
    types:
      - booking_updates
      - new_messages
      - session_reminders

  in_app:
    storage: PostgreSQL (notifications table)
    delivery: WebSocket push
    retention: 90 days

Timing Rules:
  - Quiet hours: Respect user preferences (default 10pm-8am local)
  - Batching: Aggregate non-urgent notifications
  - Throttling: Max 10 notifications/day per user (non-transactional)
```

### 5.9 Multi-tenancy / Localization / Timezones

```yaml
Multi-tenancy: Not applicable (single platform, not white-label)

Localization:
  current:
    - Languages: English only
    - Currencies: 12 supported (USD default)
    - DB structure: Ready (supported_languages, subject_localizations)
  future:
    - Languages: EN, ES, FR, DE, PT, ZH
    - Currency display: User preference
    - Payment: Stripe multi-currency

Timezones:
  storage: All timestamps in UTC
  user_preference: Stored in users.timezone
  display: Converted client-side using date-fns-tz
  booking:
    - Tutor sets availability in their timezone
    - Student sees slots in their timezone
    - Booking stored with both timezones for reference
  reminders: Sent relative to user's local time
```

### 5.10 Scalability Plan

| Scale | Users | Sessions/Day | Architecture Changes |
|-------|-------|--------------|---------------------|
| **10x** (50K users) | 50,000 | 5,000 | Add read replicas, CDN for static assets, Redis cluster |
| **100x** (500K users) | 500,000 | 50,000 | Kubernetes HPA, PostgreSQL sharding, Elasticsearch, dedicated ML infra |
| **1000x** (5M users) | 5,000,000 | 500,000 | Multi-region deployment, event-driven microservices, data lake |

### 5.11 Reliability

```yaml
SLAs:
  availability: 99.9% (8.76 hours downtime/year)
  api_latency_p95: <500ms
  booking_processing: <5 seconds
  payment_processing: <10 seconds
  message_delivery: <1 second

SLOs:
  error_rate: <0.1% of requests
  booking_success: >99% of confirmed bookings complete
  payment_success: >98% of checkouts complete
  notification_delivery: >99% within 5 minutes

Patterns:
  retries:
    - Exponential backoff with jitter
    - Max 3 retries for external APIs
    - Idempotency keys for payments

  idempotency:
    - All payment operations use idempotency keys
    - Booking creation uses deduplication window
    - Message sends use client-generated IDs

  rate_limits:
    - Auth: 5 registrations/min, 10 logins/min per IP
    - API: 100 requests/min per user (default)
    - Search: 20 requests/min per user
    - Messages: 60 messages/min per user

  circuit_breakers:
    - Stripe: Break on 5 failures in 60s, 30s recovery
    - Brevo: Break on 10 failures in 60s, 60s recovery
    - Zoom: Break on 3 failures in 60s, 30s recovery
```

### 5.12 Security

```yaml
Authentication:
  method: JWT (HS256, 30-min expiration)
  refresh: Not implemented (re-login required)
  oauth: Google OIDC
  password: bcrypt (12 rounds)
  mfa: Not implemented (future)

Authorization:
  model: RBAC (Role-Based Access Control)
  roles: student, tutor, admin, owner
  enforcement:
    - Route-level via dependencies
    - Resource-level via ownership checks

Secrets Management:
  current: Environment variables
  future: AWS Secrets Manager / HashiCorp Vault

Encryption:
  transit: TLS 1.3 (all connections)
  at_rest:
    - PostgreSQL: Encrypted volumes
    - MinIO: Server-side encryption
    - Backups: Encrypted
  passwords: bcrypt (one-way hash)

Audit Logging:
  scope: All admin actions, sensitive operations
  storage: audit_log table (immutable)
  retention: 7 years
  fields: table, record_id, action, old_data, new_data, user, ip, timestamp

Security Headers:
  - Content-Security-Policy
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Strict-Transport-Security
  - Referrer-Policy: strict-origin-when-cross-origin
```

### 5.13 Privacy & Compliance

```yaml
GDPR/CCPA Compliance:
  data_subject_rights:
    - Access: User can export all their data
    - Rectification: User can edit profile
    - Erasure: User can request account deletion
    - Portability: Export in JSON format

  consent:
    - Marketing emails: Explicit opt-in
    - Analytics: Cookie consent banner
    - Session recording: Explicit consent per session

  data_retention:
    - Active accounts: Indefinite
    - Deleted accounts: Anonymized after 30 days
    - Messages: 2 years
    - Audit logs: 7 years
    - Financial records: 7 years

  data_processing:
    - DPA: Required for enterprise customers
    - Sub-processors: Stripe, Brevo, Google, Zoom, AWS

Children's Privacy (COPPA):
  - Age verification: Date of birth with 18+ check
  - K-12: Parent account controls student account (future)
  - Parental consent: Required for under-18 (future)
```

### 5.14 Payments Architecture

```yaml
Payment Flow:
  1. Student initiates booking/package purchase
  2. Create Stripe Checkout Session (mode: payment)
  3. Student completes payment on Stripe-hosted page
  4. Webhook: checkout.session.completed
  5. Authorize funds (booking) or capture immediately (package)
  6. On session completion: capture authorized funds
  7. Calculate commission (20%/15%/10%)
  8. Queue tutor payout

Stripe Connect:
  type: Standard accounts
  onboarding: OAuth flow
  payouts: Manual request or auto-weekly (future)

Fraud Prevention:
  - Stripe Radar: Enabled
  - Velocity checks: Max 5 bookings/hour per student
  - Review queue: High-value transactions (>$500)

Chargebacks:
  - Auto-respond with session evidence
  - Dispute tracking in dispute_state
  - Win rate target: >70%

Ledgering:
  current: payments + refunds tables
  future: Double-entry accounting system

Multi-currency:
  - Student pays in their currency
  - Tutor receives in their currency
  - Platform takes fees in settlement currency (USD)
  - Exchange rate: Stripe's rate at transaction time
```

---

## 6. UX/UI Direction

### 6.1 Design Principles

1. **Accessible First**: WCAG 2.1 AA compliance; works for users with disabilities, slow connections, and older devices

2. **Trust Through Transparency**: Show tutor credentials, ratings, and fees upfront; no hidden costs; clear cancellation policies

3. **Progressive Disclosure**: Start simple, reveal complexity as needed; booking in 3 clicks; advanced filters on demand

4. **Global by Design**: Support RTL layouts (future), multiple currencies, timezone-aware scheduling

5. **Mobile-First, Desktop-Enhanced**: Core flows work on any device; rich features on larger screens

6. **Speed as Feature**: Page loads <3s on 3G; instant feedback on actions; skeleton loaders for perceived performance

7. **Calm Design**: No dark patterns; respect attention; notifications that help not annoy

### 6.2 Information Architecture

```
PUBLIC
├── Home (/)
│   ├── Hero + Search
│   ├── How It Works
│   ├── Featured Tutors
│   ├── Testimonials
│   └── CTA
├── Browse Tutors (/tutors)
│   ├── Search + Filters
│   ├── Results Grid
│   └── Pagination
├── Tutor Profile (/tutors/[id])
│   ├── Overview
│   ├── Subjects
│   ├── Reviews
│   ├── Availability
│   └── Book CTA
├── Legal (/privacy, /terms)
├── Help (/help-center)
└── Auth (/login, /register)

STUDENT (Protected)
├── Dashboard (/dashboard)
│   ├── Upcoming Sessions
│   ├── Quick Book
│   ├── Saved Tutors
│   └── Stats
├── Bookings (/bookings)
│   ├── Upcoming
│   ├── Past
│   └── Cancelled
├── Booking Detail (/bookings/[id])
│   ├── Session Info
│   ├── Join Button
│   ├── Messages
│   └── Actions
├── Messages (/messages)
│   ├── Thread List
│   └── Conversation
├── Packages (/packages)
│   ├── Active
│   ├── Expired
│   └── Purchase History
├── Wallet (/wallet)
│   ├── Balance
│   └── Transactions
├── Saved Tutors (/saved-tutors)
└── Settings (/settings/*)

TUTOR (Protected)
├── Dashboard (/tutor/dashboard)
│   ├── Today's Schedule
│   ├── Pending Requests
│   ├── Messages
│   └── Earnings Summary
├── Schedule (/tutor/schedule)
│   ├── Calendar View
│   └── Availability Editor
├── Students (/tutor/students)
│   ├── Student List
│   └── Notes
├── Earnings (/tutor/earnings)
│   ├── Balance
│   ├── Payouts
│   └── Commission Tier
├── Profile (/tutor/profile)
│   ├── Basic Info
│   ├── Subjects
│   ├── Education
│   ├── Certifications
│   └── Pricing
└── Settings (/settings/*)

ADMIN (Protected)
├── Dashboard (/admin)
│   ├── KPIs
│   ├── User Management
│   ├── Sessions
│   ├── Disputes
│   ├── Analytics
│   └── Settings
└── Audit Log

OWNER (Protected)
├── Dashboard (/owner)
│   ├── Revenue
│   ├── Growth
│   ├── Health
│   └── Commissions
```

### 6.3 Key Screens

| Screen | Platform | Purpose | Key Elements |
|--------|----------|---------|--------------|
| Landing Page | Web | Convert visitors | Hero, search, social proof |
| Tutor Search | Web + Mobile | Discovery | Filters, cards, pagination |
| Tutor Profile | Web + Mobile | Evaluate & book | Bio, reviews, availability, CTA |
| Booking Modal | Web + Mobile | Complete transaction | Steps: pricing → time → details → pay |
| Student Dashboard | Web + Mobile | Home base | Sessions, stats, quick actions |
| Tutor Dashboard | Web | Manage business | Requests, schedule, earnings |
| Messages | Web + Mobile | Communication | Thread list, chat interface |
| Settings | Web + Mobile | Account management | Profile, payments, notifications |
| Admin Console | Web | Operations | Tables, charts, actions |

### 6.4 Accessibility Checklist

- [ ] Semantic HTML (headings, landmarks, lists)
- [ ] ARIA labels for interactive elements
- [ ] Keyboard navigation (all actions accessible)
- [ ] Focus management (modals, forms)
- [ ] Color contrast (4.5:1 minimum)
- [ ] Text resizing (up to 200%)
- [ ] Screen reader testing (NVDA, VoiceOver)
- [ ] Reduced motion support
- [ ] Error identification (clear, associated)
- [ ] Form labels and instructions
- [ ] Skip links
- [ ] Captions for video content

### 6.5 Design System Plan

```yaml
Tokens:
  colors:
    primary: Blue (#2563EB)
    secondary: Purple (#7C3AED)
    success: Green (#10B981)
    warning: Amber (#F59E0B)
    error: Red (#EF4444)
    neutral: Gray scale

  typography:
    font_family: Inter, system-ui, sans-serif
    scale: 12/14/16/18/20/24/30/36/48px
    weights: 400, 500, 600, 700

  spacing:
    base: 4px
    scale: 4/8/12/16/20/24/32/40/48/64px

  radii:
    sm: 4px
    md: 8px
    lg: 12px
    full: 9999px

  shadows:
    sm: 0 1px 2px rgba(0,0,0,0.05)
    md: 0 4px 6px rgba(0,0,0,0.1)
    lg: 0 10px 15px rgba(0,0,0,0.1)

Components:
  primitives:
    - Button (primary, secondary, ghost, danger)
    - Input (text, email, password, search)
    - Select (single, multi)
    - Checkbox, Radio, Toggle
    - Avatar
    - Badge
    - Card

  composites:
    - Modal
    - Dropdown
    - Tabs
    - Toast
    - Pagination
    - DataTable

  patterns:
    - Form (with validation)
    - Empty State
    - Loading State
    - Error State
    - Confirmation Dialog

Theming:
  modes: Light (default), Dark (future)
  customization: CSS variables
```

### 6.6 Microcopy Tone Guide

**Voice Attributes:**
- Friendly but professional
- Clear and concise
- Encouraging without being patronizing
- Inclusive (avoid gendered language)

**Writing Guidelines:**
- Use active voice
- Address user as "you"
- Avoid jargon
- Be specific ("Book a session" not "Proceed")
- Error messages: What happened + What to do

**Examples:**

| Context | Do | Don't |
|---------|-----|-------|
| Empty state | "No upcoming sessions. Ready to learn something new?" | "You have no bookings." |
| Success | "Session booked! Check your email for details." | "Booking successful." |
| Error | "Payment failed. Please check your card details and try again." | "Error 402: Payment declined." |
| Loading | "Finding the perfect tutor for you..." | "Loading..." |
| CTA | "Book your first session" | "Submit" |

---

## 7. Engineering Execution Plan

### 7.1 Workstreams

| Workstream | Scope | Team Size |
|------------|-------|-----------|
| **Frontend** | Next.js app, React components, state management | 4-6 engineers |
| **Backend** | FastAPI services, business logic, integrations | 4-6 engineers |
| **Data** | PostgreSQL, migrations, analytics pipeline | 2-3 engineers |
| **ML** | AI matching, recommendations, fraud detection | 2-3 engineers |
| **DevOps** | Kubernetes, CI/CD, monitoring, security | 2-3 engineers |
| **Mobile** | React Native apps (future) | 3-4 engineers |
| **QA** | Test automation, manual testing, performance | 2-3 engineers |
| **Growth** | SEO, referrals, email campaigns | 1-2 engineers |

### 7.2 Phased Delivery

---

#### Phase 0: Foundations (Current + 4 weeks)

**Goals:**
- Stabilize existing MVP
- Fix critical bugs
- Improve test coverage
- Prepare for scale

**Features Shipped:**
- Bug fixes from backlog
- Performance optimizations
- Test coverage to 80%
- Documentation updates

**Architecture Changes:**
- None (stabilization only)

**Risks & Mitigations:**
| Risk | Mitigation |
|------|------------|
| Hidden bugs in state machine | Comprehensive integration tests |
| Performance bottlenecks | Load testing and profiling |

**Definition of Done:**
- [ ] All P0/P1 bugs closed
- [ ] Test coverage >80%
- [ ] Load test: 100 concurrent users
- [ ] Documentation current
- [ ] CI/CD green

---

#### Phase 1: MVP Launch (Weeks 5-12)

**Goals:**
- Launch to first users
- Acquire 500 tutors, 2000 students
- Process first $50K GMV
- Validate product-market fit

**Features Shipped:**
- Landing page optimization
- SEO fundamentals
- Referral program (basic)
- Tutor onboarding improvements
- Email automation (welcome, reminders)
- Basic analytics dashboard

**Architecture Changes:**
- Add application monitoring (Sentry)
- Implement structured logging
- Set up analytics pipeline (Segment → warehouse)

**Risks & Mitigations:**
| Risk | Mitigation |
|------|------------|
| Low tutor supply | Outbound recruitment, social campaigns |
| Payment failures | Stripe Radar, retry logic |
| Support overload | FAQ, help center, email templates |

**Definition of Done:**
- [ ] 500 active tutors
- [ ] 2000 registered students
- [ ] $50K GMV processed
- [ ] <2% error rate
- [ ] NPS >30

---

#### Phase 2: V1 Scale (Weeks 13-26)

**Goals:**
- Scale to 5000 tutors, 20000 students
- Launch AI matching MVP
- Achieve $500K GMV
- Positive unit economics

**Features Shipped:**
- AI tutor matching v1
- Advanced search filters
- Tutor verification badges
- Package improvements
- Mobile-responsive optimization
- Notification preferences
- Multi-currency improvements

**Architecture Changes:**
- Kubernetes deployment
- Read replicas for PostgreSQL
- Redis cluster for sessions
- CDN for static assets
- Feature flag system

**Risks & Mitigations:**
| Risk | Mitigation |
|------|------------|
| AI matching cold start | Fallback to rule-based matching |
| Database bottlenecks | Query optimization, read replicas |
| Tutor quality variance | Verification, badges, reviews |

**Definition of Done:**
- [ ] 5000 active tutors
- [ ] 20000 registered students
- [ ] $500K GMV
- [ ] AI matching used in 30% of bookings
- [ ] 99.5% uptime

---

#### Phase 3: V2 Expansion (Weeks 27-52)

**Goals:**
- International expansion (UK, AU, IN)
- Mobile apps launch
- Enterprise pilot
- $5M GMV run rate

**Features Shipped:**
- iOS and Android apps
- Parent dashboard for K-12
- Background checks integration
- Session recording (opt-in)
- Enterprise admin portal
- Advanced analytics
- Localization (ES, FR)
- Affiliate program

**Architecture Changes:**
- Multi-region deployment (US, EU)
- Event-driven architecture
- Elasticsearch for search
- ML pipeline (feature store, model serving)

**Risks & Mitigations:**
| Risk | Mitigation |
|------|------------|
| Mobile app adoption | PWA fallback, app store optimization |
| International compliance | Legal review per region |
| Enterprise sales cycle | Self-serve onboarding, pilots |

**Definition of Done:**
- [ ] Mobile apps: 10K downloads
- [ ] 3 enterprise contracts signed
- [ ] Available in 5 countries
- [ ] $5M GMV run rate
- [ ] 99.9% uptime

---

#### Phase 4: Ecosystem & Platform (Year 2+)

**Goals:**
- Build platform/ecosystem
- 100K tutors, 1M students
- $50M GMV
- Profitability

**Features Shipped:**
- Public API for partners
- LMS integrations
- Tutor tools marketplace
- Content library
- Certification programs
- Corporate learning portal
- White-label option

**Architecture Changes:**
- Microservices decomposition
- GraphQL API layer
- Data lake for analytics
- Real-time ML recommendations

---

### 7.3 90-Day Execution Plan

See [Section 12.5](#125-90-day-execution-plan) for week-by-week breakdown.

---

## 8. Team & Operations

### 8.1 Org Chart

```
                              ┌──────────────┐
                              │     CEO      │
                              └──────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
┌───────┴───────┐          ┌────────┴────────┐          ┌────────┴────────┐
│    Product    │          │   Engineering   │          │    Operations   │
│      VP       │          │       VP        │          │       VP        │
└───────────────┘          └─────────────────┘          └─────────────────┘
        │                            │                            │
   ┌────┴────┐              ┌───────┴───────┐            ┌───────┴───────┐
   │         │              │               │            │               │
┌──┴──┐  ┌───┴───┐    ┌─────┴─────┐  ┌──────┴──────┐  ┌──┴──┐      ┌─────┴─────┐
│ PM  │  │Design │    │  Backend  │  │  Frontend   │  │ CS  │      │  Finance  │
│     │  │       │    │  Lead     │  │  Lead       │  │Lead │      │           │
└─────┘  └───────┘    └───────────┘  └─────────────┘  └─────┘      └───────────┘
                            │               │
                      ┌─────┴─────┐   ┌─────┴─────┐
                      │           │   │           │
                   ┌──┴──┐    ┌───┴───┐    ┌──────┴──────┐
                   │DevOps│   │  QA   │    │    Data     │
                   │      │   │       │    │  /ML Lead   │
                   └──────┘   └───────┘    └─────────────┘
```

### 8.2 Roles & Responsibilities

| Role | Responsibilities | Reports To |
|------|-----------------|------------|
| **CEO** | Vision, strategy, fundraising, culture | Board |
| **VP Product** | Product strategy, roadmap, metrics | CEO |
| **VP Engineering** | Technical strategy, team building, delivery | CEO |
| **VP Operations** | Support, finance, legal, HR | CEO |
| **Product Manager** | Feature specs, prioritization, user research | VP Product |
| **Design Lead** | Design system, UX research, UI design | VP Product |
| **Backend Lead** | API architecture, services, integrations | VP Engineering |
| **Frontend Lead** | React/Next.js, performance, accessibility | VP Engineering |
| **DevOps Lead** | Infrastructure, CI/CD, monitoring | VP Engineering |
| **QA Lead** | Test strategy, automation, quality gates | VP Engineering |
| **Data/ML Lead** | Analytics, ML models, data infrastructure | VP Engineering |
| **CS Lead** | Support, success, community | VP Operations |

### 8.3 Hiring Plan by Phase

| Phase | New Hires | Roles |
|-------|-----------|-------|
| **Phase 0** | 0 | Stabilize with current team |
| **Phase 1** | 3-5 | 1 PM, 1 Designer, 2 Engineers, 1 CS |
| **Phase 2** | 5-8 | 2 Backend, 2 Frontend, 1 DevOps, 1 QA, 2 CS |
| **Phase 3** | 8-12 | 3 Mobile, 2 ML, 2 Engineers, 3 CS, 1 Legal |
| **Phase 4** | 15+ | Scale all teams |

### 8.4 On-Call & Incident Response

```yaml
On-Call Rotation:
  schedule: Weekly rotation (Mon 9am to Mon 9am)
  primary: 1 engineer (backend-capable)
  secondary: 1 engineer (escalation)
  tools: PagerDuty, Slack #incidents

Severity Levels:
  SEV1:
    definition: Platform down, payments broken, data breach
    response_time: 15 minutes
    resolution_target: 1 hour
    notification: CEO, VP Eng, VP Ops

  SEV2:
    definition: Major feature broken, significant user impact
    response_time: 30 minutes
    resolution_target: 4 hours
    notification: VP Eng, affected team leads

  SEV3:
    definition: Minor feature broken, workaround available
    response_time: 2 hours
    resolution_target: 24 hours
    notification: Team lead

Incident Process:
  1. Alert received → Acknowledge in PagerDuty
  2. Create incident channel: #inc-YYYY-MM-DD-short-description
  3. Assess severity, notify stakeholders
  4. Investigate and resolve
  5. Communicate status updates (every 30 min for SEV1/2)
  6. Write postmortem (within 48 hours)
  7. Track action items to completion
```

### 8.5 Support Operations

```yaml
Channels:
  - Email: support@edustream.com
  - In-app: Help widget
  - Future: Live chat, phone (enterprise)

Tiers:
  Tier 1 (CS Team):
    - Account issues
    - Basic how-to
    - Booking modifications
    - Refund requests (standard)
    response_time: <4 hours

  Tier 2 (Senior CS):
    - Complex disputes
    - Payment issues
    - Tutor complaints
    response_time: <8 hours

  Tier 3 (Engineering):
    - Technical bugs
    - Integration issues
    - Security concerns
    response_time: <24 hours

Escalation Matrix:
  Student complaint about tutor → T1 → T2 (if serious)
  Payment failure → T1 → T3 (if Stripe issue)
  Bug report → T1 → T3
  Fraud suspicion → T2 → Admin → Legal

Tools:
  - Ticketing: Zendesk
  - Internal comms: Slack
  - Documentation: Notion
```

### 8.6 Documentation Standards

```yaml
Code Documentation:
  - Docstrings: All public functions
  - README: Every module
  - Architecture Decision Records (ADRs): Major decisions
  - API docs: Auto-generated from OpenAPI

Product Documentation:
  - PRDs: Notion, template-based
  - User guides: Help center
  - Release notes: Changelog

Operational Documentation:
  - Runbooks: All critical processes
  - Incident playbooks: By service/alert
  - Onboarding guide: New engineer setup

Standards:
  - Review: All docs peer-reviewed
  - Freshness: Review quarterly
  - Ownership: Each doc has an owner
```

---

## 9. Quality Plan

### 9.1 Test Strategy

```yaml
Unit Tests:
  coverage_target: 80%
  framework: pytest (backend), Jest (frontend)
  scope:
    - Business logic
    - Utilities
    - Data transformations
  ownership: Feature developer

Integration Tests:
  coverage_target: 70% of endpoints
  framework: pytest-asyncio, httpx
  scope:
    - API endpoints
    - Database operations
    - External service mocks
  ownership: Feature developer

Contract Tests:
  scope: API schema validation
  tool: Pydantic schemas, OpenAPI
  ownership: Backend team

E2E Tests:
  coverage_target: Critical user journeys
  framework: Playwright
  scope:
    - Registration → First booking
    - Tutor onboarding
    - Payment flow
    - Dispute flow
  ownership: QA team

Load Tests:
  tool: Locust or k6
  scenarios:
    - 100 concurrent users (baseline)
    - 1000 concurrent users (scale)
    - Payment spike (Black Friday)
  schedule: Before major releases
  ownership: DevOps + QA

Security Tests:
  scope:
    - OWASP Top 10
    - Authentication bypass
    - Authorization checks
    - Input validation
  tools: Bandit (static), OWASP ZAP (dynamic)
  schedule: Quarterly + before releases
  ownership: Security + DevOps

Chaos Tests (Future):
  scope: Failure resilience
  scenarios:
    - Database failover
    - Redis unavailable
    - Stripe timeout
  tool: Chaos Monkey / Litmus
```

### 9.2 CI/CD Pipeline

```yaml
Pipeline Stages:

1. Lint:
   - Ruff (Python)
   - ESLint (TypeScript)
   - Prettier (formatting)
   duration: ~1 min

2. Type Check:
   - MyPy (Python)
   - TypeScript compiler
   duration: ~2 min

3. Unit Tests:
   - pytest with coverage
   - Jest with coverage
   - Fail if coverage < threshold
   duration: ~5 min

4. Integration Tests:
   - Docker Compose test environment
   - API tests with test database
   duration: ~10 min

5. Security Scan:
   - Bandit (Python vulnerabilities)
   - npm audit (JS vulnerabilities)
   - Trivy (container scan)
   duration: ~3 min

6. Build:
   - Docker images
   - Next.js static assets
   duration: ~5 min

7. Deploy (Staging):
   - Auto-deploy on main branch
   - Run E2E tests
   duration: ~10 min

8. Deploy (Production):
   - Manual approval required
   - Canary deployment (10% → 50% → 100%)
   - Automatic rollback on error rate spike
   duration: ~15 min

Total Pipeline: ~45 min (parallelized where possible)
```

### 9.3 Release Strategy

```yaml
Feature Flags:
  tool: LaunchDarkly or custom (Redis-based)
  usage:
    - New features: Released behind flag
    - Gradual rollout: 10% → 25% → 50% → 100%
    - Kill switch: Instant disable

Canary Deployment:
  process:
    1. Deploy to 10% of pods
    2. Monitor error rates for 15 min
    3. Auto-rollback if errors > 1%
    4. Proceed to 50%, then 100%

Release Schedule:
  - Features: Weekly (Tuesday)
  - Bug fixes: As needed
  - Hotfixes: Immediate (bypass canary for SEV1)

Rollback:
  trigger: Manual or auto (error threshold)
  method: Kubernetes rollback to previous deployment
  time: <5 minutes
```

### 9.4 Observability

```yaml
Logging:
  format: Structured JSON
  levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  fields: timestamp, level, service, request_id, user_id, message
  storage: CloudWatch / ELK Stack
  retention: 30 days (hot), 1 year (cold)

Metrics:
  tool: Prometheus + Grafana
  types:
    - RED: Rate, Errors, Duration (per endpoint)
    - USE: Utilization, Saturation, Errors (per resource)
    - Business: Bookings/hour, GMV, signups
  dashboards:
    - Platform health
    - API performance
    - Business metrics
    - Cost tracking

Tracing:
  tool: OpenTelemetry + Jaeger
  scope: Request → all services → database
  sampling: 10% (production), 100% (staging)

Alerting:
  tool: PagerDuty + Grafana Alerts
  alerts:
    - Error rate > 1% (5 min window)
    - P95 latency > 2s
    - Payment success < 95%
    - Database connections > 80%
    - Disk usage > 85%
```

### 9.5 Performance Budgets

```yaml
Frontend:
  LCP: <2.5s (Largest Contentful Paint)
  FID: <100ms (First Input Delay)
  CLS: <0.1 (Cumulative Layout Shift)
  TTI: <3.5s (Time to Interactive)
  Bundle size: <500KB (gzipped)

Backend:
  API P50: <100ms
  API P95: <500ms
  API P99: <1s
  Database query P95: <50ms

Infrastructure:
  CPU utilization: <70% average
  Memory utilization: <80% average
  Database connections: <70% of max
```

---

## 10. Analytics & Experimentation

### 10.1 North Star Metric

**Primary: Weekly Active Learners (WAL)**
- Definition: Unique students who completed at least one session in the past 7 days
- Why: Captures both acquisition and engagement; leading indicator of revenue

**Input Metrics (Drivers):**
| Metric | Definition | Target |
|--------|------------|--------|
| New signups | New accounts created | 500/week |
| Activation rate | % of signups completing first booking within 7 days | 30% |
| Booking conversion | % of search sessions → booking | 5% |
| Session completion | % of scheduled sessions completed | 85% |
| Repeat rate | % of students booking again within 30 days | 50% |
| Tutor supply | Active tutors with availability | 5000 |

### 10.2 Event Taxonomy

```yaml
User Events:
  user_signed_up:
    properties: [method, role, referral_source]
  user_verified:
    properties: [method]
  user_logged_in:
    properties: [method]
  profile_updated:
    properties: [fields_changed]

Search Events:
  search_performed:
    properties: [query, filters, results_count]
  tutor_viewed:
    properties: [tutor_id, source]
  filter_applied:
    properties: [filter_type, value]

Booking Events:
  booking_initiated:
    properties: [tutor_id, pricing_type]
  checkout_started:
    properties: [amount, currency]
  booking_created:
    properties: [booking_id, tutor_id, amount]
  booking_confirmed:
    properties: [booking_id, response_time]
  booking_cancelled:
    properties: [booking_id, cancelled_by, reason]
  session_completed:
    properties: [booking_id, duration, outcome]
  review_submitted:
    properties: [booking_id, rating]

Payment Events:
  payment_authorized:
    properties: [amount, currency, method]
  payment_captured:
    properties: [amount]
  payment_failed:
    properties: [error_code]
  refund_issued:
    properties: [amount, reason]

Engagement Events:
  message_sent:
    properties: [thread_id]
  notification_received:
    properties: [type]
  notification_clicked:
    properties: [type, action]
```

### 10.3 Funnel Definitions

```yaml
Acquisition Funnel:
  1. landing_page_viewed
  2. signup_started
  3. signup_completed
  4. email_verified

Activation Funnel:
  1. search_performed
  2. tutor_viewed
  3. booking_initiated
  4. checkout_completed
  5. session_completed

Retention Funnel:
  1. session_completed (first)
  2. returned_within_7_days
  3. booking_initiated (second)
  4. session_completed (second)

Tutor Supply Funnel:
  1. tutor_signup_started
  2. profile_created
  3. profile_submitted
  4. profile_approved
  5. first_booking_received
  6. first_session_completed
```

### 10.4 A/B Testing Framework

```yaml
Process:
  1. Hypothesis: "Showing tutor response time will increase booking rate"
  2. Define metrics: Primary (booking rate), Secondary (profile views)
  3. Calculate sample size: MDE 5%, power 80%, significance 95%
  4. Implement with feature flag
  5. Run experiment (2-4 weeks typically)
  6. Analyze results (statistical significance)
  7. Document and ship (or revert)

Guardrails:
  - Never degrade core metrics >5%
  - Monitor payment success rate
  - Watch for novelty effects

Tools:
  - Feature flags: LaunchDarkly
  - Analysis: Custom (Python) or Statsig
  - Sample size: Evan Miller calculator
```

### 10.5 Data Warehouse Design

```yaml
Architecture:
  Source → Ingestion → Warehouse → BI Tool

  PostgreSQL  ─┐
  Stripe      ─┼──▶  Fivetran/Airbyte  ──▶  Snowflake/BigQuery  ──▶  Metabase
  Segment     ─┤
  Brevo       ─┘

Tables:
  Raw Layer:
    - raw_events (all tracked events)
    - raw_users (from PostgreSQL)
    - raw_bookings (from PostgreSQL)
    - raw_payments (from Stripe)

  Staging Layer:
    - stg_users (cleaned, typed)
    - stg_bookings (enriched with user data)
    - stg_sessions (sessions with outcomes)

  Marts Layer:
    - dim_users (user dimensions)
    - dim_tutors (tutor dimensions)
    - fct_bookings (booking facts)
    - fct_payments (payment facts)
    - fct_sessions (session facts)

  Analytics Layer:
    - agg_daily_metrics
    - agg_weekly_cohorts
    - agg_tutor_performance

Governance:
  - Data owner: Data/ML Lead
  - Access: Role-based (analyst, admin)
  - PII handling: Masked in analytics layer
  - Retention: 3 years in warehouse
```

---

## 11. Risks & Hard Problems

### 11.1 Risk Register

| # | Risk | Category | Likelihood | Impact | Early Signals | Mitigation |
|---|------|----------|------------|--------|---------------|------------|
| 1 | **Low tutor supply in key subjects** | Product | High | High | Search results <5 tutors, long wait times | Aggressive recruitment, subject-specific incentives |
| 2 | **Payment fraud / chargebacks** | Tech | Medium | High | Chargeback rate >1%, suspicious patterns | Stripe Radar, velocity limits, manual review queue |
| 3 | **Tutor quality variance** | Product | High | Medium | Low ratings, complaints, refund requests | Verification, trial sessions, quality badges |
| 4 | **Platform abuse (spam, scams)** | Trust | Medium | High | Fake profiles, off-platform solicitation | Content moderation, rate limits, phone verification |
| 5 | **Data breach / security incident** | Tech | Low | Critical | Unusual access patterns, vulnerability reports | Security audits, penetration testing, incident response plan |
| 6 | **Competitor price war** | Business | Medium | Medium | Market rate decreases, tutor churn to competitors | Emphasize value (quality, UX), tutor loyalty programs |
| 7 | **Regulatory compliance (GDPR, CCPA)** | Legal | Medium | High | Complaints, regulatory inquiries | Privacy by design, DPO, legal review |
| 8 | **Payment provider issues (Stripe)** | Tech | Low | High | API degradation, account suspension | Monitor Stripe status, backup processor (Adyen) |
| 9 | **Child safety incident (K-12)** | Trust | Low | Critical | Report of inappropriate behavior | Background checks, session monitoring, rapid response |
| 10 | **Technical debt accumulation** | Tech | High | Medium | Slow velocity, frequent bugs, developer complaints | Dedicated tech debt sprints, architecture reviews |
| 11 | **Key person dependency** | Ops | Medium | Medium | Single points of failure in knowledge | Documentation, cross-training, redundancy |
| 12 | **Tutor no-show epidemic** | Product | Medium | Medium | No-show rate >5%, student complaints | Penalties, reliability scoring, auto-replacement |
| 13 | **Student churn after first session** | Product | High | Medium | <30% rebook rate, negative reviews | Improved matching, follow-up, incentives |
| 14 | **International expansion complexity** | Business | Medium | Medium | Compliance issues, localization bugs | Phased rollout, local legal counsel |
| 15 | **AI matching fails to improve conversion** | Product | Medium | Medium | No lift in A/B test, user complaints | Fallback to rule-based, iterate on algorithm |

### 11.2 Hard Problems Deep Dive

#### Problem 1: AI Tutor Matching (Cold Start)

**Challenge**: New students have no history; new tutors have no reviews.

**Approach**:
1. **Explicit preferences**: Ask students about learning style, goals, budget
2. **Implicit signals**: Search behavior, profile views, message content
3. **Tutor features**: Subjects, experience, response time, rating, price
4. **Collaborative filtering**: "Students like you also booked..."
5. **Exploration/exploitation**: Balance showing proven tutors vs new tutors

**Fallback**: Rule-based matching (subject + price + availability + rating)

#### Problem 2: Two-Sided Marketplace Balance

**Challenge**: Chicken-and-egg; need tutors to attract students and vice versa.

**Approach**:
1. **Supply-led launch**: Recruit tutors first with guaranteed minimum bookings
2. **Geographic focus**: Start in 2-3 cities with critical mass
3. **Subject focus**: Nail 3-5 high-demand subjects before expanding
4. **Subsidize early**: Discounts for students, bonuses for tutors

#### Problem 3: Trust at Scale

**Challenge**: Quality assurance with thousands of tutors globally.

**Approach**:
1. **Tiered verification**: Basic (ID) → Verified (credentials) → Premium (background check)
2. **Algorithmic quality**: Flag tutors with low ratings, high cancellations
3. **Community moderation**: Trusted users can flag issues
4. **Progressive trust**: New tutors limited to 5 students until track record

---

## 12. Final Deliverables

### 12.1 Product Vision Doc (1 Page)

---

# EduStream Product Vision

**Mission**: Democratize access to quality education by connecting learners worldwide with affordable, vetted tutors.

**Vision**: By 2036, EduStream is the world's largest tutoring marketplace, facilitating 100M+ sessions annually across 150+ countries.

**Target Users**:
- Students (K-12, university, adult learners) seeking affordable, quality tutoring
- Tutors (emerging markets, premium) seeking income and flexible work

**Key Differentiator**: Price/accessibility through global tutor supply and lower commission (10-20% vs competitor's 25-33%)

**Business Model**: Commission on transactions (20% → 15% → 10% based on tutor earnings)

**North Star Metric**: Weekly Active Learners (WAL)

**2026 Goals**:
- 5,000 active tutors
- 20,000 active students
- $500K GMV
- AI matching powering 30% of bookings

**Core Features**:
1. Tutor search & discovery with AI matching
2. Real-time booking with instant confirmation
3. Secure payments with tutor payouts
4. Session packages with volume discounts
5. Real-time messaging and notifications
6. Review system for trust and quality

---

### 12.2 PRD Template: AI Tutor Matching

---

# PRD: AI Tutor Matching

## Overview
AI-powered recommendations to help students find the best tutor for their needs.

## Problem Statement
Students struggle to choose from hundreds of tutors. Current search relies on filters and sorting, leading to decision paralysis and suboptimal matches.

## Goals
- Increase search-to-booking conversion by 20%
- Reduce time-to-first-booking by 30%
- Improve student satisfaction (session ratings) by 0.2 stars

## Non-Goals
- Automated booking without student confirmation
- Replacing search functionality

## User Stories
1. As a student, I receive personalized tutor recommendations based on my profile and preferences
2. As a student, I understand why a tutor is recommended to me
3. As a student, I can provide feedback to improve recommendations

## Requirements

### Functional
| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | Display "Recommended for you" carousel on search results | P0 |
| F2 | Show match score (0-100) with explanation | P0 |
| F3 | Consider subject, price, availability, rating, language | P0 |
| F4 | Personalize based on past bookings and preferences | P1 |
| F5 | "Not interested" feedback mechanism | P1 |
| F6 | A/B testable via feature flag | P0 |

### Non-Functional
| ID | Requirement | Priority |
|----|-------------|----------|
| N1 | Recommendations load in <500ms | P0 |
| N2 | Fallback to rule-based if ML unavailable | P0 |
| N3 | Model retraining weekly | P1 |

## Design
[Link to Figma mockups]

## Technical Approach
- Feature store: PostgreSQL (existing data) + Redis (real-time)
- Model: Gradient boosted trees (LightGBM) initially
- Serving: FastAPI endpoint with caching
- Training: Weekly batch job on session outcomes

## Success Metrics
| Metric | Baseline | Target |
|--------|----------|--------|
| Search-to-booking | 4% | 5% |
| Time to first booking | 5 days | 3.5 days |
| Session rating (matched) | 4.3 | 4.5 |

## Risks
- Cold start for new users (mitigate: explicit preferences)
- Filter bubble (mitigate: exploration percentage)

## Timeline
- Week 1-2: Feature engineering, data pipeline
- Week 3-4: Model training, evaluation
- Week 5: API integration, frontend
- Week 6: A/B test launch
- Week 7-8: Monitor, iterate

---

### 12.3 PRD Template: Parent Dashboard

---

# PRD: Parent Dashboard

## Overview
Enable parents to manage their children's tutoring accounts, approve bookings, and monitor progress.

## Problem Statement
K-12 students often have parents booking on their behalf. Current flow requires shared accounts or parents posing as students, creating compliance and UX issues.

## Goals
- Enable COPPA-compliant K-12 tutoring
- Increase K-12 segment by 50%
- Reduce support tickets about family accounts by 80%

## User Stories
1. As a parent, I create and manage my child's account
2. As a parent, I approve/decline booking requests on behalf of my child
3. As a parent, I view my child's session history and progress
4. As a parent, I set spending limits and notification preferences
5. As a child (13+), I browse and request bookings that require parent approval

## Requirements

### Functional
| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | Parent account type with child linking | P0 |
| F2 | Child account creation with DOB verification | P0 |
| F3 | Booking approval workflow | P0 |
| F4 | Parent dashboard with child overview | P0 |
| F5 | Spending limits per child | P1 |
| F6 | Session notes visible to parent | P1 |
| F7 | Child can browse tutors (no booking without approval) | P1 |

### Non-Functional
| ID | Requirement | Priority |
|----|-------------|----------|
| N1 | COPPA compliance (parental consent) | P0 |
| N2 | Clear data separation between parent/child | P0 |

## Success Metrics
| Metric | Baseline | Target |
|--------|----------|--------|
| K-12 registrations | 1000/mo | 1500/mo |
| Family account support tickets | 50/mo | 10/mo |

---

### 12.4 Technical Design Doc Outline

---

# TDD: AI Tutor Matching System

## 1. Overview
Design for personalized tutor recommendation engine.

## 2. Background
Current state: Filter + sort search
Problem: Low conversion, decision paralysis

## 3. Goals & Non-Goals
Goals: +20% conversion, <500ms latency
Non-Goals: Automated booking, real-time model updates

## 4. High-Level Design
```
Student Profile + Search Context
         │
         ▼
┌─────────────────────┐
│   Feature Service   │  ← Real-time features (Redis)
│                     │  ← Static features (PostgreSQL)
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Ranking Model     │  ← LightGBM model
│                     │  ← Served via FastAPI
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   Result Blender    │  ← Mix ML + rule-based
│                     │  ← Apply business rules
└─────────────────────┘
         │
         ▼
    Top N Tutors
```

## 5. Detailed Design

### 5.1 Feature Engineering
- Student: subjects of interest, price sensitivity, timezone, past bookings
- Tutor: subjects, price, rating, response time, completion rate
- Cross: subject match, price fit, availability overlap

### 5.2 Model Training
- Training data: Historical bookings with outcomes
- Label: Session completed with rating >= 4
- Features: 50+ signals
- Model: LightGBM (fast, interpretable)

### 5.3 Serving Architecture
- Endpoint: GET /api/recommendations?user_id=X&subject=Y
- Cache: 5-minute TTL per user-subject pair
- Fallback: Rule-based (subject + rating + price)

## 6. Data Model Changes
```sql
CREATE TABLE recommendation_feedback (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    tutor_id INT REFERENCES tutor_profiles(id),
    feedback VARCHAR(20), -- 'clicked', 'booked', 'not_interested'
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 7. API Changes
```yaml
GET /api/recommendations:
  params:
    - subject_id (optional)
    - limit (default 10)
  response:
    - tutors: [{id, match_score, match_reasons}]
```

## 8. Testing Strategy
- Unit: Feature extraction, model inference
- Integration: API endpoint, caching
- A/B: 50/50 split, 2-week test

## 9. Monitoring
- Recommendation latency P95
- Model prediction distribution
- Click-through rate on recommendations
- Booking rate (recommended vs organic)

## 10. Rollout Plan
- Week 1: Shadow mode (log predictions, don't show)
- Week 2: 10% of users
- Week 3: 50% of users
- Week 4: 100% (if metrics positive)

---

### 12.5 90-Day Execution Plan

---

# 90-Day Plan: Launch & Stabilize

## Month 1: Stabilization (Weeks 1-4)

### Week 1: Assessment & Planning
- [ ] Audit all P0/P1 bugs in backlog
- [ ] Set up error monitoring (Sentry)
- [ ] Create launch checklist
- [ ] Define success metrics

### Week 2: Bug Fixes
- [ ] Fix critical state machine edge cases
- [ ] Resolve payment flow issues
- [ ] Fix timezone display bugs
- [ ] Address mobile responsiveness issues

### Week 3: Testing & Performance
- [ ] Increase test coverage to 80%
- [ ] Load test (100 concurrent users)
- [ ] Fix identified performance bottlenecks
- [ ] Database query optimization

### Week 4: Documentation & Process
- [ ] Update API documentation
- [ ] Create runbooks for common issues
- [ ] Set up on-call rotation
- [ ] Finalize support processes

## Month 2: Launch Prep (Weeks 5-8)

### Week 5: Tutor Recruitment
- [ ] Launch tutor recruitment campaign
- [ ] Onboard 100 tutors (target subjects)
- [ ] Create tutor onboarding content
- [ ] Set up tutor support channel

### Week 6: Landing Page & SEO
- [ ] A/B test landing page variants
- [ ] Implement SEO meta tags
- [ ] Create subject-specific landing pages
- [ ] Set up Google Search Console

### Week 7: Email Automation
- [ ] Welcome sequence (3 emails)
- [ ] Booking reminder emails
- [ ] Post-session follow-up
- [ ] Winback sequence (inactive users)

### Week 8: Analytics Setup
- [ ] Implement event tracking
- [ ] Set up funnel dashboards
- [ ] Configure alerting
- [ ] Create weekly report template

## Month 3: Growth (Weeks 9-13)

### Week 9: Soft Launch
- [ ] Launch to beta users (500)
- [ ] Monitor metrics daily
- [ ] Rapid bug fixes
- [ ] Gather feedback

### Week 10: Marketing Push
- [ ] Launch social media campaigns
- [ ] Begin content marketing
- [ ] Influencer outreach
- [ ] PR for launch

### Week 11: Referral Program
- [ ] Implement basic referral system
- [ ] $10 credit for referrer and referee
- [ ] Track referral attribution

### Week 12: Optimization
- [ ] Analyze funnel drop-offs
- [ ] A/B test checkout flow
- [ ] Optimize tutor search ranking
- [ ] Address top user complaints

### Week 13: Review & Plan
- [ ] 90-day retrospective
- [ ] Compile learnings document
- [ ] Plan Phase 2 priorities
- [ ] Celebrate wins

---

### 12.6 Launch Checklist

---

# Launch Readiness Checklist

## Technical

### Infrastructure
- [ ] Production environment stable (99.9% uptime for 2 weeks)
- [ ] Database backups verified
- [ ] SSL certificates valid
- [ ] CDN configured
- [ ] Rate limiting enabled
- [ ] DDoS protection active

### Monitoring
- [ ] Error tracking (Sentry) configured
- [ ] Uptime monitoring (Pingdom/UptimeRobot)
- [ ] Performance dashboards live
- [ ] On-call rotation set
- [ ] Incident response plan documented

### Security
- [ ] Penetration test completed
- [ ] Vulnerability scan clean
- [ ] Security headers configured
- [ ] PII encrypted at rest
- [ ] Audit logging enabled

## Product

### Core Flows
- [ ] Registration → Email verification working
- [ ] Tutor search returning results
- [ ] Booking flow end-to-end tested
- [ ] Payment processing live
- [ ] Payout flow tested
- [ ] Messaging working

### Content
- [ ] Terms of Service published
- [ ] Privacy Policy published
- [ ] Help Center articles (top 20 questions)
- [ ] FAQ page live

## Operations

### Support
- [ ] Support email configured
- [ ] Ticketing system ready
- [ ] Response templates created
- [ ] Escalation process defined

### Legal
- [ ] Business registration complete
- [ ] Payment processor agreement signed
- [ ] Cookie consent implemented
- [ ] GDPR/CCPA processes ready

### Marketing
- [ ] Landing page final
- [ ] Social media accounts created
- [ ] Email campaigns scheduled
- [ ] Press kit prepared

## Go/No-Go Criteria

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Uptime (2 weeks) | 99.9% | | |
| Error rate | <1% | | |
| Payment success | >98% | | |
| Active tutors | 500 | | |
| P0 bugs open | 0 | | |
| P1 bugs open | <5 | | |

**Launch Date**: ____________

**Decision**: [ ] GO  [ ] NO-GO

**Signed Off By**:
- [ ] Engineering Lead
- [ ] Product Lead
- [ ] Operations Lead
- [ ] CEO

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| GMV | Gross Merchandise Value - total value of transactions |
| WAL | Weekly Active Learners - unique students with completed sessions |
| Session | A tutoring appointment (booking that reached COMPLETED) |
| Package | Pre-purchased bundle of sessions |
| Commission | Platform fee as percentage of transaction |
| State Machine | The 4-field booking status system (session/outcome/payment/dispute) |

### B. Assumptions Made

1. **Market**: Global English-speaking is primary; localization can wait
2. **Segment**: All ages (K-12, university, adult) served by same platform
3. **Differentiator**: Price/accessibility is primary value prop
4. **Monetization**: Commission-only model is sufficient
5. **Competition**: Can win on price + UX vs established players
6. **Supply**: Can recruit quality tutors from emerging markets
7. **Technology**: Current stack (FastAPI/Next.js) scales to $10M GMV

### C. Open Questions

1. Background check provider for international tutors?
2. Video platform strategy (Zoom vs built-in)?
3. Mobile app timing (when to invest)?
4. Enterprise sales timing and approach?
5. Content/curriculum offerings (beyond tutoring)?

---

**Document Owner**: Product Team
**Last Updated**: January 2026
**Review Cadence**: Quarterly
