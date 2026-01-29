-- ============================================================================
-- Migration 040: Add Session Attendance Tracking
--
-- Adds columns to track when participants join sessions, enabling
-- attendance-based outcome determination for auto-ended sessions.
--
-- Problem solved:
-- - Very short sessions (25 min) with technical difficulties were being
--   auto-ended with COMPLETED outcome even when neither party joined
-- - This led to incorrect payment captures and poor user experience
--
-- Solution:
-- - Track actual join times for tutor and student
-- - Use attendance data to determine appropriate session outcome:
--   - Neither joined -> NOT_HELD (void payment)
--   - Only student joined -> NO_SHOW_TUTOR (refund)
--   - Only tutor joined -> NO_SHOW_STUDENT (capture payment)
--   - Both joined -> COMPLETED (capture payment)
-- ============================================================================

-- Add tutor join timestamp
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS tutor_joined_at TIMESTAMP WITH TIME ZONE;

-- Add student join timestamp
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS student_joined_at TIMESTAMP WITH TIME ZONE;

-- Add comment for documentation
COMMENT ON COLUMN bookings.tutor_joined_at IS 'Timestamp when tutor clicked join/entered the session';
COMMENT ON COLUMN bookings.student_joined_at IS 'Timestamp when student clicked join/entered the session';

-- Create index for finding sessions where attendance needs to be checked
-- (active sessions without attendance recorded)
CREATE INDEX IF NOT EXISTS idx_bookings_attendance_check
    ON bookings(session_state, tutor_joined_at, student_joined_at)
    WHERE session_state = 'ACTIVE';

DO $$
BEGIN
    RAISE NOTICE 'Migration 040_add_session_attendance_tracking completed';
END $$;
