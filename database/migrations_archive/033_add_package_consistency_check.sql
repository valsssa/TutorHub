-- Migration 033: Add package session consistency constraint
-- Purpose: Ensure sessions_remaining is always computed correctly from sessions_purchased - sessions_used
-- Date: 2026-01-28

-- ============================================================================
-- FIX INCONSISTENT DATA BEFORE ADDING CONSTRAINT
-- ============================================================================

-- First, fix any existing inconsistencies in student_packages
UPDATE student_packages
SET sessions_remaining = sessions_purchased - sessions_used
WHERE sessions_remaining != sessions_purchased - sessions_used;

-- Log how many records were fixed
DO $$
DECLARE
    fixed_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO fixed_count
    FROM student_packages
    WHERE sessions_remaining != sessions_purchased - sessions_used;

    IF fixed_count > 0 THEN
        RAISE WARNING 'Fixed % inconsistent package records before adding constraint', fixed_count;
    ELSE
        RAISE NOTICE 'All package records are consistent - no fixes needed';
    END IF;
END $$;

-- ============================================================================
-- ADD CONSISTENCY CONSTRAINT
-- ============================================================================

-- Add constraint to ensure sessions_remaining = sessions_purchased - sessions_used
-- This prevents data corruption and ensures package accounting is always correct
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_sessions_consistency'
        AND conrelid = 'student_packages'::regclass
    ) THEN
        ALTER TABLE student_packages
        ADD CONSTRAINT chk_sessions_consistency
        CHECK (sessions_remaining = sessions_purchased - sessions_used);
        RAISE NOTICE 'Added sessions consistency constraint to student_packages';
    ELSE
        RAISE NOTICE 'Sessions consistency constraint already exists';
    END IF;
END $$;

COMMENT ON CONSTRAINT chk_sessions_consistency ON student_packages IS
'Ensures sessions_remaining always equals sessions_purchased minus sessions_used (denormalized for query performance)';

-- ============================================================================
-- VALIDATION QUERIES
-- ============================================================================

-- Verify all packages are now consistent
DO $$
DECLARE
    total_packages INTEGER;
    inconsistent_packages INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_packages FROM student_packages;

    SELECT COUNT(*) INTO inconsistent_packages
    FROM student_packages
    WHERE sessions_remaining != sessions_purchased - sessions_used;

    RAISE NOTICE 'Migration 033_add_package_consistency_check completed successfully';
    RAISE NOTICE 'Total packages: %', total_packages;
    RAISE NOTICE 'Inconsistent packages: %', inconsistent_packages;

    IF inconsistent_packages > 0 THEN
        RAISE WARNING 'WARNING: % packages still inconsistent - constraint will prevent new writes', inconsistent_packages;
    ELSE
        RAISE NOTICE 'All packages are consistent - constraint active';
    END IF;
END $$;

-- ============================================================================
-- APPLICATION CODE REQUIREMENTS
-- ============================================================================

-- When updating package sessions, application code must update both fields:
--
-- Example (when consuming a session):
--   package.sessions_used += 1
--   package.sessions_remaining = package.sessions_purchased - package.sessions_used
--
-- Example (when purchasing additional sessions):
--   package.sessions_purchased += additional_sessions
--   package.sessions_remaining = package.sessions_purchased - package.sessions_used
--
-- The constraint will REJECT any update that violates the consistency rule.
