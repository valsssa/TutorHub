# Booking Status Flow Analysis

**Status:** 🔴 Not Started  
**Priority:** High  
**Related Task:** Booking Status Inconsistencies (API_DATABASE_COMPATIBILITY_TODO.md)

---

## Overview

This document describes the flow of booking statuses in the system, when they are shown, when they are not, and the inconsistencies that need to be fixed.

---

## Database Status Values (Source of Truth)

The database constraint defines **8 valid status values**:

1. **`PENDING`** - Created by student, awaiting tutor confirmation
2. **`CONFIRMED`** - Live session scheduled (tutor confirmed or auto-confirmed)
3. **`CANCELLED_BY_STUDENT`** - Student cancelled the booking
4. **`CANCELLED_BY_TUTOR`** - Tutor cancelled the booking
5. **`NO_SHOW_STUDENT`** - Student didn't attend (reported by tutor)
6. **`NO_SHOW_TUTOR`** - Tutor didn't attend (reported by student)
7. **`COMPLETED`** - Session finished successfully
8. **`REFUNDED`** - Payment refunded (terminal financial state)

**Location:** `database/init.sql` (line 370-377), `database/migrations/004_update_booking_status_constraint.sql`

---

## Status State Machine (Valid Transitions)

**Location:** `backend/core/config.py` (BookingStatus class), `backend/modules/bookings/service.py` (VALID_TRANSITIONS)

### State Transition Rules

```
PENDING
  ├─→ CONFIRMED (tutor confirms or auto-confirm enabled)
  ├─→ CANCELLED_BY_STUDENT (student cancels)
  └─→ CANCELLED_BY_TUTOR (tutor cancels)

CONFIRMED
  ├─→ CANCELLED_BY_STUDENT (student cancels)
  ├─→ CANCELLED_BY_TUTOR (tutor cancels)
  ├─→ NO_SHOW_STUDENT (tutor reports after grace window)
  ├─→ NO_SHOW_TUTOR (student reports after grace window)
  └─→ COMPLETED (session finished)

CANCELLED_BY_STUDENT → REFUNDED (automatic or admin action)
CANCELLED_BY_TUTOR → REFUNDED (automatic or admin action)
NO_SHOW_TUTOR → REFUNDED (automatic or admin action)
COMPLETED → REFUNDED (exception via admin only)

Terminal States (no transitions):
  - CANCELLED_BY_STUDENT (unless refunded)
  - CANCELLED_BY_TUTOR (unless refunded)
  - NO_SHOW_STUDENT (terminal)
  - NO_SHOW_TUTOR (unless refunded)
  - REFUNDED (terminal)
```

---

## API Status Filtering (Current Implementation)

**Location:** `backend/modules/bookings/presentation/api.py` (lines 177-198)

### How Status Filters Work

The API accepts a `status` query parameter that maps to database statuses:

#### 1. **`status=upcoming`** (Filter, NOT a status)
**Shown:** Bookings with:
- Status = `PENDING` OR `CONFIRMED`
- AND `start_time >= NOW()` (future sessions)

**Not Shown:**
- Past bookings (even if PENDING/CONFIRMED)
- Completed bookings
- Cancelled bookings
- No-show bookings
- Refunded bookings

**Implementation:**
```python
if status_filter.lower() == "upcoming":
    query = query.filter(
        Booking.status.in_(["PENDING", "CONFIRMED"]),
        Booking.start_time >= datetime.utcnow(),
    )
```

#### 2. **`status=pending`** (Direct status match)
**Shown:** Bookings with status = `PENDING`

**Not Shown:**
- All other statuses
- Past PENDING bookings (still shown, but should be rare)

**Implementation:**
```python
elif status_filter.lower() == "pending":
    query = query.filter(Booking.status == "PENDING")
```

#### 3. **`status=completed`** (Direct status match)
**Shown:** Bookings with status = `COMPLETED`

**Not Shown:**
- All other statuses
- Pending/confirmed bookings
- Cancelled bookings
- No-show bookings
- Refunded bookings

**Implementation:**
```python
elif status_filter.lower() == "completed":
    query = query.filter(Booking.status == "COMPLETED")
```

#### 4. **`status=cancelled`** (Aggregated filter)
**Shown:** Bookings with status IN:
- `CANCELLED_BY_STUDENT`
- `CANCELLED_BY_TUTOR`
- `NO_SHOW_STUDENT`
- `NO_SHOW_TUTOR`

**Not Shown:**
- `PENDING`
- `CONFIRMED`
- `COMPLETED`
- `REFUNDED`

**Implementation:**
```python
elif status_filter.lower() == "cancelled":
    query = query.filter(
        Booking.status.in_([
            "CANCELLED_BY_STUDENT",
            "CANCELLED_BY_TUTOR",
            "NO_SHOW_STUDENT",
            "NO_SHOW_TUTOR",
        ])
    )
```

#### 5. **No status filter** (All bookings)
**Shown:** All bookings for the user (regardless of status)

**Not Shown:** None (all statuses included)

---

## Frontend Status Handling (Current Implementation)

**Location:** `frontend/app/bookings/BookingsPageContent.tsx`, `frontend/types/booking.ts`

### Frontend Status Types

The frontend defines status filters as:
```typescript
type StatusFilter = "upcoming" | "pending" | "completed" | "cancelled";
```

### Frontend Booking Status Type

**Location:** `frontend/types/booking.ts` (lines 6-20)

```typescript
export type BookingStatus =
  | "PENDING"
  | "CONFIRMED"
  | "CANCELLED_BY_STUDENT"
  | "CANCELLED_BY_TUTOR"
  | "NO_SHOW_STUDENT"
  | "NO_SHOW_TUTOR"
  | "COMPLETED"
  | "REFUNDED"
  // Legacy statuses for backward compatibility
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show";
```

**Issue:** Frontend includes both uppercase (correct) and lowercase (legacy) statuses, causing confusion.

### Frontend Tab Configuration

**Location:** `frontend/app/bookings/BookingsPageContent.tsx` (lines 227-232)

```typescript
const tabs = [
  { key: "upcoming" as StatusFilter, label: "Upcoming", count: 0 },
  { key: "pending" as StatusFilter, label: "Pending", count: 0 },
  { key: "completed" as StatusFilter, label: "Completed", count: 0 },
  { key: "cancelled" as StatusFilter, label: "Cancelled", count: 0 },
];
```

### Frontend Status Display Logic

**Location:** `frontend/components/dashboards/StudentDashboard.tsx` (lines 221-232)

```typescript
const isUpcoming =
  booking.status === "CONFIRMED" ||
  booking.status === "confirmed" ||
  booking.status === "PENDING" ||
  booking.status === "pending";

const isCompleted =
  booking.status === "COMPLETED" || booking.status === "completed";

const canJoin =
  isUpcoming &&
  (booking.status === "CONFIRMED" || booking.status === "confirmed") &&
  isJoinable(booking.start_at) &&
  booking.join_url;
```

**Issue:** Frontend checks for both uppercase and lowercase statuses, indicating inconsistent data from backend.

---

## Inconsistencies Identified

### 1. **"upcoming" is a Filter, Not a Status**

**Problem:**
- API documentation and frontend treat `"upcoming"` as if it's a booking status
- Database has no `"upcoming"` status value
- `"upcoming"` is computed from `status IN ('PENDING', 'CONFIRMED') AND start_time > NOW()`

**Impact:**
- Confusion in API documentation
- Frontend may try to filter by `status='upcoming'` which doesn't exist in database
- Users may expect to see `status: "upcoming"` in booking responses

**Fix Required:**
- Remove `"upcoming"` from status documentation
- Clarify in API docs that `"upcoming"` is a computed filter
- Update frontend to understand it's a filter, not a status

---

### 2. **Cancellation Status Aggregation**

**Problem:**
- API filter `status=cancelled` aggregates 4 different statuses:
  - `CANCELLED_BY_STUDENT`
  - `CANCELLED_BY_TUTOR`
  - `NO_SHOW_STUDENT`
  - `NO_SHOW_TUTOR`
- Frontend doesn't differentiate between cancellation types
- No way to filter by specific cancellation reason

**Impact:**
- Can't distinguish who cancelled (student vs tutor)
- Can't distinguish cancellation type (cancelled vs no-show)
- Frontend displays generic "cancelled" label

**Fix Required:**
- Update frontend to display separate cancellation statuses
- Add UI to show cancellation reason (student/tutor/no-show)
- Consider adding separate filters for each cancellation type

---

### 3. **Missing Status Values in API Documentation**

**Problem:**
- API documentation only mentions: `"upcoming"`, `"pending"`, `"completed"`, `"cancelled"`
- Missing documentation for:
  - `NO_SHOW_STUDENT`
  - `NO_SHOW_TUTOR`
  - `REFUNDED`
  - Separate cancellation statuses

**Impact:**
- Developers don't know all available statuses
- API consumers may not handle all status cases
- Frontend may not display all statuses correctly

**Fix Required:**
- Document all 8 status values in API reference
- Add examples showing each status
- Update API response examples

---

### 4. **Backend Status Validation Missing**

**Problem:**
- Backend API doesn't validate status values against database constraint
- Invalid status values could be accepted
- No enum validation in Pydantic schemas

**Impact:**
- Invalid status values could be stored
- Database constraint violation errors at runtime
- Inconsistent data

**Fix Required:**
- Add Pydantic enum validation for status values
- Validate status transitions in service layer
- Return clear error messages for invalid statuses

---

### 5. **Frontend Legacy Status Support**

**Problem:**
- Frontend supports both uppercase and lowercase statuses
- Indicates backend may return inconsistent casing
- Legacy statuses: `"pending"`, `"confirmed"`, `"cancelled"`, `"completed"`, `"no_show"`

**Impact:**
- Code duplication (checking both cases)
- Potential bugs if backend changes casing
- Confusion about which format is correct

**Fix Required:**
- Ensure backend always returns uppercase statuses
- Remove legacy lowercase support from frontend
- Update all status comparisons to use uppercase only

---

## Status Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Booking Status Flow                           │
└─────────────────────────────────────────────────────────────────┘

                    [Student Creates Booking]
                              │
                              ▼
                         ┌─────────┐
                         │ PENDING │
                         └─────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
        │ CONFIRMED   │ │CANCELLED_BY│ │CANCELLED_BY │
        │ (tutor      │ │_STUDENT    │ │_TUTOR       │
        │  confirms)  │ │            │ │             │
        └─────────────┘ └─────────────┘ └─────────────┘
                │             │             │
                │             │             │
                │             └──────┬──────┘
                │                    │
                │                    ▼
                │              ┌──────────┐
                │              │ REFUNDED │
                │              └──────────┘
                │
    ┌───────────┼───────────┬───────────┬───────────┐
    │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│CANCELLED│ │CANCELLED│ │NO_SHOW  │ │NO_SHOW  │ │COMPLETED│
│_BY_     │ │_BY_     │ │_STUDENT │ │_TUTOR   │ │         │
│STUDENT  │ │TUTOR    │ │         │ │         │ │         │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
    │           │           │           │           │
    └───────────┴───────────┴───────────┴───────────┘
                              │
                              ▼
                         ┌──────────┐
                         │ REFUNDED │
                         └──────────┘
```

---

## When Statuses Are Shown vs Not Shown

### Status Visibility by Filter

| Filter | Shows | Doesn't Show |
|--------|-------|-------------|
| `upcoming` | `PENDING` + `CONFIRMED` (future only) | Past bookings, `COMPLETED`, `CANCELLED_*`, `NO_SHOW_*`, `REFUNDED` |
| `pending` | `PENDING` (all) | All other statuses |
| `completed` | `COMPLETED` | All other statuses |
| `cancelled` | `CANCELLED_BY_STUDENT`, `CANCELLED_BY_TUTOR`, `NO_SHOW_STUDENT`, `NO_SHOW_TUTOR` | `PENDING`, `CONFIRMED`, `COMPLETED`, `REFUNDED` |
| *(none)* | All statuses | None |

### Status Visibility by Context

| Context | Shows | Doesn't Show |
|---------|-------|-------------|
| **Student Dashboard** | `PENDING`, `CONFIRMED` (as "upcoming") | Past bookings, completed, cancelled |
| **Tutor Dashboard** | `PENDING` (as "pending requests"), `CONFIRMED` (as "upcoming") | Completed, cancelled (unless filtered) |
| **Booking Details** | All statuses (for owned bookings) | None (all statuses visible) |
| **Admin Dashboard** | All statuses | None (admin sees everything) |

---

## Recommended Fixes

### 1. Update API Documentation
- [ ] Document all 8 status values: `PENDING`, `CONFIRMED`, `CANCELLED_BY_STUDENT`, `CANCELLED_BY_TUTOR`, `NO_SHOW_STUDENT`, `NO_SHOW_TUTOR`, `COMPLETED`, `REFUNDED`
- [ ] Remove `"upcoming"` from status documentation
- [ ] Add section explaining `"upcoming"` is a computed filter (not a status)
- [ ] Update API response examples to show all statuses

### 2. Update Frontend
- [ ] Remove legacy lowercase status support
- [ ] Update status display to show separate cancellation types
- [ ] Add UI badges/labels for each cancellation status
- [ ] Update status filters to handle all 8 statuses

### 3. Add Backend Validation
- [ ] Add Pydantic enum validation for status values
- [ ] Validate status transitions in service layer
- [ ] Return clear error messages for invalid statuses
- [ ] Ensure all status values are uppercase

### 4. Update API Response Examples
- [ ] Show examples for each of the 8 statuses
- [ ] Include cancellation reason in responses
- [ ] Document status transition rules

---

## Files to Update

1. **`docs/API_REFERENCE.md`** - Booking endpoints section
2. **`backend/modules/bookings/presentation/api.py`** - Status validation
3. **`backend/schemas.py`** - BookingStatus enum validation
4. **`frontend/lib/api.ts`** - Booking types
5. **`frontend/types/index.ts`** - BookingStatus enum
6. **`frontend/types/booking.ts`** - Remove legacy statuses
7. **`frontend/app/bookings/BookingsPageContent.tsx`** - Update status filters
8. **`frontend/components/dashboards/*.tsx`** - Update status display logic

---

## Acceptance Criteria

- [ ] All 8 statuses documented in API reference
- [ ] `"upcoming"` removed from status documentation (kept as filter only)
- [ ] Frontend correctly displays separate cancellation statuses
- [ ] Backend validates status against database constraint
- [ ] API response examples show all statuses
- [ ] Frontend no longer supports legacy lowercase statuses
- [ ] Status transitions validated in service layer

---

**Last Updated:** January 24, 2026  
**Status:** 🔴 Not Started
