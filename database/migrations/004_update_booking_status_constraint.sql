-- Migration 004: Validate four-field booking status system
-- The bookings table uses four independent status fields:
--   session_state, session_outcome, payment_state, dispute_state
-- This migration adds constraints to validate each field.

-- Drop legacy constraint if it exists (was for old single 'status' column)
ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS valid_booking_status;

-- Constraint for session_state (booking lifecycle)
ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS valid_session_state;

ALTER TABLE bookings
  ADD CONSTRAINT valid_session_state CHECK (
    session_state IN (
      'REQUESTED',
      'SCHEDULED',
      'ACTIVE',
      'ENDED',
      'EXPIRED',
      'CANCELLED'
    )
  );

-- Constraint for payment_state
ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS valid_payment_state;

ALTER TABLE bookings
  ADD CONSTRAINT valid_payment_state CHECK (
    payment_state IN (
      'PENDING',
      'AUTHORIZED',
      'CAPTURED',
      'VOIDED',
      'REFUNDED',
      'PARTIALLY_REFUNDED'
    )
  );

-- Constraint for dispute_state
ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS valid_dispute_state;

ALTER TABLE bookings
  ADD CONSTRAINT valid_dispute_state CHECK (
    dispute_state IN (
      'NONE',
      'OPEN',
      'RESOLVED_UPHELD',
      'RESOLVED_REFUNDED'
    )
  );

-- session_outcome is nullable (only set for terminal states)
-- No constraint needed as it's validated at application level

COMMENT ON CONSTRAINT valid_session_state ON bookings IS
  'Validates session lifecycle states per BookingStateMachine';
COMMENT ON CONSTRAINT valid_payment_state ON bookings IS
  'Validates payment lifecycle states';
COMMENT ON CONSTRAINT valid_dispute_state ON bookings IS
  'Validates dispute lifecycle states';
