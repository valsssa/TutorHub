-- Migration: 052_fix_booking_overlap_constraint.sql
-- Description: Fix double-booking prevention with proper GIST exclusion constraint
-- Author: Claude
-- Date: 2026-02-05
--
-- Problem:
-- The old UNIQUE INDEX only prevented exact time matches, not overlapping time ranges:
--   CREATE UNIQUE INDEX idx_bookings_no_overlap
--   ON bookings (tutor_profile_id, start_time, end_time)
--   WHERE session_state IN ('REQUESTED', 'SCHEDULED');
--
-- This allowed overlapping bookings like:
--   - Tutor1 booked 1PM-2PM AND 1:30PM-2:30PM (OVERLAPPING!)
--
-- Solution:
-- Use PostgreSQL GIST-based EXCLUDE constraint with btree_gist extension.
-- The tstzrange type with && operator detects ANY overlap, not just exact matches.
--
-- How GIST exclusion prevents overlaps:
-- - tstzrange(start_time, end_time, '[)') creates a half-open time range [start, end)
-- - The && operator returns TRUE if two ranges overlap at any point
-- - EXCLUDE USING gist ensures no two rows can have overlapping ranges for the same tutor
-- - This is enforced atomically at the database level, preventing race conditions
--
-- Example: If Tutor1 has booking 1PM-2PM [13:00, 14:00):
-- - Attempting 1:30PM-2:30PM [13:30, 14:30) will FAIL because [13:00, 14:00) && [13:30, 14:30) = TRUE
-- - Attempting 2PM-3PM [14:00, 15:00) will SUCCEED because [13:00, 14:00) && [14:00, 15:00) = FALSE
--   (the '[)' means end time is exclusive, so 14:00 doesn't overlap with itself)

BEGIN;

-- =============================================================================
-- STEP 1: Ensure btree_gist extension is available
-- =============================================================================
-- Required for combining equality (=) with range overlap (&&) in exclusion constraints

CREATE EXTENSION IF NOT EXISTS btree_gist;

-- =============================================================================
-- STEP 2: Check for existing overlapping bookings BEFORE applying constraint
-- =============================================================================
-- This helps identify data issues that need manual resolution

DO $$
DECLARE
    overlap_count INTEGER;
    overlap_details TEXT;
BEGIN
    -- Find overlapping bookings for the same tutor in active states
    WITH overlaps AS (
        SELECT
            b1.id AS booking1_id,
            b2.id AS booking2_id,
            b1.tutor_profile_id,
            b1.start_time AS b1_start,
            b1.end_time AS b1_end,
            b2.start_time AS b2_start,
            b2.end_time AS b2_end,
            b1.session_state AS b1_state,
            b2.session_state AS b2_state
        FROM bookings b1
        JOIN bookings b2 ON b1.tutor_profile_id = b2.tutor_profile_id
            AND b1.id < b2.id  -- Avoid counting same pair twice
            AND b1.session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE')
            AND b2.session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE')
            AND b1.deleted_at IS NULL
            AND b2.deleted_at IS NULL
            AND tstzrange(b1.start_time, b1.end_time, '[)') && tstzrange(b2.start_time, b2.end_time, '[)')
    )
    SELECT COUNT(*), string_agg(
        'Booking ' || booking1_id || ' (' || b1_state || ': ' || b1_start || ' - ' || b1_end || ') overlaps with ' ||
        'Booking ' || booking2_id || ' (' || b2_state || ': ' || b2_start || ' - ' || b2_end || ')',
        E'\n'
    )
    INTO overlap_count, overlap_details
    FROM overlaps;

    IF overlap_count > 0 THEN
        RAISE WARNING 'Found % overlapping booking pair(s) that need resolution:', overlap_count;
        RAISE WARNING E'%', overlap_details;
        RAISE WARNING 'These must be resolved before the constraint can be applied.';
        RAISE WARNING 'Options: Cancel one booking, change times, or mark one as deleted.';
        -- For safety, we'll continue but log the warning
        -- In production, you might want to RAISE EXCEPTION instead
    ELSE
        RAISE NOTICE 'No overlapping bookings found. Safe to apply constraint.';
    END IF;
END $$;

-- =============================================================================
-- STEP 3: Drop the old insufficient UNIQUE INDEX if it exists
-- =============================================================================
-- The old index only prevented exact time matches, not overlaps

DROP INDEX IF EXISTS idx_bookings_no_overlap;

-- Also drop the constraint if it already exists (idempotency)
ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_no_time_overlap;

-- =============================================================================
-- STEP 4: Add the GIST-based EXCLUDE constraint
-- =============================================================================
-- This constraint prevents any overlapping time ranges for the same tutor
-- in active booking states (REQUESTED, SCHEDULED, ACTIVE)
--
-- Key aspects:
-- - tutor_profile_id WITH = : Same tutor
-- - tstzrange(start_time, end_time, '[)') WITH && : Overlapping time ranges
-- - '[)' means half-open interval: includes start, excludes end
--   So booking 1-2PM [13:00, 14:00) does NOT conflict with 2-3PM [14:00, 15:00)
-- - WHERE clause limits to active states (soft-deleted records are ignored)

ALTER TABLE bookings
ADD CONSTRAINT bookings_no_time_overlap
EXCLUDE USING gist (
    tutor_profile_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE') AND deleted_at IS NULL);

-- =============================================================================
-- STEP 5: Add supporting index for query performance
-- =============================================================================
-- This index helps with time range queries even outside of constraint enforcement

DROP INDEX IF EXISTS idx_bookings_tutor_time_range;

CREATE INDEX IF NOT EXISTS idx_bookings_tutor_time_range
ON bookings USING gist (tutor_profile_id, tstzrange(start_time, end_time, '[)'))
WHERE session_state IN ('REQUESTED', 'SCHEDULED', 'ACTIVE') AND deleted_at IS NULL;

-- =============================================================================
-- STEP 6: Add documentation
-- =============================================================================

COMMENT ON CONSTRAINT bookings_no_time_overlap ON bookings IS
'Prevents double-booking by ensuring no two active bookings (REQUESTED, SCHEDULED, ACTIVE) '
'for the same tutor have overlapping time ranges. Uses GIST exclusion constraint with '
'tstzrange for proper overlap detection. Soft-deleted records are excluded.';

-- =============================================================================
-- STEP 7: Verification
-- =============================================================================

DO $$
DECLARE
    constraint_exists BOOLEAN;
    old_index_exists BOOLEAN;
BEGIN
    -- Verify constraint was created
    SELECT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_no_time_overlap'
        AND conrelid = 'bookings'::regclass
    ) INTO constraint_exists;

    -- Verify old index is gone
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE indexname = 'idx_bookings_no_overlap'
    ) INTO old_index_exists;

    IF NOT constraint_exists THEN
        RAISE EXCEPTION 'Migration 052 failed: bookings_no_time_overlap constraint was not created';
    END IF;

    IF old_index_exists THEN
        RAISE EXCEPTION 'Migration 052 failed: Old idx_bookings_no_overlap index still exists';
    END IF;

    RAISE NOTICE 'Migration 052 completed successfully:';
    RAISE NOTICE '  - Old UNIQUE INDEX idx_bookings_no_overlap: REMOVED';
    RAISE NOTICE '  - New EXCLUDE constraint bookings_no_time_overlap: CREATED';
    RAISE NOTICE '  - Supporting GIST index: CREATED';
    RAISE NOTICE '  - Protection scope: REQUESTED, SCHEDULED, ACTIVE states';
    RAISE NOTICE '  - Soft-deleted records: EXCLUDED from constraint';
END $$;

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('052', 'Fix double-booking prevention with proper GIST exclusion constraint')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- =============================================================================
-- ROLLBACK Section (if needed, run manually)
-- =============================================================================
--
-- BEGIN;
--
-- -- Remove the GIST exclusion constraint
-- ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_no_time_overlap;
--
-- -- Remove the supporting GIST index
-- DROP INDEX IF EXISTS idx_bookings_tutor_time_range;
--
-- -- Restore the old UNIQUE INDEX (not recommended - less protection)
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_no_overlap
-- ON bookings (tutor_profile_id, start_time, end_time)
-- WHERE session_state IN ('REQUESTED', 'SCHEDULED');
--
-- -- Remove migration record
-- DELETE FROM schema_migrations WHERE version = '052';
--
-- COMMIT;
-- =============================================================================
