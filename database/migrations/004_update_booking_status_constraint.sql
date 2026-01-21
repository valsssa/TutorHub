-- Migration 004: Extend booking status constraint
-- Ensures the constraint mirrors the application state machine.

ALTER TABLE bookings
  DROP CONSTRAINT IF EXISTS valid_booking_status;

ALTER TABLE bookings
  ADD CONSTRAINT valid_booking_status CHECK (
    status IN (
      'PENDING',
      'CONFIRMED',
      'CANCELLED_BY_STUDENT',
      'CANCELLED_BY_TUTOR',
      'NO_SHOW_STUDENT',
      'NO_SHOW_TUTOR',
      'COMPLETED',
      'REFUNDED'
    )
  );

COMMENT ON CONSTRAINT valid_booking_status ON bookings IS
  'Validates against the current BookingService state machine';
