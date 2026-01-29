# ADR-002: Four-Field Booking State Machine

## Status

Accepted

## Date

2026-01-29

## Context

Session bookings in a tutoring marketplace have complex lifecycle requirements:
- Sessions move through multiple stages (requested, confirmed, active, completed)
- Payment state must track authorization, capture, and refunds
- Disputes can be filed after session completion
- Different actors (student, tutor, admin, system) can trigger transitions
- State changes must be atomic and auditable

A single status field would require 40+ enum values to represent all combinations.

## Decision

We will use a **four-field state machine** for booking status:

1. **session_state**: The session lifecycle
   - REQUESTED, SCHEDULED, ACTIVE, ENDED, CANCELLED, EXPIRED

2. **session_outcome**: The result of a completed session
   - COMPLETED, NOT_HELD, NO_SHOW_STUDENT, NO_SHOW_TUTOR

3. **payment_state**: The payment lifecycle
   - PENDING, AUTHORIZED, CAPTURED, VOIDED, REFUNDED, PARTIALLY_REFUNDED

4. **dispute_state**: The dispute lifecycle
   - NONE, OPEN, RESOLVED_UPHELD, RESOLVED_REFUNDED

State transitions are enforced by a pure Python `BookingStateMachine` class in the domain layer.

## Consequences

### Positive

- **Query flexibility**: "All bookings with open disputes" is a simple WHERE clause
- **Independent evolution**: Each concern can evolve separately
- **Explicit states**: No implicit state combinations
- **Testable**: Pure Python class with no dependencies
- **Auditable**: Each field change can be logged independently

### Negative

- **Complexity**: Four fields to track instead of one
- **Validation overhead**: Must ensure valid field combinations
- **Learning curve**: Engineers must understand four state machines

### Neutral

- Legacy single-status computed for backward compatibility
- Migration from old status required careful data transformation

## Alternatives Considered

### Option A: Single Status Enum

One field with all possible states: PENDING_TUTOR_RESPONSE, CONFIRMED_PAYMENT_PENDING, etc.

**Pros:**
- Simple queries for exact state
- Single field to update

**Cons:**
- 40+ enum values
- Hard to query by dimension ("all with payment issues")
- Combinatorial explosion on new states

**Why not chosen:** Unmaintainable enum size and inflexible queries.

### Option B: Event Sourcing

Store state as a sequence of events, derive current state.

**Pros:**
- Complete audit trail
- Flexible projections
- Event replay capability

**Cons:**
- Significant complexity increase
- Query performance concerns
- Team unfamiliar with pattern

**Why not chosen:** Complexity not justified for current audit needs.

### Option C: State Machine Library

Use a library like `transitions` or `xstate` for state management.

**Pros:**
- Visualization tools
- Battle-tested implementations

**Cons:**
- External dependency
- Learning curve for specific library
- May not fit multi-field model

**Why not chosen:** Custom implementation simpler for our multi-field needs.

## References

- Implementation: `backend/modules/bookings/domain/state_machine.py`
- Status enums: `backend/modules/bookings/domain/status.py`
- Migration: `database/migrations/034_booking_status_redesign.sql`
