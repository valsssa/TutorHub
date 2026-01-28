# Refund Logic Analysis

**Status:** 🔴 Not Started  
**Priority:** High  
**Related Task:** Payment Endpoints Implementation (API_DATABASE_COMPATIBILITY_TODO.md)

---

## Overview

This document describes the complete refund logic in the booking system, including policy rules, refund triggers, status transitions, and the relationship between refunds and booking statuses.

---

## Refund Policy Rules

**Location:** `backend/modules/bookings/policy_engine.py` (CancellationPolicy class)

### Policy Constants

```python
FREE_CANCEL_WINDOW_HOURS = 12  # 12-hour cancellation window
TUTOR_CANCEL_PENALTY_CENTS = 500  # $5 compensation for late tutor cancellation
```

### 1. Student Cancellation Policy

**Method:** `CancellationPolicy.evaluate_student_cancellation()`

#### Rules:

| Timing | Refund Amount | Package Credit | Notes |
|--------|---------------|----------------|-------|
| **≥ 12 hours before** | Full refund (100%) | Restored | Full package credit restored if package booking |
| **< 12 hours before** | No refund (0%) | Not restored | Credit lost, no refund |
| **Already started** | Not allowed | N/A | Cannot cancel after session starts |

#### Implementation Logic:

```python
if time_until_start <= 0:
    # Already started - not allowed
    return PolicyDecision(allow=False, reason_code="ALREADY_STARTED")

if hours_until_start >= 12:
    # Full refund or package credit restoration
    return PolicyDecision(
        allow=True,
        refund_cents=rate_cents if not is_package else 0,
        restore_package_unit=is_package,
        message="Cancelled with full refund/credit restoration"
    )
else:
    # < 12h - no refund
    return PolicyDecision(
        allow=True,
        refund_cents=0,
        restore_package_unit=False,
        message="Cancelled within 12h window. No refund available."
    )
```

---

### 2. Tutor Cancellation Policy

**Method:** `CancellationPolicy.evaluate_tutor_cancellation()`

#### Rules:

| Timing | Student Refund | Package Credit | Tutor Penalty | Strike Applied |
|--------|----------------|----------------|---------------|----------------|
| **≥ 12 hours before** | Full refund (100%) | Restored | None | No |
| **< 12 hours before** | Full refund (100%) + $5 compensation | Restored | $5 compensation | Yes |
| **Already started** | Not allowed | N/A | N/A | N/A |

#### Implementation Logic:

```python
if hours_until_start >= 12:
    # Early cancellation - no penalty
    return PolicyDecision(
        allow=True,
        refund_cents=rate_cents if not is_package else 0,
        restore_package_unit=is_package,
        tutor_compensation_cents=0,
        apply_strike_to_tutor=False,
        message="Tutor cancelled with sufficient notice"
    )
else:
    # Late cancellation - penalty applied
    return PolicyDecision(
        allow=True,
        refund_cents=rate_cents if not is_package else 0,
        restore_package_unit=is_package,
        tutor_compensation_cents=500,  # $5 compensation
        apply_strike_to_tutor=True,
        message="Tutor cancelled within 12h. Student compensated."
    )
```

---

### 3. No-Show Policy

**Location:** `backend/modules/bookings/policy_engine.py` (NoShowPolicy class)

#### Rules:

| Scenario | Student Refund | Tutor Payment | Tutor Penalty | Strike Applied |
|----------|----------------|---------------|---------------|----------------|
| **Student No-Show** (reported by tutor) | No refund (0%) | Full payment | None | No |
| **Tutor No-Show** (reported by student) | Full refund (100%) | No payment | Strike applied | Yes |

#### Grace Period & Report Window:

- **Grace Period:** 10 minutes after session start time
- **Report Window:** Must report within 24 hours of session start
- **Too Early:** Cannot report within 10 minutes (wait for grace period)
- **Too Late:** Cannot report after 24 hours

#### Implementation Logic:

```python
# Student No-Show (reported by tutor)
if reporter_role == "TUTOR":
    return PolicyDecision(
        allow=True,
        message="Student no-show confirmed. Tutor will be paid."
        # No refund, no penalty
    )

# Tutor No-Show (reported by student)
else:  # STUDENT
    return PolicyDecision(
        allow=True,
        apply_strike_to_tutor=True,
        message="Tutor no-show confirmed. Refund issued."
        # Full refund, strike applied
    )
```

---

## Refund Status Transitions

**Location:** `backend/core/config.py` (BookingStatus.TRANSITIONS), `backend/modules/bookings/service.py` (VALID_TRANSITIONS)

### Valid Transitions to REFUNDED

```
CANCELLED_BY_STUDENT → REFUNDED
CANCELLED_BY_TUTOR → REFUNDED
NO_SHOW_TUTOR → REFUNDED
COMPLETED → REFUNDED (exception via admin only)
```

### Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Refund Status Flow                         │
└─────────────────────────────────────────────────────────────┘

                    [Booking Created]
                           │
                           ▼
                    ┌──────────┐
                    │  PENDING │
                    └──────────┘
                           │
                           ▼
                    ┌──────────┐
                    │ CONFIRMED│
                    └──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│CANCELLED_BY   │  │CANCELLED_BY   │  │NO_SHOW_TUTOR  │
│_STUDENT       │  │_TUTOR         │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ▼
                    ┌──────────┐
                    │ REFUNDED │
                    └──────────┘
                           │
                    (Terminal State)

Exception Path:
┌──────────┐
│COMPLETED │ → (Admin Only) → ┌──────────┐
└──────────┘                  │ REFUNDED │
                              └──────────┘
```

---

## Refund Database Schema

**Location:** `database/init.sql` (lines 451-469), `backend/models/payments.py` (Refund model)

### Refund Table Structure

```sql
CREATE TABLE refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    booking_id INTEGER REFERENCES bookings(id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    reason VARCHAR(30) NOT NULL,
    provider_refund_id TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_refund_reason CHECK (
        reason IN (
            'STUDENT_CANCEL',
            'TUTOR_CANCEL',
            'NO_SHOW_TUTOR',
            'GOODWILL',
            'OTHER'
        )
    )
);
```

### Refund Reasons

| Reason Code | Description | When Used |
|-------------|-------------|-----------|
| `STUDENT_CANCEL` | Student cancelled booking | Student cancellation (≥12h = refund, <12h = no refund) |
| `TUTOR_CANCEL` | Tutor cancelled booking | Tutor cancellation (always full refund) |
| `NO_SHOW_TUTOR` | Tutor didn't attend | Student reports tutor no-show |
| `GOODWILL` | Goodwill refund | Admin-issued refund for quality issues |
| `OTHER` | Other reasons | Manual refunds, exceptions |

---

## Refund Processing Flow

### Current Implementation Status

**⚠️ Note:** The actual refund processing (creating Refund records and updating booking status to `REFUNDED`) is **not yet implemented**. The policy engine determines refund eligibility, but the actual payment processing and status update is missing.

**Missing Implementation:**
- `POST /api/refunds` endpoint (listed in TODO)
- Payment provider integration (Stripe/Adyen/PayPal)
- Automatic refund processing after cancellation
- Booking status update to `REFUNDED`

### Expected Flow (When Implemented)

#### 1. Student Cancellation (≥12h before)

```
1. Student cancels booking
   ↓
2. BookingService.cancel_booking() called
   ↓
3. CancellationPolicy.evaluate_student_cancellation()
   → Returns: refund_cents = full_amount, restore_package_unit = true
   ↓
4. Booking status updated to: CANCELLED_BY_STUDENT
   ↓
5. If package booking:
   → Restore package credit (decrement lessons_used)
   ↓
6. If regular booking (not package):
   → Create Refund record
   → Process refund via payment provider (Stripe)
   → Update booking status to: REFUNDED
   → Update payment status to: REFUNDED
```

#### 2. Student Cancellation (<12h before)

```
1. Student cancels booking
   ↓
2. BookingService.cancel_booking() called
   ↓
3. CancellationPolicy.evaluate_student_cancellation()
   → Returns: refund_cents = 0, restore_package_unit = false
   ↓
4. Booking status updated to: CANCELLED_BY_STUDENT
   ↓
5. No refund processed
   ↓
6. Booking remains in CANCELLED_BY_STUDENT status (not REFUNDED)
```

#### 3. Tutor Cancellation (Any time)

```
1. Tutor cancels booking
   ↓
2. BookingService.cancel_booking() called
   ↓
3. CancellationPolicy.evaluate_tutor_cancellation()
   → Returns: refund_cents = full_amount, tutor_compensation_cents (if <12h)
   ↓
4. Booking status updated to: CANCELLED_BY_TUTOR
   ↓
5. If <12h before:
   → Apply strike to tutor profile
   → Record $5 compensation
   ↓
6. Process refund:
   → Create Refund record (reason: TUTOR_CANCEL)
   → Process refund via payment provider
   → Update booking status to: REFUNDED
   → Update payment status to: REFUNDED
```

#### 4. Tutor No-Show (Reported by Student)

```
1. Student reports tutor no-show
   ↓
2. BookingService.mark_no_show() called
   ↓
3. NoShowPolicy.evaluate_no_show_report()
   → Returns: apply_strike_to_tutor = true
   ↓
4. Booking status updated to: NO_SHOW_TUTOR
   ↓
5. Apply strike to tutor profile
   ↓
6. Process refund:
   → Create Refund record (reason: NO_SHOW_TUTOR)
   → Process refund via payment provider
   → Update booking status to: REFUNDED
   → Update payment status to: REFUNDED
```

#### 5. Student No-Show (Reported by Tutor)

```
1. Tutor reports student no-show
   ↓
2. BookingService.mark_no_show() called
   ↓
3. NoShowPolicy.evaluate_no_show_report()
   → Returns: (no refund, no penalty)
   ↓
4. Booking status updated to: NO_SHOW_STUDENT
   ↓
5. No refund processed
   ↓
6. Tutor receives full payment
   ↓
7. Booking remains in NO_SHOW_STUDENT status (not REFUNDED)
```

#### 6. Admin Exception Refund (COMPLETED → REFUNDED)

```
1. Admin initiates refund for completed booking
   ↓
2. Admin endpoint: POST /api/admin/bookings/{id}/refund
   ↓
3. Validate: booking.status == COMPLETED
   ↓
4. Create Refund record (reason: GOODWILL or OTHER)
   ↓
5. Process refund via payment provider
   ↓
6. Update booking status to: REFUNDED
   ↓
7. Update payment status to: REFUNDED
```

---

## Refund Amount Calculation

### Regular Bookings (Not Package)

```python
# Full refund
refund_amount = booking.total_amount

# Partial refund (if configured in future)
refund_amount = booking.total_amount * (refund_percentage / 100)
```

### Package Bookings

```python
# Package credit restoration (no payment refund)
if decision.restore_package_unit:
    package.lessons_used = package.lessons_used - 1
    # No refund record created
else:
    # Credit lost, no refund
    # No refund record created
```

### Tutor Compensation (Late Tutor Cancellation)

```python
# Student receives full refund
student_refund = booking.total_amount

# Student receives additional compensation
compensation = 500  # $5.00 in cents

# Total student credit = refund + compensation
total_student_credit = student_refund + compensation
```

---

## Package Credit Restoration

**Location:** `backend/modules/bookings/service.py` (cancel_booking method)

### When Package Credit is Restored

| Scenario | Credit Restored | Refund Processed |
|----------|-----------------|------------------|
| Student cancels ≥12h before | ✅ Yes | ❌ No (package credit restored instead) |
| Student cancels <12h before | ❌ No | ❌ No (credit lost) |
| Tutor cancels (any time) | ✅ Yes | ❌ No (package credit restored instead) |
| Tutor no-show | ✅ Yes | ❌ No (package credit restored instead) |

### Implementation

```python
if decision.restore_package_unit and booking.package_id:
    package = db.query(StudentPackage).filter(
        StudentPackage.id == booking.package_id
    ).first()
    
    if package and package.lessons_used > 0:
        package.lessons_used = package.lessons_used - 1
        # Credit restored, no refund record needed
```

---

## Refund Timing Rules Summary

| Scenario | Timing | Refund Amount | Package Credit | Status After |
|----------|--------|---------------|----------------|--------------|
| **Student cancels** | ≥12h before | 100% | Restored | CANCELLED_BY_STUDENT → REFUNDED |
| **Student cancels** | <12h before | 0% | Lost | CANCELLED_BY_STUDENT (not refunded) |
| **Tutor cancels** | ≥12h before | 100% | Restored | CANCELLED_BY_TUTOR → REFUNDED |
| **Tutor cancels** | <12h before | 100% + $5 | Restored | CANCELLED_BY_TUTOR → REFUNDED |
| **Tutor no-show** | After grace period | 100% | Restored | NO_SHOW_TUTOR → REFUNDED |
| **Student no-show** | After grace period | 0% | Lost | NO_SHOW_STUDENT (not refunded) |
| **Admin exception** | Anytime | Variable | N/A | COMPLETED → REFUNDED |

---

## Missing Implementation Details

### 1. Payment Provider Integration

**Status:** ❌ Not Implemented

**Required:**
- Stripe/Adyen/PayPal integration
- Refund API calls to payment provider
- Webhook handling for refund status updates
- Provider refund ID storage

**Location:** `backend/modules/payments/` (to be created)

### 2. Refund Endpoint

**Status:** ❌ Not Implemented

**Required:**
- `POST /api/refunds` endpoint
- Refund request validation
- Payment provider refund processing
- Booking status update to `REFUNDED`

**Location:** `backend/modules/payments/presentation/api.py` (to be created)

### 3. Automatic Refund Processing

**Status:** ❌ Not Implemented

**Required:**
- Automatic refund after cancellation (when eligible)
- Background job for refund processing
- Retry logic for failed refunds
- Refund status tracking

**Location:** `backend/modules/payments/application/services.py` (to be created)

### 4. Admin Refund Endpoint

**Status:** ❌ Not Implemented

**Required:**
- `POST /api/admin/bookings/{id}/refund` endpoint
- Admin-only access
- Exception refund processing
- Goodwill refund support

**Location:** `backend/modules/admin/presentation/api.py` (to be added)

---

## Files to Review/Update

1. **`backend/modules/bookings/policy_engine.py`** - ✅ Policy logic implemented
2. **`backend/modules/bookings/service.py`** - ✅ Cancellation logic implemented, ❌ Refund processing missing
3. **`backend/modules/payments/`** - ❌ Payment service module missing (to be created)
4. **`database/init.sql`** - ✅ Refund table schema exists
5. **`backend/models/payments.py`** - ✅ Refund model exists
6. **`docs/API_REFERENCE.md`** - ❌ Refund endpoints not documented

---

## Acceptance Criteria

- [ ] Payment provider integration (Stripe/Adyen/PayPal)
- [ ] `POST /api/refunds` endpoint implemented
- [ ] Automatic refund processing after eligible cancellations
- [ ] Booking status updates to `REFUNDED` after refund processed
- [ ] Refund records created in database
- [ ] Package credit restoration working correctly
- [ ] Tutor compensation for late cancellations
- [ ] Admin exception refund endpoint
- [ ] Refund webhook handling
- [ ] Refund status tracking and retry logic

---

**Last Updated:** January 24, 2026  
**Status:** 🔴 Not Started
