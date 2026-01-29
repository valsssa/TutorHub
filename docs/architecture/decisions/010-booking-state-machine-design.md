# ADR-010: Booking State Machine Design

## Status

Accepted

## Date

2026-01-29

## Context

Session bookings in EduStream have complex lifecycle requirements:
- Sessions progress through multiple stages (requested, scheduled, active, ended)
- Payment authorization must be held during session, then captured or refunded
- Disputes can arise after session completion
- Multiple actors can trigger transitions (student, tutor, admin, system/scheduler)
- Different actors have different permissions for different transitions
- State changes must be atomic and auditable
- Concurrent operations must be handled safely (race conditions)

A naive single-status approach would require 40+ enum values to represent all valid combinations of session state, payment state, and dispute state.

## Decision

We will use a **four-field state model** with a centralized `BookingStateMachine` class enforcing all transitions.

### Four-Field Model

```python
class SessionState(Enum):
    REQUESTED = "REQUESTED"    # Awaiting tutor response
    SCHEDULED = "SCHEDULED"    # Confirmed, upcoming
    ACTIVE = "ACTIVE"          # In progress
    ENDED = "ENDED"            # Terminal
    EXPIRED = "EXPIRED"        # Terminal (24h timeout)
    CANCELLED = "CANCELLED"    # Terminal

class SessionOutcome(Enum):
    COMPLETED = "COMPLETED"       # Session happened
    NOT_HELD = "NOT_HELD"         # Never happened (cancelled/expired)
    NO_SHOW_STUDENT = "NO_SHOW_STUDENT"
    NO_SHOW_TUTOR = "NO_SHOW_TUTOR"

class PaymentState(Enum):
    PENDING = "PENDING"           # Awaiting authorization
    AUTHORIZED = "AUTHORIZED"     # Funds held
    CAPTURED = "CAPTURED"         # Tutor paid
    VOIDED = "VOIDED"             # Released without capture
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"

class DisputeState(Enum):
    NONE = "NONE"
    OPEN = "OPEN"
    RESOLVED_UPHELD = "RESOLVED_UPHELD"
    RESOLVED_REFUNDED = "RESOLVED_REFUNDED"
```

### Transition Rules

Session state transitions (forward-only):
```
REQUESTED → SCHEDULED (tutor accepts)
REQUESTED → CANCELLED (declined/cancelled)
REQUESTED → EXPIRED (24h timeout via scheduler)
SCHEDULED → ACTIVE (auto at start_time via scheduler)
SCHEDULED → CANCELLED (manual cancellation)
ACTIVE → ENDED (auto at end_time + grace via scheduler)
```

Payment state transitions:
```
PENDING → AUTHORIZED (on booking acceptance)
PENDING → VOIDED (cancelled before auth)
AUTHORIZED → CAPTURED (session completed successfully)
AUTHORIZED → VOIDED (cancelled after auth)
AUTHORIZED → REFUNDED (tutor no-show or dispute)
CAPTURED → REFUNDED (dispute resolution)
CAPTURED → PARTIALLY_REFUNDED (partial refund)
```

Dispute state transitions:
```
NONE → OPEN (user files dispute)
OPEN → RESOLVED_UPHELD (admin decision: original stands)
OPEN → RESOLVED_REFUNDED (admin decision: issue refund)
```

### State Machine Implementation

```python
class BookingStateMachine:
    @classmethod
    def accept_booking(cls, booking: Booking) -> TransitionResult:
        """REQUESTED → SCHEDULED, PENDING → AUTHORIZED"""

    @classmethod
    def cancel_booking(cls, booking: Booking, by: Role) -> TransitionResult:
        """REQUESTED/SCHEDULED → CANCELLED"""

    @classmethod
    def expire_booking(cls, booking: Booking) -> TransitionResult:
        """REQUESTED → EXPIRED (system job)"""

    @classmethod
    def start_session(cls, booking: Booking) -> TransitionResult:
        """SCHEDULED → ACTIVE (system job)"""

    @classmethod
    def end_session(cls, booking: Booking, outcome: Outcome) -> TransitionResult:
        """ACTIVE → ENDED (system job or manual)"""

    @classmethod
    def mark_no_show(cls, booking: Booking, who: str, reporter: str) -> TransitionResult:
        """Handle no-show with conflict detection"""

    @classmethod
    def open_dispute(cls, booking: Booking, reason: str) -> TransitionResult:
        """NONE → OPEN"""

    @classmethod
    def resolve_dispute(cls, booking: Booking, resolution: DisputeState) -> TransitionResult:
        """OPEN → RESOLVED_*"""
```

### Race Condition Prevention

Two-layer locking strategy:

1. **Pessimistic locking**: `SELECT FOR UPDATE` on booking row
   ```python
   booking = db.query(Booking).filter(...).with_for_update(nowait=True).first()
   ```

2. **Optimistic locking**: Version column incremented on each transition
   ```python
   booking.version = (booking.version or 1) + 1
   ```

3. **Idempotent transitions**: Success if already in target state
   ```python
   if booking.session_state == SessionState.SCHEDULED.value:
       return TransitionResult(success=True, already_in_target_state=True)
   ```

## Consequences

### Positive

- **Query flexibility**: Easy to query by any dimension
  - "All disputed bookings": `WHERE dispute_state = 'OPEN'`
  - "Payment issues": `WHERE payment_state IN ('PENDING', 'AUTHORIZED')`
- **Independent evolution**: Add payment states without touching session logic
- **Explicit states**: No hidden combinations or invalid states
- **Testable**: Pure Python class with no database dependencies
- **Race-safe**: Locking strategy prevents concurrent modification issues
- **Idempotent**: Safe for retries and background job restarts

### Negative

- **Complexity**: Four fields to understand vs one
- **Validation overhead**: Must check valid combinations
- **Learning curve**: Engineers must understand the model
- **More columns**: Database schema slightly more complex

### Neutral

- Legacy single-status can be computed for backward compatibility
- State machine methods handle all field coordination
- Audit trail captured via updated_at timestamps

## Alternatives Considered

### Option A: Single Status Enum

One field with all combinations: `PENDING_AWAITING_PAYMENT`, `CONFIRMED_PAYMENT_HELD`, etc.

**Pros:**
- Simple mental model
- One field to check

**Cons:**
- 40+ enum values needed
- Cannot query by dimension
- Adding states causes combinatorial explosion
- Hard to extend

**Why not chosen:** Doesn't scale with feature additions.

### Option B: Event Sourcing

Store all state changes as events, derive current state.

**Pros:**
- Complete audit trail
- Time-travel debugging
- Flexible projections

**Cons:**
- Significant complexity
- Query performance requires read models
- Team unfamiliar with pattern

**Why not chosen:** Overkill for current audit requirements; can adopt later.

### Option C: State Machine Library

Use `transitions` or similar library.

**Pros:**
- Visualization tools
- Tested implementations
- Declarative configuration

**Cons:**
- External dependency
- May not support multi-field model
- Library learning curve

**Why not chosen:** Custom implementation cleaner for four-field model.

### Option D: Database Triggers

Enforce transitions at database level.

**Pros:**
- Enforced regardless of code path
- Cannot be bypassed

**Cons:**
- Logic split between Python and SQL
- Harder to test
- Less flexible error handling

**Why not chosen:** Business logic should live in application layer.

## Policy Engine Design

Transition permissions are checked by the state machine:

```python
# Who can perform which transitions
TRANSITION_PERMISSIONS = {
    "accept": ["tutor"],
    "decline": ["tutor"],
    "cancel": ["student", "tutor", "admin", "system"],
    "expire": ["system"],
    "start": ["system"],
    "end": ["system"],
    "mark_no_show": ["student", "tutor"],
    "open_dispute": ["student", "tutor"],
    "resolve_dispute": ["admin"],
}
```

Future enhancement: Extract to configurable policy engine for:
- Time-based rules (can't cancel < 24h before)
- Role-based overrides
- A/B testing of policies

## References

- State machine: `backend/modules/bookings/domain/state_machine.py`
- Status enums: `backend/modules/bookings/domain/status.py`
- Background jobs: `backend/modules/bookings/jobs.py`
- Database migration: `database/migrations/034_booking_status_redesign.sql`
- Related: ADR-002 (Four-Field Booking State Machine)
