-- ============================================================================
-- Migration 002: Fix Favorites Unique Constraint for Soft Delete Support
-- ============================================================================
--
-- Problem:
-- The existing uq_favorite UNIQUE constraint on (student_id, tutor_profile_id)
-- applies to ALL rows, including soft-deleted ones (where deleted_at IS NOT NULL).
-- This blocks re-favoriting a tutor after unfavoriting because the soft-deleted
-- row still exists and violates the uniqueness constraint.
--
-- Solution:
-- Replace the table-level UNIQUE constraint with a partial unique index that
-- only enforces uniqueness for active (non-deleted) rows.
--
-- Date: 2026-02-06
-- ============================================================================

-- Step 1: Drop the existing UNIQUE constraint
-- Note: PostgreSQL requires dropping the constraint by name
ALTER TABLE favorite_tutors DROP CONSTRAINT IF EXISTS uq_favorite;

-- Step 2: Create partial unique index for active favorites only
-- This ensures a student can only have ONE active favorite per tutor,
-- but allows re-favoriting after soft delete (creating a new row while
-- the old soft-deleted row remains for audit purposes)
CREATE UNIQUE INDEX IF NOT EXISTS idx_favorite_tutors_unique_active
    ON favorite_tutors(student_id, tutor_profile_id)
    WHERE deleted_at IS NULL;

-- Step 3: Add missing index on tutor_profile_id for efficient lookups
-- This improves performance when querying "which students favorited this tutor"
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_tutor
    ON favorite_tutors(tutor_profile_id);

-- ============================================================================
-- Verification Query (optional - run manually to confirm migration)
-- ============================================================================
-- Check that the old constraint is gone and new index exists:
--
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'favorite_tutors';
--
-- Expected output should include:
--   idx_favorite_tutors_unique_active (partial unique index with WHERE clause)
--   idx_favorite_tutors_tutor (regular index)
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Migration 002: Fix Favorites Unique Constraint';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Changes applied:';
    RAISE NOTICE '  1. Dropped uq_favorite UNIQUE constraint';
    RAISE NOTICE '  2. Created partial unique index idx_favorite_tutors_unique_active';
    RAISE NOTICE '     (enforces uniqueness only for active rows)';
    RAISE NOTICE '  3. Added idx_favorite_tutors_tutor index on tutor_profile_id';
    RAISE NOTICE '';
    RAISE NOTICE '  Students can now re-favorite tutors after unfavoriting.';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
END $$;
