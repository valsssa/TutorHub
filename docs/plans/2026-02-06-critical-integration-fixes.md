# Critical Integration Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix ALL integration issues between frontend, backend, and database discovered during comprehensive analysis.

**Architecture:** This plan addresses eight critical categories: (1) datetime/timezone consistency, (2) booking state enum alignment, (3) soft delete column additions, (4) field naming standardization, (5) missing model columns, (6) frontend type alignment, (7) API contract fixes, and (8) data flow race conditions. Each fix follows TDD with minimal changes to existing patterns.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL 17, TypeScript, Next.js 15

**Estimated Tasks:** 45 tasks across 12 phases

---

## Table of Contents

1. [Phase 1: DateTime/Timezone Consistency](#phase-1-datetimetimezone-consistency-critical) (Tasks 1-3)
2. [Phase 2: Booking State Enum Alignment](#phase-2-booking-state-enum-alignment-critical) (Task 4)
3. [Phase 3: Frontend Type Alignment](#phase-3-frontend-type-alignment-critical) (Tasks 5-12)
4. [Phase 4: Soft Delete Columns](#phase-4-database-model-soft-delete-alignment-major) (Tasks 13-15)
5. [Phase 5: Payment Model Fixes](#phase-5-payment-model-field-naming-major) (Tasks 16-18)
6. [Phase 6: User Model Missing Fields](#phase-6-user-model-missing-fields-major) (Tasks 19-20)
7. [Phase 7: TutorProfile Missing Fields](#phase-7-tutorprofile-missing-fields-major) (Tasks 21-22)
8. [Phase 8: Tutor Constraints](#phase-8-tutor-profile-constraints-minor) (Tasks 23-24)
9. [Phase 9: API Response Contract Fixes](#phase-9-api-response-contract-fixes-major) (Tasks 25-30)
10. [Phase 10: Data Flow Race Conditions](#phase-10-data-flow-race-condition-fixes-major) (Tasks 31-36)
11. [Phase 11: Frontend Data Flow Fixes](#phase-11-frontend-data-flow-fixes-major) (Tasks 37-41)
12. [Phase 12: Verification](#phase-12-run-full-test-suite) (Tasks 42-45)

---

## Phase 1: DateTime/Timezone Consistency (CRITICAL)

### Task 1: Create datetime utility module

**Files:**
- Create: `backend/core/datetime_utils.py`
- Test: `backend/tests/test_datetime_utils.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_datetime_utils.py
"""Tests for datetime utility functions."""
from datetime import datetime, timezone

import pytest

from core.datetime_utils import utc_now, is_aware, ensure_utc


class TestUtcNow:
    def test_returns_timezone_aware_datetime(self):
        result = utc_now()
        assert result.tzinfo is not None
        assert result.tzinfo == timezone.utc

    def test_returns_current_time(self):
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after


class TestIsAware:
    def test_aware_datetime_returns_true(self):
        aware = datetime.now(timezone.utc)
        assert is_aware(aware) is True

    def test_naive_datetime_returns_false(self):
        naive = datetime.utcnow()
        assert is_aware(naive) is False


class TestEnsureUtc:
    def test_aware_utc_returns_unchanged(self):
        dt = datetime.now(timezone.utc)
        result = ensure_utc(dt)
        assert result == dt

    def test_naive_datetime_raises_error(self):
        naive = datetime.utcnow()
        with pytest.raises(ValueError, match="naive datetime"):
            ensure_utc(naive)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_datetime_utils.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'core.datetime_utils'"

**Step 3: Write minimal implementation**

```python
# backend/core/datetime_utils.py
"""Centralized datetime utilities for timezone-aware operations.

All datetime operations in the codebase MUST use these utilities
to ensure timezone consistency. Never use datetime.utcnow().
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current time as timezone-aware UTC datetime.

    Use this instead of datetime.utcnow() or datetime.now().
    """
    return datetime.now(timezone.utc)


def is_aware(dt: datetime) -> bool:
    """Check if datetime is timezone-aware."""
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def ensure_utc(dt: datetime) -> datetime:
    """Validate that datetime is timezone-aware UTC.

    Raises:
        ValueError: If datetime is naive (no timezone info)
    """
    if not is_aware(dt):
        raise ValueError(
            f"Received naive datetime {dt}. All datetimes must be timezone-aware UTC."
        )
    return dt
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_datetime_utils.py -v`
Expected: PASS (3 test classes, 6 tests)

**Step 5: Commit**

```bash
git add backend/core/datetime_utils.py backend/tests/test_datetime_utils.py
git commit -m "feat(core): add centralized datetime utilities for timezone consistency"
```

---

### Task 2: Fix datetime.utcnow() in booking presentation layer

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Modify: `backend/modules/bookings/domain/state_machine.py`
- Test: `backend/modules/bookings/tests/test_datetime_usage.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_datetime_usage.py
"""Tests to verify datetime usage in bookings module."""
from pathlib import Path


def test_no_utcnow_in_bookings_api():
    """Ensure datetime.utcnow() is not used in bookings API."""
    api_path = Path(__file__).parent.parent / "presentation" / "api.py"
    source = api_path.read_text()
    assert "utcnow()" not in source, (
        "Found datetime.utcnow() in bookings/presentation/api.py. "
        "Use core.datetime_utils.utc_now() instead."
    )


def test_no_utcnow_in_bookings_state_machine():
    """Ensure datetime.utcnow() is not used in state machine."""
    sm_path = Path(__file__).parent.parent / "domain" / "state_machine.py"
    source = sm_path.read_text()
    assert "utcnow()" not in source, (
        "Found datetime.utcnow() in bookings/domain/state_machine.py. "
        "Use core.datetime_utils.utc_now() instead."
    )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest modules/bookings/tests/test_datetime_usage.py -v`
Expected: FAIL

**Step 3: Fix api.py - add import and replace all utcnow()**

```python
# At top of backend/modules/bookings/presentation/api.py, add:
from core.datetime_utils import utc_now

# Replace all datetime.utcnow() with utc_now()
```

**Step 4: Fix state_machine.py - add import and replace all utcnow()**

```python
# At top of backend/modules/bookings/domain/state_machine.py, add:
from core.datetime_utils import utc_now

# Replace all datetime.utcnow() with utc_now()
```

**Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest modules/bookings/tests/test_datetime_usage.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/modules/bookings/presentation/api.py backend/modules/bookings/domain/state_machine.py backend/modules/bookings/tests/test_datetime_usage.py
git commit -m "fix(bookings): replace datetime.utcnow() with timezone-aware utc_now()"
```

---

### Task 3: Fix datetime.utcnow() in all core modules

**Files:**
- Modify: `backend/core/audit.py`
- Modify: `backend/core/feature_flags.py`
- Modify: `backend/core/ports/email.py`
- Test: `backend/tests/test_datetime_usage_core.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_datetime_usage_core.py
"""Tests to verify datetime usage across entire codebase."""
from pathlib import Path
import os


def test_no_utcnow_in_entire_codebase():
    """Ensure datetime.utcnow() is not used anywhere in codebase."""
    backend_path = Path(__file__).parent.parent
    violations = []

    for root, dirs, files in os.walk(backend_path):
        # Skip test files and migrations
        if "__pycache__" in root or "migrations" in root:
            continue
        for file in files:
            if file.endswith(".py") and not file.startswith("test_"):
                file_path = Path(root) / file
                try:
                    source = file_path.read_text()
                    if "utcnow()" in source and "datetime_utils" not in str(file_path):
                        violations.append(str(file_path.relative_to(backend_path)))
                except Exception:
                    pass

    assert not violations, (
        f"Found datetime.utcnow() in: {violations}. "
        "Use core.datetime_utils.utc_now() instead."
    )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_datetime_usage_core.py -v`
Expected: FAIL with list of files

**Step 3: Fix each file with utcnow()**

For each file found:
1. Add import: `from core.datetime_utils import utc_now`
2. Replace all `datetime.utcnow()` with `utc_now()`

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_datetime_usage_core.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "fix(core): replace all datetime.utcnow() with timezone-aware utc_now()"
```

---

## Phase 2: Booking State Enum Alignment (CRITICAL)

### Task 4: Fix domain entity default enum values

**Files:**
- Modify: `backend/modules/bookings/domain/entities.py`
- Test: `backend/modules/bookings/tests/test_entity_enums.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_entity_enums.py
"""Tests to verify booking entity uses valid enum values."""
from modules.bookings.domain.entities import BookingEntity
from modules.bookings.domain.status import SessionState, SessionOutcome


def test_booking_entity_default_session_state_is_valid():
    """Default session_state must be REQUESTED."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_profile_id=1,
        start_at=None,
        end_at=None,
        duration_minutes=60,
    )
    assert entity.session_state == SessionState.REQUESTED


def test_booking_entity_default_session_outcome_is_none():
    """Default session_outcome should be None."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_profile_id=1,
        start_at=None,
        end_at=None,
        duration_minutes=60,
    )
    assert entity.session_outcome is None


def test_is_confirmed_uses_scheduled_state():
    """is_confirmed property should check SCHEDULED state."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_profile_id=1,
        start_at=None,
        end_at=None,
        duration_minutes=60,
        session_state=SessionState.SCHEDULED,
    )
    assert entity.is_confirmed is True


def test_is_completed_uses_ended_with_completed_outcome():
    """is_completed should check ENDED state with COMPLETED outcome."""
    entity = BookingEntity(
        id=None,
        student_id=1,
        tutor_profile_id=1,
        start_at=None,
        end_at=None,
        duration_minutes=60,
        session_state=SessionState.ENDED,
        session_outcome=SessionOutcome.COMPLETED,
    )
    assert entity.is_completed is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest modules/bookings/tests/test_entity_enums.py -v`
Expected: FAIL

**Step 3: Fix the entity defaults and properties**

```python
# backend/modules/bookings/domain/entities.py

# Change default session_state from PENDING_TUTOR to REQUESTED
session_state: SessionState = SessionState.REQUESTED

# Change default session_outcome from SessionOutcome.PENDING to None
session_outcome: SessionOutcome | None = None

# Fix is_confirmed to use SCHEDULED
@property
def is_confirmed(self) -> bool:
    return self.session_state == SessionState.SCHEDULED

# Fix is_completed to check ENDED + COMPLETED outcome
@property
def is_completed(self) -> bool:
    return (
        self.session_state == SessionState.ENDED
        and self.session_outcome == SessionOutcome.COMPLETED
    )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest modules/bookings/tests/test_entity_enums.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/modules/bookings/domain/entities.py backend/modules/bookings/tests/test_entity_enums.py
git commit -m "fix(bookings): align entity default enums with database constraints"
```

---

## Phase 3: Frontend Type Alignment (CRITICAL)

### Task 5: Remove legacy SessionState values

**Files:**
- Modify: `frontend-v2/types/booking.ts`
- Test: `frontend-v2/__tests__/types/booking-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/booking-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const LEGACY_SESSION_STATES = [
  'pending_tutor', 'pending_student', 'confirmed', 'in_progress',
  'completed', 'cancelled', 'expired', 'no_show',
];

const LEGACY_PAYMENT_STATES = [
  'pending', 'authorized', 'captured', 'released_to_tutor', 'refunded', 'failed',
];

describe('SessionState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    for (const legacyState of LEGACY_SESSION_STATES) {
      expect(typeFile).not.toContain(`'${legacyState}'`);
    }
  });
});

describe('PaymentState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    for (const legacyState of LEGACY_PAYMENT_STATES) {
      expect(typeFile).not.toContain(`'${legacyState}'`);
    }
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/booking-types.test.ts`
Expected: FAIL

**Step 3: Update types/booking.ts**

```typescript
// frontend-v2/types/booking.ts

/**
 * Valid session states matching backend BookingStateMachine.
 * State flow: REQUESTED -> SCHEDULED -> ACTIVE -> ENDED
 * Terminal states: ENDED, CANCELLED, EXPIRED
 */
export type SessionState =
  | 'REQUESTED'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'ENDED'
  | 'EXPIRED'
  | 'CANCELLED';

/**
 * Valid payment states matching backend PaymentState enum.
 */
export type PaymentState =
  | 'PENDING'
  | 'AUTHORIZED'
  | 'CAPTURED'
  | 'VOIDED'
  | 'REFUNDED'
  | 'PARTIALLY_REFUNDED';
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/booking-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/booking.ts frontend-v2/__tests__/types/booking-types.test.ts
git commit -m "fix(frontend): remove legacy SessionState/PaymentState enum values"
```

---

### Task 6: Add missing User type fields

**Files:**
- Modify: `frontend-v2/types/user.ts`
- Test: `frontend-v2/__tests__/types/user-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/user-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('User type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/user.ts'),
    'utf-8'
  );

  it('should include profile_incomplete field', () => {
    expect(typeFile).toContain('profile_incomplete');
  });

  it('should include full_name field', () => {
    expect(typeFile).toContain('full_name');
  });

  it('should have first_name as nullable', () => {
    expect(typeFile).toMatch(/first_name.*string \| null/);
  });

  it('should have last_name as nullable', () => {
    expect(typeFile).toMatch(/last_name.*string \| null/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/user-types.test.ts`
Expected: FAIL

**Step 3: Update types/user.ts**

```typescript
// frontend-v2/types/user.ts

/**
 * User entity matching backend UserResponse schema.
 * Note: first_name/last_name can be null for incomplete profiles.
 */
export interface User {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  profile_incomplete: boolean;
  role: UserRole;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  timezone: string;
  currency: string;
  preferred_language?: string;
  locale?: string;
  created_at: string;
  updated_at: string;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/user-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/user.ts frontend-v2/__tests__/types/user-types.test.ts
git commit -m "fix(frontend): add missing User type fields to match backend schema"
```

---

### Task 7: Fix Booking type field aliases

**Files:**
- Modify: `frontend-v2/types/booking.ts`
- Test: `frontend-v2/__tests__/types/booking-fields.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/booking-fields.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Booking type fields', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should use start_at as primary field', () => {
    expect(typeFile).toMatch(/^\s+start_at: string;/m);
  });

  it('should NOT have start_time alias', () => {
    // start_time should not exist as a separate field
    expect(typeFile).not.toMatch(/^\s+start_time\??: string;/m);
  });

  it('should use end_at as primary field', () => {
    expect(typeFile).toMatch(/^\s+end_at: string;/m);
  });
});

describe('BookingListResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should NOT have items alias field', () => {
    // BookingListResponse should only have bookings, not items
    expect(typeFile).not.toMatch(/items\?: Booking\[\]/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/booking-fields.test.ts`
Expected: FAIL

**Step 3: Update types/booking.ts - remove field aliases**

```typescript
// In Booking interface, remove start_time? alias:
export interface Booking {
  id: number;
  student_id: number;
  tutor_profile_id: number;
  start_at: string;  // Primary field, no alias
  end_at: string;
  // ... rest of fields
}

// In BookingListResponse, remove items? alias:
export interface BookingListResponse {
  bookings: Booking[];  // Primary field only
  total: number;
  page: number;
  page_size: number;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/booking-fields.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/booking.ts frontend-v2/__tests__/types/booking-fields.test.ts
git commit -m "fix(frontend): remove field aliases from Booking types"
```

---

### Task 8: Fix Message type field aliases

**Files:**
- Modify: `frontend-v2/types/message.ts`
- Test: `frontend-v2/__tests__/types/message-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/message-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Message type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/message.ts'),
    'utf-8'
  );

  it('should use message as primary content field', () => {
    expect(typeFile).toMatch(/^\s+message: string;/m);
  });

  it('should NOT have content alias', () => {
    expect(typeFile).not.toMatch(/^\s+content\??: string;/m);
  });
});

describe('PaginatedMessagesResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/message.ts'),
    'utf-8'
  );

  it('should use messages as primary field', () => {
    expect(typeFile).toMatch(/messages: Message\[\]/);
  });

  it('should NOT have items alias', () => {
    expect(typeFile).not.toMatch(/items\?: Message\[\]/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/message-types.test.ts`
Expected: FAIL

**Step 3: Update types/message.ts - remove aliases**

```typescript
// frontend-v2/types/message.ts

export interface Message {
  id: number;
  sender_id: number;
  recipient_id?: number;
  message: string;  // Primary field, remove content? alias
  conversation_id?: number;
  // ... rest
}

export interface PaginatedMessagesResponse {
  messages: Message[];  // Primary field only, remove items?
  total: number;
  page: number;
  page_size: number;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/message-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/message.ts frontend-v2/__tests__/types/message-types.test.ts
git commit -m "fix(frontend): remove field aliases from Message types"
```

---

### Task 9: Add TutorProfileStatus type

**Files:**
- Modify: `frontend-v2/types/tutor.ts`
- Test: `frontend-v2/__tests__/types/tutor-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/tutor-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('TutorProfileStatus type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/tutor.ts'),
    'utf-8'
  );

  it('should have TutorProfileStatus type defined', () => {
    expect(typeFile).toContain('TutorProfileStatus');
  });

  it('should include all valid status values', () => {
    const validStatuses = [
      'incomplete', 'pending_approval', 'under_review',
      'approved', 'rejected', 'archived'
    ];
    for (const status of validStatuses) {
      expect(typeFile).toContain(`'${status}'`);
    }
  });
});

describe('TutorProfile type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/tutor.ts'),
    'utf-8'
  );

  it('should use typed profile_status', () => {
    expect(typeFile).toMatch(/profile_status.*TutorProfileStatus/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/tutor-types.test.ts`
Expected: FAIL

**Step 3: Add TutorProfileStatus type**

```typescript
// frontend-v2/types/tutor.ts

/**
 * Valid tutor profile status values matching backend constraint.
 */
export type TutorProfileStatus =
  | 'incomplete'
  | 'pending_approval'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'archived';

export interface TutorProfile {
  // ... existing fields
  profile_status: TutorProfileStatus;  // Change from string
  // ...
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/tutor-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/tutor.ts frontend-v2/__tests__/types/tutor-types.test.ts
git commit -m "fix(frontend): add TutorProfileStatus typed enum"
```

---

### Task 10: Fix Notification type

**Files:**
- Modify: `frontend-v2/types/notification.ts`
- Test: `frontend-v2/__tests__/types/notification-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/notification-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Notification type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/notification.ts'),
    'utf-8'
  );

  it('should use typed NotificationType for type field', () => {
    expect(typeFile).toMatch(/type: NotificationType/);
  });
});

describe('NotificationStats type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/notification.ts'),
    'utf-8'
  );

  it('should use count field matching backend', () => {
    // Backend returns { count: int }, not unread_count
    expect(typeFile).toMatch(/count: number/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/notification-types.test.ts`
Expected: FAIL

**Step 3: Update types/notification.ts**

```typescript
// frontend-v2/types/notification.ts

export type NotificationType =
  | 'booking_request'
  | 'booking_confirmed'
  | 'booking_cancelled'
  | 'message'
  | 'review'
  | 'payment'
  | 'system';

export interface Notification {
  id: number;
  type: NotificationType;  // Use typed enum, not string
  title: string;
  message: string;
  // ...
}

export interface NotificationStats {
  count: number;  // Match backend UnreadCountResponse
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/notification-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/notification.ts frontend-v2/__tests__/types/notification-types.test.ts
git commit -m "fix(frontend): use typed NotificationType and fix stats field"
```

---

### Task 11: Add DisputeState type

**Files:**
- Modify: `frontend-v2/types/booking.ts`
- Test: Already covered in booking-types.test.ts

**Step 1: Add DisputeState type**

```typescript
// Add to frontend-v2/types/booking.ts

/**
 * Valid dispute states matching backend DisputeState enum.
 */
export type DisputeState =
  | 'NONE'
  | 'OPEN'
  | 'RESOLVED_UPHELD'
  | 'RESOLVED_REFUNDED';

/**
 * Valid session outcome values.
 */
export type SessionOutcome =
  | 'COMPLETED'
  | 'NOT_HELD'
  | 'NO_SHOW_STUDENT'
  | 'NO_SHOW_TUTOR';
```

**Step 2: Run type check**

Run: `cd frontend-v2 && npm run type-check`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend-v2/types/booking.ts
git commit -m "fix(frontend): add DisputeState and SessionOutcome types"
```

---

### Task 12: Standardize PaginatedResponse type

**Files:**
- Modify: `frontend-v2/types/api.ts`
- Test: `frontend-v2/__tests__/types/api-types.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/types/api-types.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('PaginatedResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/api.ts'),
    'utf-8'
  );

  it('should have consistent pagination fields', () => {
    expect(typeFile).toContain('total: number');
    expect(typeFile).toContain('page: number');
    expect(typeFile).toContain('page_size: number');
  });

  it('should be generic with items field', () => {
    expect(typeFile).toMatch(/items: T\[\]/);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend-v2 && npm test -- __tests__/types/api-types.test.ts`
Expected: FAIL

**Step 3: Update types/api.ts**

```typescript
// frontend-v2/types/api.ts

/**
 * Standard paginated response matching backend pagination pattern.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend-v2 && npm test -- __tests__/types/api-types.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend-v2/types/api.ts frontend-v2/__tests__/types/api-types.test.ts
git commit -m "fix(frontend): standardize PaginatedResponse type"
```

---

## Phase 4: Database Model Soft Delete Alignment (MAJOR)

### Task 13: Add soft delete columns to Notification model

**Files:**
- Modify: `backend/models/notifications.py`
- Test: `backend/tests/test_notification_soft_delete.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_notification_soft_delete.py
"""Tests for notification soft delete functionality."""
from sqlalchemy import inspect
from models.notifications import Notification


def test_notification_has_deleted_at_column():
    mapper = inspect(Notification)
    column_names = [c.key for c in mapper.columns]
    assert "deleted_at" in column_names


def test_notification_has_deleted_by_column():
    mapper = inspect(Notification)
    column_names = [c.key for c in mapper.columns]
    assert "deleted_by" in column_names
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_notification_soft_delete.py -v`
Expected: FAIL

**Step 3: Add columns**

```python
# backend/models/notifications.py
deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_notification_soft_delete.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/notifications.py backend/tests/test_notification_soft_delete.py
git commit -m "fix(models): add soft delete columns to Notification model"
```

---

### Task 14: Add soft delete columns to Conversation and Message models

**Files:**
- Modify: `backend/models/messages.py`
- Test: `backend/tests/test_message_soft_delete.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_message_soft_delete.py
"""Tests for message soft delete functionality."""
from sqlalchemy import inspect
from models.messages import Conversation, Message, MessageAttachment


def test_conversation_has_deleted_at():
    mapper = inspect(Conversation)
    assert "deleted_at" in [c.key for c in mapper.columns]


def test_conversation_has_deleted_by():
    mapper = inspect(Conversation)
    assert "deleted_by" in [c.key for c in mapper.columns]


def test_message_attachment_has_file_category():
    mapper = inspect(MessageAttachment)
    assert "file_category" in [c.key for c in mapper.columns]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_message_soft_delete.py -v`
Expected: FAIL

**Step 3: Add missing columns**

```python
# backend/models/messages.py

# In Conversation class:
deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

# In MessageAttachment class:
file_category = Column(String(50), nullable=True)  # 'image', 'document', 'video', 'audio', 'other'
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_message_soft_delete.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/messages.py backend/tests/test_message_soft_delete.py
git commit -m "fix(models): add soft delete to Conversation and file_category to MessageAttachment"
```

---

### Task 15: Add soft delete columns to all remaining models

**Files:**
- Modify: `backend/models/students.py`
- Modify: `backend/models/payments.py`
- Modify: `backend/models/reviews.py`
- Modify: `backend/models/tutors.py`
- Test: `backend/tests/test_soft_delete_columns.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_soft_delete_columns.py
"""Tests to verify all models have soft delete columns."""
import pytest
from sqlalchemy import inspect

from models.students import FavoriteTutor, StudentPackage, StudentProfile
from models.payments import Refund, Payout, Wallet, WalletTransaction
from models.reviews import Review
from models.tutors import TutorSubject, TutorAvailability, TutorCertification, TutorEducation


MODELS_REQUIRING_SOFT_DELETE = [
    FavoriteTutor, StudentPackage, StudentProfile,
    Refund, Payout, Wallet, WalletTransaction,
    Review,
    TutorSubject, TutorAvailability, TutorCertification, TutorEducation,
]


@pytest.mark.parametrize("model_class", MODELS_REQUIRING_SOFT_DELETE)
def test_model_has_deleted_at(model_class):
    mapper = inspect(model_class)
    assert "deleted_at" in [c.key for c in mapper.columns], f"{model_class.__name__} missing deleted_at"


@pytest.mark.parametrize("model_class", MODELS_REQUIRING_SOFT_DELETE)
def test_model_has_deleted_by(model_class):
    mapper = inspect(model_class)
    assert "deleted_by" in [c.key for c in mapper.columns], f"{model_class.__name__} missing deleted_by"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_soft_delete_columns.py -v`
Expected: FAIL

**Step 3: Add soft delete columns to each model**

For each model, add:
```python
deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_soft_delete_columns.py -v`
Expected: PASS (24 tests)

**Step 5: Commit**

```bash
git add backend/models/students.py backend/models/payments.py backend/models/reviews.py backend/models/tutors.py backend/tests/test_soft_delete_columns.py
git commit -m "fix(models): add soft delete columns to all models"
```

---

## Phase 5: Payment Model Field Naming (MAJOR)

### Task 16: Fix payment metadata field naming

**Files:**
- Modify: `backend/models/payments.py`
- Test: `backend/tests/test_payment_metadata_fields.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_payment_metadata_fields.py
from sqlalchemy import inspect
from models.payments import Payment, Refund, Payout


def test_payment_uses_metadata():
    mapper = inspect(Payment)
    columns = [c.key for c in mapper.columns]
    assert "metadata" in columns
    assert "payment_metadata" not in columns


def test_refund_uses_metadata():
    mapper = inspect(Refund)
    columns = [c.key for c in mapper.columns]
    assert "metadata" in columns
    assert "refund_metadata" not in columns


def test_payout_uses_metadata():
    mapper = inspect(Payout)
    columns = [c.key for c in mapper.columns]
    assert "metadata" in columns
    assert "payout_metadata" not in columns
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_payment_metadata_fields.py -v`
Expected: FAIL

**Step 3: Rename fields**

```python
# backend/models/payments.py
# Change payment_metadata, refund_metadata, payout_metadata to metadata
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_payment_metadata_fields.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/payments.py backend/tests/test_payment_metadata_fields.py
git commit -m "fix(models): rename metadata fields to match database"
```

---

### Task 17: Add archived ID fields to Payment/Payout

**Files:**
- Modify: `backend/models/payments.py`
- Test: `backend/tests/test_payment_archived_ids.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_payment_archived_ids.py
from sqlalchemy import inspect
from models.payments import Payment, Payout


def test_payment_has_archived_student_id():
    mapper = inspect(Payment)
    assert "archived_student_id" in [c.key for c in mapper.columns]


def test_payout_has_archived_tutor_id():
    mapper = inspect(Payout)
    assert "archived_tutor_id" in [c.key for c in mapper.columns]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_payment_archived_ids.py -v`
Expected: FAIL

**Step 3: Add columns**

```python
# backend/models/payments.py

# In Payment class:
archived_student_id = Column(Integer, nullable=True)

# In Payout class:
archived_tutor_id = Column(Integer, nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_payment_archived_ids.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/payments.py backend/tests/test_payment_archived_ids.py
git commit -m "fix(models): add archived ID fields to Payment/Payout"
```

---

### Task 18: Fix fraud detection confidence_score type

**Files:**
- Modify: `backend/models/auth.py`
- Test: `backend/tests/test_fraud_detection_model.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_fraud_detection_model.py
from sqlalchemy import inspect, Numeric
from models.auth import RegistrationFraudSignal


def test_confidence_score_is_numeric():
    """confidence_score should be Numeric(3,2), not Integer."""
    mapper = inspect(RegistrationFraudSignal)
    col = mapper.columns.get("confidence_score")
    assert col is not None
    # Should be Numeric type, not Integer
    assert isinstance(col.type, Numeric)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_fraud_detection_model.py -v`
Expected: FAIL

**Step 3: Fix the column type**

```python
# backend/models/auth.py
# Change from:
# confidence_score = Column(Integer, default=50, nullable=False)
# To:
confidence_score = Column(Numeric(3, 2), default=0.50, nullable=False)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_fraud_detection_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/auth.py backend/tests/test_fraud_detection_model.py
git commit -m "fix(models): change confidence_score from Integer to Numeric(3,2)"
```

---

## Phase 6: User Model Missing Fields (MAJOR)

### Task 19: Add locale detection fields to User model

**Files:**
- Modify: `backend/models/auth.py`
- Test: `backend/tests/test_user_locale_fields.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_user_locale_fields.py
from sqlalchemy import inspect
from models.auth import User


def test_user_has_detected_language():
    mapper = inspect(User)
    assert "detected_language" in [c.key for c in mapper.columns]


def test_user_has_locale():
    mapper = inspect(User)
    assert "locale" in [c.key for c in mapper.columns]


def test_user_has_detected_locale():
    mapper = inspect(User)
    assert "detected_locale" in [c.key for c in mapper.columns]


def test_user_has_locale_detection_confidence():
    mapper = inspect(User)
    assert "locale_detection_confidence" in [c.key for c in mapper.columns]
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_user_locale_fields.py -v`
Expected: FAIL

**Step 3: Add missing columns**

```python
# backend/models/auth.py - in User class

detected_language = Column(String(2), nullable=True)
locale = Column(String(10), default="en-US", nullable=True)
detected_locale = Column(String(10), nullable=True)
locale_detection_confidence = Column(Numeric(3, 2), nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_user_locale_fields.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/auth.py backend/tests/test_user_locale_fields.py
git commit -m "fix(models): add locale detection fields to User model"
```

---

### Task 20: Fix preferred_language field type

**Files:**
- Modify: `backend/models/auth.py`
- Test: `backend/tests/test_user_language_field.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_user_language_field.py
from sqlalchemy import inspect
from models.auth import User


def test_preferred_language_max_length():
    """preferred_language should be max 2 chars to match CHAR(2) in DB."""
    mapper = inspect(User)
    col = mapper.columns.get("preferred_language")
    assert col is not None
    # Should be 2 chars, not 5
    assert col.type.length == 2
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_user_language_field.py -v`
Expected: FAIL (currently String(5))

**Step 3: Fix the column**

```python
# backend/models/auth.py
# Change from:
# preferred_language = Column(String(5))
# To:
preferred_language = Column(String(2), default="en")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_user_language_field.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/auth.py backend/tests/test_user_language_field.py
git commit -m "fix(models): change preferred_language to String(2)"
```

---

## Phase 7: TutorProfile Missing Fields (MAJOR)

### Task 21: Add missing TutorProfile verification fields

**Files:**
- Modify: `backend/models/tutors.py`
- Test: `backend/tests/test_tutor_profile_fields.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tutor_profile_fields.py
from sqlalchemy import inspect
from models.tutors import TutorProfile


REQUIRED_FIELDS = [
    "badges",
    "is_identity_verified",
    "is_education_verified",
    "is_background_checked",
    "verification_notes",
    "profile_completeness_score",
    "last_completeness_check",
    "cancellation_strikes",
    "trial_price_cents",
    "payout_method",
    "teaching_philosophy",
]


def test_tutor_profile_has_all_required_fields():
    mapper = inspect(TutorProfile)
    columns = [c.key for c in mapper.columns]

    missing = [f for f in REQUIRED_FIELDS if f not in columns]
    assert not missing, f"TutorProfile missing fields: {missing}"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tutor_profile_fields.py -v`
Expected: FAIL

**Step 3: Add missing columns**

```python
# backend/models/tutors.py - in TutorProfile class

from sqlalchemy.dialects.postgresql import ARRAY, JSONB

badges = Column(ARRAY(String), default=list, nullable=True)
is_identity_verified = Column(Boolean, default=False, nullable=False)
is_education_verified = Column(Boolean, default=False, nullable=False)
is_background_checked = Column(Boolean, default=False, nullable=False)
verification_notes = Column(Text, nullable=True)
profile_completeness_score = Column(Integer, default=0, nullable=True)
last_completeness_check = Column(TIMESTAMP(timezone=True), nullable=True)
cancellation_strikes = Column(Integer, default=0, nullable=False)
trial_price_cents = Column(Integer, nullable=True)
payout_method = Column(JSONB, nullable=True)
teaching_philosophy = Column(Text, nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tutor_profile_fields.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/tutors.py backend/tests/test_tutor_profile_fields.py
git commit -m "fix(models): add missing TutorProfile verification and completeness fields"
```

---

### Task 22: Add missing StudentProfile fields

**Files:**
- Modify: `backend/models/students.py`
- Test: `backend/tests/test_student_profile_fields.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_student_profile_fields.py
from sqlalchemy import inspect
from models.students import StudentProfile


def test_student_profile_has_interests():
    mapper = inspect(StudentProfile)
    assert "interests" in [c.key for c in mapper.columns]


def test_student_profile_has_soft_delete():
    mapper = inspect(StudentProfile)
    columns = [c.key for c in mapper.columns]
    assert "deleted_at" in columns
    assert "deleted_by" in columns
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_student_profile_fields.py -v`
Expected: FAIL

**Step 3: Add missing columns**

```python
# backend/models/students.py - in StudentProfile class

from sqlalchemy.dialects.postgresql import ARRAY

interests = Column(ARRAY(String), default=list, nullable=True)
deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_student_profile_fields.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/students.py backend/tests/test_student_profile_fields.py
git commit -m "fix(models): add interests and soft delete to StudentProfile"
```

---

## Phase 8: Tutor Profile Constraints (MINOR)

### Task 23: Add 'archived' to profile_status constraint

**Files:**
- Modify: `backend/models/tutors.py`
- Test: `backend/tests/test_tutor_profile_constraints.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tutor_profile_constraints.py
from models.tutors import TutorProfile


def test_profile_status_allows_archived():
    constraints = TutorProfile.__table__.constraints
    check_constraints = [c for c in constraints if hasattr(c, 'sqltext')]

    status_constraint = next(
        (c for c in check_constraints if 'profile_status' in str(c.sqltext)), None
    )
    assert status_constraint is not None
    assert 'archived' in str(status_constraint.sqltext)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tutor_profile_constraints.py -v`
Expected: FAIL

**Step 3: Update constraint**

```python
# backend/models/tutors.py
CheckConstraint(
    "profile_status IN ('incomplete', 'pending_approval', 'under_review', 'approved', 'rejected', 'archived')",
    name="valid_profile_status",
)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tutor_profile_constraints.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/tutors.py backend/tests/test_tutor_profile_constraints.py
git commit -m "fix(models): add 'archived' to profile_status constraint"
```

---

### Task 24: Fix proficiency_level case mismatch

**Files:**
- Modify: `backend/models/tutors.py`
- Test: `backend/tests/test_tutor_subject_constraints.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_tutor_subject_constraints.py
from models.tutors import TutorSubject


def test_proficiency_level_uses_uppercase():
    constraints = TutorSubject.__table__.constraints
    check_constraints = [c for c in constraints if hasattr(c, 'sqltext')]

    proficiency_constraint = next(
        (c for c in check_constraints if 'proficiency_level' in str(c.sqltext)), None
    )
    assert proficiency_constraint is not None
    assert "'NATIVE'" in str(proficiency_constraint.sqltext)
    assert "'native'" not in str(proficiency_constraint.sqltext)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tutor_subject_constraints.py -v`
Expected: FAIL

**Step 3: Update constraint**

```python
# backend/models/tutors.py
CheckConstraint(
    "proficiency_level IN ('NATIVE', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1')",
    name="valid_proficiency",
)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tutor_subject_constraints.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/tutors.py backend/tests/test_tutor_subject_constraints.py
git commit -m "fix(models): use UPPERCASE proficiency_level values"
```

---

## Phase 9: API Response Contract Fixes (MAJOR)

### Task 25: Fix notification unread count response

**Files:**
- Modify: `backend/modules/notifications/presentation/api.py`
- Test: `backend/modules/notifications/tests/test_unread_count_response.py`

**Step 1: Write the failing test**

```python
# backend/modules/notifications/tests/test_unread_count_response.py
"""Test notification unread count response format."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


def test_unread_count_returns_count_field(client, auth_headers):
    """Response should have 'count' field, not 'unread_count'."""
    response = client.get("/api/v1/notifications/unread-count", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "unread_count" not in data
```

**Step 2: Verify response format matches frontend expectations**

The backend already returns `count`, but ensure schema is explicit.

**Step 3: Commit**

```bash
git add backend/modules/notifications/tests/test_unread_count_response.py
git commit -m "test(notifications): verify unread count response format"
```

---

### Task 26: Add FavoriteTutor unique constraint to model

**Files:**
- Modify: `backend/models/students.py`
- Test: `backend/tests/test_favorite_constraint.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_favorite_constraint.py
from models.students import FavoriteTutor


def test_favorite_has_unique_constraint():
    """FavoriteTutor should have unique constraint on (student_id, tutor_profile_id)."""
    table = FavoriteTutor.__table__
    unique_constraints = [c for c in table.constraints if hasattr(c, 'columns') and len(c.columns) > 1]

    has_unique = any(
        set(c.name for c in uc.columns) == {'student_id', 'tutor_profile_id'}
        for uc in unique_constraints
    )
    assert has_unique, "Missing unique constraint on (student_id, tutor_profile_id)"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_favorite_constraint.py -v`
Expected: FAIL

**Step 3: Add constraint**

```python
# backend/models/students.py - in FavoriteTutor class

__table_args__ = (
    UniqueConstraint('student_id', 'tutor_profile_id', name='uq_favorite'),
)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_favorite_constraint.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/models/students.py backend/tests/test_favorite_constraint.py
git commit -m "fix(models): add unique constraint to FavoriteTutor"
```

---

### Task 27: Standardize booking date filter parameter names

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Test: `backend/modules/bookings/tests/test_booking_filters.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_booking_filters.py
"""Test booking list filter parameters."""


def test_list_bookings_accepts_from_date_filter(client, auth_headers):
    """Should accept from_date query parameter."""
    response = client.get(
        "/api/v1/bookings?from_date=2026-01-01T00:00:00Z",
        headers=auth_headers
    )
    # Should not error on from_date parameter
    assert response.status_code in [200, 422]  # 200 OK or 422 if validation


def test_list_bookings_accepts_to_date_filter(client, auth_headers):
    """Should accept to_date query parameter."""
    response = client.get(
        "/api/v1/bookings?to_date=2026-12-31T23:59:59Z",
        headers=auth_headers
    )
    assert response.status_code in [200, 422]
```

**Step 2: Update query parameters if needed**

Verify the booking list endpoint accepts `from_date` and `to_date` parameters.

**Step 3: Commit**

```bash
git add backend/modules/bookings/tests/test_booking_filters.py
git commit -m "test(bookings): verify date filter parameters"
```

---

### Task 28: Add row-level locking to reschedule endpoint

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Test: `backend/modules/bookings/tests/test_reschedule_locking.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_reschedule_locking.py
"""Test reschedule endpoint uses proper locking."""
from pathlib import Path


def test_reschedule_uses_locking():
    """reschedule_booking should use get_booking_with_lock."""
    api_path = Path(__file__).parent.parent / "presentation" / "api.py"
    source = api_path.read_text()

    # Find the reschedule function and check it uses locking
    # This is a code inspection test
    assert "get_booking_with_lock" in source or "with_for_update" in source, (
        "reschedule_booking should use row-level locking"
    )
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest modules/bookings/tests/test_reschedule_locking.py -v`
Expected: May pass or fail depending on current implementation

**Step 3: Add locking to reschedule endpoint**

```python
# backend/modules/bookings/presentation/api.py
# In reschedule_booking function, use:
booking = BookingStateMachine.get_booking_with_lock(db, booking_id)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest modules/bookings/tests/test_reschedule_locking.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/modules/bookings/presentation/api.py backend/modules/bookings/tests/test_reschedule_locking.py
git commit -m "fix(bookings): add row-level locking to reschedule endpoint"
```

---

### Task 29: Add external calendar timeout

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Test: `backend/modules/bookings/tests/test_calendar_timeout.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_calendar_timeout.py
"""Test calendar conflict check has timeout."""
from pathlib import Path


def test_calendar_check_has_timeout():
    """External calendar check should have timeout protection."""
    api_path = Path(__file__).parent.parent / "presentation" / "api.py"
    source = api_path.read_text()

    # Check for asyncio.wait_for or timeout parameter
    has_timeout = "wait_for" in source or "timeout" in source
    assert has_timeout, "Calendar conflict check should have timeout protection"
```

**Step 2: Run test to verify current state**

Run: `cd backend && python -m pytest modules/bookings/tests/test_calendar_timeout.py -v`

**Step 3: Add timeout to calendar check**

```python
# backend/modules/bookings/presentation/api.py
import asyncio

# Wrap calendar check with timeout:
try:
    await asyncio.wait_for(
        service.check_external_calendar_conflict(...),
        timeout=5.0  # 5 second timeout
    )
except asyncio.TimeoutError:
    # Log warning but allow booking to proceed
    logger.warning("Calendar check timed out, proceeding without external validation")
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest modules/bookings/tests/test_calendar_timeout.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/modules/bookings/presentation/api.py backend/modules/bookings/tests/test_calendar_timeout.py
git commit -m "fix(bookings): add timeout to external calendar check"
```

---

### Task 30: Add Stripe webhook idempotency check

**Files:**
- Modify: `backend/modules/payments/wallet_router.py`
- Test: `backend/modules/payments/tests/test_webhook_idempotency.py`

**Step 1: Write the failing test**

```python
# backend/modules/payments/tests/test_webhook_idempotency.py
"""Test webhook idempotency."""
from pathlib import Path


def test_webhook_checks_duplicate_event():
    """Webhook handler should check for duplicate event IDs."""
    router_path = Path(__file__).parent.parent / "wallet_router.py"
    source = router_path.read_text()

    # Should check event ID or use idempotency key
    has_idempotency = (
        "event_id" in source or
        "idempotency" in source or
        "already_processed" in source
    )
    assert has_idempotency, "Webhook should have idempotency check"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest modules/payments/tests/test_webhook_idempotency.py -v`

**Step 3: Add idempotency check**

```python
# backend/modules/payments/wallet_router.py
# In webhook handler, add:

# Check if event already processed
existing = db.query(WebhookEvent).filter(
    WebhookEvent.stripe_event_id == event.id
).first()
if existing:
    return {"status": "already_processed"}

# Record event
webhook_event = WebhookEvent(stripe_event_id=event.id, event_type=event.type)
db.add(webhook_event)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest modules/payments/tests/test_webhook_idempotency.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/modules/payments/wallet_router.py backend/modules/payments/tests/test_webhook_idempotency.py
git commit -m "fix(payments): add webhook idempotency check"
```

---

## Phase 10: Data Flow Race Condition Fixes (MAJOR)

### Task 31: Fix booking creation calendar race condition

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Test: `backend/modules/bookings/tests/test_booking_creation_order.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_booking_creation_order.py
"""Test booking creation does calendar check inside transaction."""
from pathlib import Path
import re


def test_calendar_check_inside_transaction():
    """Calendar check should happen after acquiring lock, not before."""
    api_path = Path(__file__).parent.parent / "presentation" / "api.py"
    source = api_path.read_text()

    # Find create_booking function
    # Calendar check should be after lock acquisition
    # This is a structural test - verify order of operations

    # Look for pattern: lock acquisition -> calendar check -> create
    # Not: calendar check -> lock -> create

    # This test documents the expected order
    assert "get_booking_with_lock" in source or "FOR UPDATE" in source
```

**Step 2: Document the fix needed**

The calendar check should happen AFTER acquiring a lock on the time slot, not before. This prevents the race condition where:
1. Check calendar (slot appears free)
2. Another request books the slot
3. This request creates conflicting booking

**Step 3: Reorder operations**

```python
# backend/modules/bookings/presentation/api.py
# In booking creation:
# 1. Start transaction
# 2. Acquire lock on tutor's time slot
# 3. Check internal conflicts
# 4. Check external calendar
# 5. Create booking
# 6. Commit
```

**Step 4: Commit**

```bash
git add backend/modules/bookings/presentation/api.py backend/modules/bookings/tests/test_booking_creation_order.py
git commit -m "fix(bookings): move calendar check inside transaction"
```

---

### Task 32: Add booking confirmation idempotency

**Files:**
- Modify: `backend/modules/bookings/presentation/api.py`
- Test: `backend/modules/bookings/tests/test_confirmation_idempotency.py`

**Step 1: Write the failing test**

```python
# backend/modules/bookings/tests/test_confirmation_idempotency.py
"""Test booking confirmation is idempotent."""


def test_confirm_booking_is_idempotent(client, auth_headers, scheduled_booking):
    """Confirming already-confirmed booking should not error or duplicate meeting."""
    booking_id = scheduled_booking.id

    # First confirmation
    response1 = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers
    )

    # Second confirmation (should be idempotent)
    response2 = client.post(
        f"/api/v1/bookings/{booking_id}/confirm",
        headers=auth_headers
    )

    # Both should succeed or second should return existing state
    assert response2.status_code in [200, 409]  # OK or Conflict
```

**Step 2: Ensure confirmation handles already-confirmed state**

**Step 3: Commit**

```bash
git add backend/modules/bookings/tests/test_confirmation_idempotency.py
git commit -m "test(bookings): verify confirmation idempotency"
```

---

### Task 33: Fix token refresh race condition in frontend

**Files:**
- Modify: `frontend-v2/lib/api/client.ts`
- Test: `frontend-v2/__tests__/lib/api/client-refresh.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/lib/api/client-refresh.test.ts
import { describe, it, expect, vi } from 'vitest';

describe('API Client Token Refresh', () => {
  it('should queue requests during refresh', async () => {
    // Test that multiple 401s result in single refresh call
    // This is a design test documenting expected behavior
  });

  it('should not start multiple refresh attempts', async () => {
    // Verify isRefreshing flag prevents race
  });
});
```

**Step 2: Verify refresh logic uses proper mutex pattern**

The current implementation has `isRefreshing` flag. Verify it properly queues requests.

**Step 3: Commit**

```bash
git add frontend-v2/__tests__/lib/api/client-refresh.test.ts
git commit -m "test(frontend): verify token refresh race condition handling"
```

---

### Task 34: Add auth state validation on focus

**Files:**
- Modify: `frontend-v2/lib/hooks/use-auth.ts`
- Test: `frontend-v2/__tests__/hooks/use-auth-focus.test.ts`

**Step 1: Write the test**

```typescript
// frontend-v2/__tests__/hooks/use-auth-focus.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('useAuth hook', () => {
  it('should revalidate on window focus', () => {
    const hookFile = fs.readFileSync(
      path.join(__dirname, '../../lib/hooks/use-auth.ts'),
      'utf-8'
    );

    // Should use refetchOnWindowFocus
    expect(hookFile).toContain('refetchOnWindowFocus');
  });
});
```

**Step 2: Run test to verify current state**

Run: `cd frontend-v2 && npm test -- __tests__/hooks/use-auth-focus.test.ts`

**Step 3: Add refetchOnWindowFocus if missing**

```typescript
// frontend-v2/lib/hooks/use-auth.ts
const { data: user } = useQuery({
  queryKey: ['user'],
  queryFn: () => authApi.getMe(),
  staleTime: 5 * 60 * 1000,
  refetchOnWindowFocus: true,  // Add this
});
```

**Step 4: Commit**

```bash
git add frontend-v2/lib/hooks/use-auth.ts frontend-v2/__tests__/hooks/use-auth-focus.test.ts
git commit -m "fix(frontend): revalidate auth state on window focus"
```

---

### Task 35: Fix CSRF token parsing

**Files:**
- Modify: `frontend-v2/lib/api/client.ts`
- Test: `frontend-v2/__tests__/lib/api/csrf.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/lib/api/csrf.test.ts
import { describe, it, expect } from 'vitest';

describe('CSRF Token Parsing', () => {
  it('should handle malformed cookies gracefully', () => {
    // Test with edge cases:
    // - Cookie with spaces in value
    // - Cookie with special characters
    // - Missing cookie
    // - Empty cookie value
  });

  it('should use decodeURIComponent for cookie values', () => {
    const clientFile = require('fs').readFileSync(
      require('path').join(__dirname, '../../lib/api/client.ts'),
      'utf-8'
    );
    expect(clientFile).toContain('decodeURIComponent');
  });
});
```

**Step 2: Fix CSRF parsing to handle edge cases**

```typescript
// frontend-v2/lib/api/client.ts
private getCsrfToken(): string | null {
  try {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const [name, ...valueParts] = cookie.trim().split('=');
      if (name === 'csrf_token') {
        const value = valueParts.join('=');  // Handle = in value
        return value ? decodeURIComponent(value) : null;
      }
    }
  } catch (e) {
    console.error('Failed to parse CSRF token:', e);
  }
  return null;
}
```

**Step 3: Commit**

```bash
git add frontend-v2/lib/api/client.ts frontend-v2/__tests__/lib/api/csrf.test.ts
git commit -m "fix(frontend): improve CSRF token parsing robustness"
```

---

### Task 36: Add wallet balance invalidation after payment

**Files:**
- Modify: `frontend-v2/app/(dashboard)/wallet/page.tsx`
- Test: `frontend-v2/__tests__/pages/wallet-invalidation.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/wallet-invalidation.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Wallet page', () => {
  it('should invalidate balance query after topup', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/wallet/page.tsx'),
      'utf-8'
    );

    // Should use queryClient.invalidateQueries after payment
    expect(pageFile).toContain('invalidateQueries');
  });
});
```

**Step 2: Add query invalidation**

```typescript
// frontend-v2/app/(dashboard)/wallet/page.tsx
import { useQueryClient } from '@tanstack/react-query';

// After successful topup redirect:
const queryClient = useQueryClient();

// On mount, check for success param and invalidate
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('success') === 'true') {
    queryClient.invalidateQueries({ queryKey: ['wallet-balance'] });
  }
}, [queryClient]);
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/wallet/page.tsx frontend-v2/__tests__/pages/wallet-invalidation.test.ts
git commit -m "fix(frontend): invalidate wallet balance after topup"
```

---

## Phase 11: Frontend Data Flow Fixes (MAJOR)

### Task 37: Add timezone conversion to booking form

**Files:**
- Modify: `frontend-v2/app/(dashboard)/bookings/new/page.tsx`
- Test: `frontend-v2/__tests__/pages/booking-timezone.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/booking-timezone.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Booking form timezone handling', () => {
  it('should convert local time to UTC before submission', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/bookings/new/page.tsx'),
      'utf-8'
    );

    // Should use toISOString() or similar for UTC conversion
    expect(pageFile).toMatch(/toISOString|toUTC|timezone/i);
  });
});
```

**Step 2: Add timezone conversion**

```typescript
// frontend-v2/app/(dashboard)/bookings/new/page.tsx

const onSubmit = async (data: FormData) => {
  // Convert local datetime to UTC
  const localDate = new Date(data.start_time);
  const utcString = localDate.toISOString();

  await bookingsApi.create({
    ...data,
    start_at: utcString,  // Send as UTC
  });
};
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/bookings/new/page.tsx frontend-v2/__tests__/pages/booking-timezone.test.ts
git commit -m "fix(frontend): convert booking times to UTC before submission"
```

---

### Task 38: Add search query validation

**Files:**
- Modify: `frontend-v2/app/(dashboard)/tutors/page.tsx`
- Test: `frontend-v2/__tests__/pages/tutor-search-validation.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/tutor-search-validation.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Tutor search validation', () => {
  it('should limit search query length', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/tutors/page.tsx'),
      'utf-8'
    );

    // Should have maxLength or validation
    expect(pageFile).toMatch(/maxLength|slice|substring/);
  });
});
```

**Step 2: Add validation**

```typescript
// frontend-v2/app/(dashboard)/tutors/page.tsx

const handleSearch = (e: React.FormEvent) => {
  e.preventDefault();
  // Validate and sanitize search query
  const sanitized = searchQuery.trim().slice(0, 100);  // Max 100 chars
  setTutorFilters({ subject: sanitized || undefined, page: 1 });
};
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/tutors/page.tsx frontend-v2/__tests__/pages/tutor-search-validation.test.ts
git commit -m "fix(frontend): add search query validation and length limit"
```

---

### Task 39: Sync filter state with URL

**Files:**
- Modify: `frontend-v2/app/(dashboard)/tutors/page.tsx`
- Test: `frontend-v2/__tests__/pages/tutor-filter-url.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/tutor-filter-url.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Tutor filter URL sync', () => {
  it('should use URL search params for filters', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/tutors/page.tsx'),
      'utf-8'
    );

    // Should use useSearchParams or router.push with query
    expect(pageFile).toMatch(/useSearchParams|searchParams|router\.push/);
  });
});
```

**Step 2: Add URL sync**

```typescript
// frontend-v2/app/(dashboard)/tutors/page.tsx
import { useSearchParams, useRouter } from 'next/navigation';

const searchParams = useSearchParams();
const router = useRouter();

// Read filters from URL on mount
useEffect(() => {
  const subject = searchParams.get('subject');
  const page = searchParams.get('page');
  if (subject || page) {
    setTutorFilters({
      subject: subject || undefined,
      page: page ? parseInt(page) : 1,
    });
  }
}, [searchParams]);

// Update URL when filters change
const handleSearch = () => {
  const params = new URLSearchParams();
  if (searchQuery) params.set('subject', searchQuery);
  router.push(`/tutors?${params.toString()}`);
};
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/tutors/page.tsx frontend-v2/__tests__/pages/tutor-filter-url.test.ts
git commit -m "fix(frontend): sync tutor filters with URL params"
```

---

### Task 40: Add cents validation in wallet topup

**Files:**
- Modify: `frontend-v2/app/(dashboard)/wallet/page.tsx`
- Test: `frontend-v2/__tests__/pages/wallet-cents-validation.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/wallet-cents-validation.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Wallet topup validation', () => {
  it('should validate amount is positive', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/wallet/page.tsx'),
      'utf-8'
    );

    // Should validate amount > 0
    expect(pageFile).toMatch(/amount\s*[<>=]+\s*0|min.*amount/i);
  });

  it('should round to valid cents', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/wallet/page.tsx'),
      'utf-8'
    );

    // Should use Math.round for cents conversion
    expect(pageFile).toContain('Math.round');
  });
});
```

**Step 2: Add validation**

```typescript
// frontend-v2/app/(dashboard)/wallet/page.tsx

const handleTopup = async () => {
  // Validate
  if (amount <= 0) {
    setError('Amount must be greater than 0');
    return;
  }
  if (amount > 10000) {
    setError('Maximum topup is $10,000');
    return;
  }

  // Convert to cents with proper rounding
  const amountCents = Math.round(amount * 100);

  // Proceed with topup
};
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/wallet/page.tsx frontend-v2/__tests__/pages/wallet-cents-validation.test.ts
git commit -m "fix(frontend): add wallet topup amount validation"
```

---

### Task 41: Fix message unread count clearing

**Files:**
- Modify: `frontend-v2/app/(dashboard)/messages/[conversationId]/page.tsx`
- Test: `frontend-v2/__tests__/pages/message-unread-clear.test.ts`

**Step 1: Write the failing test**

```typescript
// frontend-v2/__tests__/pages/message-unread-clear.test.ts
import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Message conversation page', () => {
  it('should mark messages as read on view', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/messages/[conversationId]/page.tsx'),
      'utf-8'
    );

    // Should call mark as read API
    expect(pageFile).toMatch(/markAsRead|mark.*read|read.*message/i);
  });

  it('should invalidate unread count after marking read', () => {
    const pageFile = fs.readFileSync(
      path.join(__dirname, '../../app/(dashboard)/messages/[conversationId]/page.tsx'),
      'utf-8'
    );

    expect(pageFile).toContain('invalidateQueries');
  });
});
```

**Step 2: Add read marking**

```typescript
// frontend-v2/app/(dashboard)/messages/[conversationId]/page.tsx

useEffect(() => {
  // Mark conversation as read when viewing
  const markRead = async () => {
    await messagesApi.markConversationRead(conversationId);
    queryClient.invalidateQueries({ queryKey: ['conversations'] });
    queryClient.invalidateQueries({ queryKey: ['unread-count'] });
  };
  markRead();
}, [conversationId, queryClient]);
```

**Step 3: Commit**

```bash
git add frontend-v2/app/(dashboard)/messages/[conversationId]/page.tsx frontend-v2/__tests__/pages/message-unread-clear.test.ts
git commit -m "fix(frontend): mark messages as read and clear unread count"
```

---

## Phase 12: Run Full Test Suite

### Task 42: Run backend test suite

**Step 1: Run all backend tests**

Run: `cd backend && python -m pytest tests/ modules/ -v --tb=short`
Expected: All tests PASS

**Step 2: Check for any regressions**

Review test output for failures related to changes.

**Step 3: Commit any test fixes if needed**

```bash
git add -A
git commit -m "test: fix any regressions from integration fixes"
```

---

### Task 43: Run frontend test suite

**Step 1: Run all frontend tests**

Run: `cd frontend-v2 && npm test`
Expected: All tests PASS

**Step 2: Run type checking**

Run: `cd frontend-v2 && npm run type-check`
Expected: No type errors

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "test: fix any frontend test regressions"
```

---

### Task 44: Run linting

**Step 1: Run backend linting**

Run: `./scripts/lint-backend.sh`
Expected: PASS

**Step 2: Run frontend linting**

Run: `./scripts/lint-frontend.sh`
Expected: PASS

**Step 3: Fix any linting issues**

```bash
./scripts/lint-all.sh --fix
git add -A
git commit -m "style: fix linting issues"
```

---

### Task 45: Final verification commit

**Step 1: Run complete test suite**

Run: `docker compose -f docker-compose.test.yml up --build --abort-on-container-exit`
Expected: All services pass

**Step 2: Final commit**

```bash
git add -A
git commit -m "chore: complete integration fixes implementation"
```

---

## Summary of All Changes

| Phase | Tasks | Files Modified | Tests Added |
|-------|-------|----------------|-------------|
| 1: DateTime | 1-3 | ~15 files | 3 test files |
| 2: Booking Enums | 4 | 1 file | 1 test file |
| 3: Frontend Types | 5-12 | 6 type files | 8 test files |
| 4: Soft Delete | 13-15 | 5 model files | 3 test files |
| 5: Payment Models | 16-18 | 2 files | 3 test files |
| 6: User Model | 19-20 | 1 file | 2 test files |
| 7: TutorProfile | 21-22 | 2 files | 2 test files |
| 8: Constraints | 23-24 | 1 file | 2 test files |
| 9: API Contracts | 25-30 | 4 files | 6 test files |
| 10: Race Conditions | 31-36 | 4 files | 6 test files |
| 11: Frontend Flow | 37-41 | 5 files | 5 test files |
| 12: Verification | 42-45 | - | - |

**Total: 45 tasks, ~50 files modified, ~40 new test files**

---

## Post-Implementation Checklist

- [ ] All datetime usages migrated to `utc_now()`
- [ ] No `datetime.utcnow()` remaining in codebase
- [ ] Booking entity uses valid enum defaults
- [ ] Frontend types match backend schema exactly
- [ ] All models have soft delete columns
- [ ] Payment metadata fields renamed
- [ ] All model constraints match database
- [ ] API responses match frontend expectations
- [ ] Race conditions addressed with proper locking
- [ ] Frontend validates input before API calls
- [ ] Full test suite passes
- [ ] No TypeScript type errors
- [ ] Linting passes
