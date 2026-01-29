# Domain Model & Bounded Contexts

## 1. Strategic Domain Analysis

### Domain Classification

```
+------------------------------------------------------------------------------+
|                          CORE DOMAINS (Build In-House)                        |
+------------------------------------------------------------------------------+
|                                                                               |
|  +------------------+  +--------------------+  +-------------------+          |
|  |     BOOKING      |  |     TUTORING       |  |   MARKETPLACE     |          |
|  |                  |  |                    |  |                   |          |
|  | State machine    |  | Tutor profiles,    |  | Search, discovery |          |
|  | for session      |  | subjects, packages |  | matching, quality |          |
|  | lifecycle        |  | availability mgmt  |  | signals (reviews) |          |
|  +------------------+  +--------------------+  +-------------------+          |
|                                                                               |
+------------------------------------------------------------------------------+
|                       SUPPORTING DOMAINS (Build)                              |
+------------------------------------------------------------------------------+
|                                                                               |
|  +------------------+  +--------------------+                                 |
|  |  COMMUNICATION   |  |    ANALYTICS       |                                 |
|  |                  |  |                    |                                 |
|  | Real-time        |  | Owner dashboard,   |                                 |
|  | messaging,       |  | tutor metrics      |                                 |
|  | notifications    |  |                    |                                 |
|  +------------------+  +--------------------+                                 |
|                                                                               |
+------------------------------------------------------------------------------+
|                       GENERIC DOMAINS (Buy/Outsource)                         |
+------------------------------------------------------------------------------+
|                                                                               |
|  +------------------+  +--------------------+  +-------------------+          |
|  |    IDENTITY      |  |     PAYMENTS       |  |   VIDEO CONF      |          |
|  |                  |  |                    |  |                   |          |
|  | JWT + OAuth      |  | Stripe Connect     |  | Zoom integration  |          |
|  +------------------+  +--------------------+  +-------------------+          |
|                                                                               |
+------------------------------------------------------------------------------+
```

### Domain Justification

| Domain | Classification | Justification |
|--------|---------------|---------------|
| Booking | Core | Competitive differentiator, complex state management |
| Tutoring | Core | Unique to marketplace, custom matching logic |
| Marketplace | Core | Discovery and quality define user experience |
| Communication | Supporting | Necessary but not differentiating |
| Analytics | Supporting | Business intelligence, can use off-shelf tools |
| Identity | Generic | OAuth standards, no custom logic needed |
| Payments | Generic | Stripe handles complexity, compliance |
| Video | Generic | Zoom provides reliable infrastructure |

## 2. Bounded Context Map

```
                    +---------------------------------------+
                    |           IDENTITY CONTEXT            |
                    |  (Auth, OAuth, JWT, User roles)       |
                    +-------------------+-------------------+
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
                    v                   v                   v
+----------------------+  +-------------------+  +----------------------+
|   TUTORING CONTEXT   |  |  STUDENT CONTEXT  |  |    ADMIN CONTEXT     |
|                      |  |                   |  |                      |
| Tutor profiles       |  | Student profiles  |  | Approvals            |
| Certifications       |  | Learning goals    |  | Audit logs           |
| Availability         |  | Credit balance    |  | User management      |
| Pricing options      |  | Favorites         |  | Reports              |
+----------+-----------+  +--------+----------+  +----------+-----------+
           |                       |                        |
           +-----------+-----------+------------------------+
                       |
                       v
           +---------------------------+
           |     BOOKING CONTEXT       | <---- Core Domain
           |                           |
           | Sessions, state machine,  |
           | cancellations, no-shows,  |
           | disputes                  |
           +-------------+-------------+
                         |
           +-------------+-------------+
           |             |             |
           v             v             v
+----------------+  +-----------+  +----------------------+
| PAYMENT CONTEXT|  |  PACKAGE  |  | COMMUNICATION CONTEXT|
|                |  |  CONTEXT  |  |                      |
| Stripe Connect |  | Session   |  | Messages             |
| Payments       |  | bundles   |  | Notifications        |
| Refunds        |  | Validity  |  | WebSocket presence   |
| Payouts        |  | Credits   |  |                      |
+----------------+  +-----------+  +----------------------+
```

### Context Relationships

| Upstream | Downstream | Relationship | Integration |
|----------|------------|--------------|-------------|
| Identity | All | Conformist | JWT token, role checks |
| Booking | Payment | Customer-Supplier | Booking creates payment intent |
| Booking | Package | Customer-Supplier | Booking consumes credits |
| Booking | Communication | Publisher-Subscriber | State changes trigger notifications |
| Tutoring | Booking | Shared Kernel | TutorProfile, pricing shared |

## 3. Aggregate Design

### 3.1 Booking Aggregate (Most Complex)

```
+------------------------------------------------------------------+
|                    BOOKING AGGREGATE                              |
|                    (Aggregate Root: Booking)                      |
+------------------------------------------------------------------+
|                                                                   |
|  Booking                                                          |
|  +-- id (identity)                                                |
|  +-- session_state (REQUESTED -> SCHEDULED -> ACTIVE -> ENDED)    |
|  +-- session_outcome (COMPLETED, NO_SHOW_*, NOT_HELD)             |
|  +-- payment_state (PENDING -> AUTHORIZED -> CAPTURED)            |
|  +-- dispute_state (NONE -> OPEN -> RESOLVED_*)                   |
|  +-- cancelled_by_role (value object)                             |
|  +-- TimeRange [start_time, end_time] (value object)              |
|  +-- PricingSnapshot [rate_cents, fee, earnings] (value object)   |
|  +-- SessionMaterial[] (entity)                                   |
|                                                                   |
|  Invariants:                                                      |
|  - Cannot transition to invalid state                             |
|  - Cannot dispute non-terminal sessions                           |
|  - Cannot cancel after session starts                             |
|  - Payment state must align with session state                    |
|                                                                   |
+------------------------------------------------------------------+
```

### 3.2 TutorProfile Aggregate

```
+------------------------------------------------------------------+
|                 TUTOR PROFILE AGGREGATE                           |
|                 (Aggregate Root: TutorProfile)                    |
+------------------------------------------------------------------+
|                                                                   |
|  TutorProfile                                                     |
|  +-- id (identity)                                                |
|  +-- profile_status (INCOMPLETE -> PENDING -> APPROVED)           |
|  +-- hourly_rate (value object with currency)                     |
|  +-- TutorSubject[] (entity, subject specializations)             |
|  +-- TutorCertification[] (entity, credentials)                   |
|  +-- TutorEducation[] (entity, background)                        |
|  +-- TutorAvailability[] (entity, weekly slots)                   |
|  +-- TutorBlackout[] (entity, vacation periods)                   |
|  +-- TutorPricingOption[] (entity, packages)                      |
|                                                                   |
|  Invariants:                                                      |
|  - Cannot accept bookings until approved                          |
|  - Availability slots cannot overlap                              |
|  - Pricing options must have positive values                      |
|                                                                   |
+------------------------------------------------------------------+
```

### 3.3 User Aggregate

```
+------------------------------------------------------------------+
|                      USER AGGREGATE                               |
|                      (Aggregate Root: User)                       |
+------------------------------------------------------------------+
|                                                                   |
|  User                                                             |
|  +-- id (identity)                                                |
|  +-- email (unique, normalized)                                   |
|  +-- role (student | tutor | admin | owner)                       |
|  +-- UserProfile (entity, extended info)                          |
|  +-- NotificationPreferences (entity)                             |
|                                                                   |
|  Invariants:                                                      |
|  - Email must be unique and valid format                          |
|  - Role cannot change after creation (except admin promotion)     |
|                                                                   |
+------------------------------------------------------------------+
```

### 3.4 StudentPackage Aggregate

```
+------------------------------------------------------------------+
|                  STUDENT PACKAGE AGGREGATE                        |
|                  (Aggregate Root: StudentPackage)                 |
+------------------------------------------------------------------+
|                                                                   |
|  StudentPackage                                                   |
|  +-- id (identity)                                                |
|  +-- sessions_purchased (immutable after creation)                |
|  +-- sessions_remaining (decremented on booking)                  |
|  +-- sessions_used (incremented on completion)                    |
|  +-- expires_at (validity period)                                 |
|  +-- status (active | expired | exhausted | refunded)             |
|                                                                   |
|  Invariants:                                                      |
|  - sessions_remaining = sessions_purchased - sessions_used        |
|  - Cannot use expired packages                                    |
|  - Cannot exceed purchased sessions                               |
|                                                                   |
+------------------------------------------------------------------+
```

## 4. Value Objects

| Value Object | Properties | Used In |
|--------------|------------|---------|
| EmailAddress | email (validated format) | User |
| TimeRange | start_time, end_time | Booking, Availability |
| Money | amount_cents, currency | Pricing, Payments |
| SessionState | enum value | Booking |
| PaymentState | enum value | Booking |
| DisputeState | enum value | Booking |
| PricingSnapshot | rate, fee, earnings | Booking |

## 5. Invariant Enforcement

| Invariant | Layer | Mechanism | Justification |
|-----------|-------|-----------|---------------|
| State transitions | Domain (Python) | BookingStateMachine class | Complex rules, testable |
| Unique email | Database | UNIQUE constraint | Race condition protection |
| Availability overlap | Application | Query + validate | Cross-aggregate check |
| Pricing > 0 | Database + App | CHECK + validation | Defense in depth |
| Time ordering | Database | CHECK constraint | Data integrity |
| FK integrity | Database | Foreign keys | Referential integrity |
| Soft delete cascade | Application | Service methods | Audit trail control |

## 6. Domain Events (Conceptual)

While not currently implemented as explicit events, these state changes have side effects:

| Event | Trigger | Side Effects |
|-------|---------|--------------|
| BookingRequested | Student creates booking | Notify tutor, log response tracking |
| BookingConfirmed | Tutor accepts | Notify student, authorize payment |
| BookingCancelled | Either party cancels | Process refund, restore credits |
| SessionStarted | Scheduled time reached | Update session state |
| SessionEnded | End time + grace passed | Capture payment, prompt review |
| DisputeOpened | User files dispute | Notify admin |
| TutorApproved | Admin approves | Notify tutor, enable bookings |

**Future Enhancement**: Implement explicit domain events with event sourcing for better audit trails and decoupling.

## 7. Anti-Corruption Layers

### Stripe Integration

```python
# core/stripe_client.py acts as ACL
class StripeClient:
    def create_payment_intent(self, amount_cents, currency, metadata) -> PaymentIntent:
        # Translates domain concepts to Stripe API

    def create_refund(self, payment_intent_id, amount_cents) -> Refund:
        # Handles Stripe-specific error codes
```

### External Calendar Integration

```python
# core/google_calendar.py acts as ACL
class GoogleCalendarClient:
    def create_event(self, booking: Booking) -> str:
        # Maps Booking aggregate to Google Calendar event format

    def delete_event(self, event_id: str) -> None:
        # Handles Google API specifics
```

## 8. Module Dependencies

```
                    +----------------+
                    |     core/      |
                    | (dependencies, |
                    |  security,     |
                    |  utils, etc.)  |
                    +-------+--------+
                            |
                            | used by all
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
+---------------+  +------------------+  +---------------+
|     auth      |<-|     bookings     |->|   payments    |
|               |  |                  |  |               |
| Provides:     |  | Consumes:        |  | Provides:     |
|  - JWT tokens |  |  - User identity |  |  - Checkout   |
|  - OAuth flow |  |  - Tutor profile |  |  - Refunds    |
|  - Roles      |  |  - Package credit|  |  - Payouts    |
+---------------+  |  - Payment intent|  +---------------+
                   +--------+---------+
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
+---------------+  +------------------+  +---------------+
|   packages    |  |  notifications   |  |   messages    |
+---------------+  +------------------+  +---------------+
```

### Coupling Risk Assessment

| Module | Afferent (incoming) | Efferent (outgoing) | Risk |
|--------|---------------------|---------------------|------|
| core/ | All modules | 0 | Low (utility) |
| auth/ | All modules | core/ | Low (foundational) |
| bookings/ | 2 | 6+ | **High (hub)** |
| payments/ | 1 | core/, stripe | Medium |
| notifications/ | 1 | core/, email | Low |

**Recommendation**: Introduce domain events to decouple `bookings` from downstream consumers.
