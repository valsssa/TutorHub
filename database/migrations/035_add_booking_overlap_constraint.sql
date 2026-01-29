-- Migration 035: Add PostgreSQL exclusion constraint to prevent booking overlaps
-- This provides database-level protection against double-booking race conditions
-- as a safety net in addition to application-level row locking

-- First, ensure the btree_gist extension is available for exclusion constraints
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Drop the old unique index that only prevented exact time matches
DROP INDEX IF EXISTS idx_bookings_no_overlap;

-- Create an exclusion constraint that prevents any time range overlaps
-- for the same tutor in active booking states
--
-- The constraint uses:
-- - btree_gist for combining equality (=) with range overlap (&&)
-- - tstzrange for time range overlap detection
-- - Only active states: REQUESTED, SCHEDULED, ACTIVE
--
-- Note: PostgreSQL exclusion constraints guarantee atomicity at the database level,
-- preventing any overlapping bookings even under heavy concurrent load
ALTER TABLE bookings
ADD CONSTRAINT bookings_no_time_overlap
EXCLUDE USING gist (
    tutor_profile_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE'));

-- Add an index to support the constraint and improve query performance
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_time_range
ON bookings USING gist (tutor_profile_id, tstzrange(start_time, end_time, '[)'))
WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE');

-- Add comment documenting the constraint
COMMENT ON CONSTRAINT bookings_no_time_overlap ON bookings IS
'Prevents double-booking by ensuring no two active bookings for the same tutor have overlapping time ranges';
