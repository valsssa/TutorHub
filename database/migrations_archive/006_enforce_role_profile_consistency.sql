-- ============================================================================
-- Migration: 006_enforce_role_profile_consistency.sql
-- Purpose: Enforce role-profile consistency at database level
-- 
-- This migration adds PostgreSQL triggers to automatically:
-- 1. Create tutor_profiles when user.role changes to 'tutor'
-- 2. Archive tutor_profiles when user.role changes from 'tutor'
-- 3. Backfill existing inconsistencies
-- 
-- Author: System
-- Date: 2025-01-14
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create trigger function for role-profile consistency
-- ============================================================================

CREATE OR REPLACE FUNCTION enforce_role_profile_consistency()
RETURNS TRIGGER AS $$
DECLARE
    v_profile_exists BOOLEAN;
BEGIN
    -- Case 1: Role changed TO 'tutor'
    IF NEW.role = 'tutor' AND (OLD IS NULL OR OLD.role != 'tutor') THEN
        -- Check if profile already exists
        SELECT EXISTS(
            SELECT 1 FROM tutor_profiles WHERE user_id = NEW.id
        ) INTO v_profile_exists;
        
        IF v_profile_exists THEN
            -- Reactivate archived profile
            UPDATE tutor_profiles 
            SET profile_status = 'incomplete',
                is_approved = FALSE,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = NEW.id 
            AND profile_status = 'archived';
            
            RAISE NOTICE 'Reactivated tutor_profiles for user %', NEW.id;
        ELSE
            -- Create new tutor profile
            INSERT INTO tutor_profiles (
                user_id,
                title,
                headline,
                bio,
                description,
                hourly_rate,
                experience_years,
                languages,
                profile_status,
                is_approved,
                created_at,
                updated_at
            ) VALUES (
                NEW.id,
                '',
                NULL,
                NULL,
                NULL,
                1.00,
                0,
                ARRAY[]::TEXT[],
                'incomplete',
                FALSE,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
            
            RAISE NOTICE 'Created tutor_profiles for user %', NEW.id;
        END IF;
    END IF;
    
    -- Case 2: Role changed FROM 'tutor' to something else
    IF OLD IS NOT NULL AND OLD.role = 'tutor' AND NEW.role != 'tutor' THEN
        -- Archive tutor profile (soft delete)
        -- Preserves historical data for bookings and reviews
        UPDATE tutor_profiles 
        SET is_approved = FALSE,
            profile_status = 'archived',
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = NEW.id
        AND profile_status != 'archived';
        
        RAISE NOTICE 'Archived tutor_profiles for user % (role changed from tutor to %)', NEW.id, NEW.role;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Step 2: Attach trigger to users table
-- ============================================================================

-- Drop existing trigger if it exists (idempotent)
DROP TRIGGER IF EXISTS trg_role_profile_consistency ON users;

-- Create trigger that fires AFTER INSERT OR UPDATE
CREATE TRIGGER trg_role_profile_consistency
    AFTER INSERT OR UPDATE OF role ON users
    FOR EACH ROW
    EXECUTE FUNCTION enforce_role_profile_consistency();

-- ============================================================================
-- Step 3: Add helper function for consistency checks
-- ============================================================================

CREATE OR REPLACE FUNCTION check_role_profile_consistency()
RETURNS TABLE(
    check_name TEXT,
    issue_count INTEGER,
    user_ids INTEGER[]
) AS $$
BEGIN
    -- Check 1: Tutors without profiles
    RETURN QUERY
    SELECT 
        'tutors_without_profiles'::TEXT,
        COUNT(*)::INTEGER,
        ARRAY_AGG(id)::INTEGER[]
    FROM users
    WHERE role = 'tutor'
    AND NOT EXISTS (
        SELECT 1 FROM tutor_profiles WHERE user_id = users.id
    );
    
    -- Check 2: Active profiles for non-tutors
    RETURN QUERY
    SELECT 
        'profiles_without_tutor_role'::TEXT,
        COUNT(*)::INTEGER,
        ARRAY_AGG(u.id)::INTEGER[]
    FROM users u
    INNER JOIN tutor_profiles tp ON u.id = tp.user_id
    WHERE u.role != 'tutor'
    AND tp.profile_status != 'archived';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Step 4: Backfill existing data (one-time operation)
-- ============================================================================

DO $$
DECLARE
    v_user_record RECORD;
    v_tutors_created INTEGER := 0;
    v_profiles_archived INTEGER := 0;
BEGIN
    RAISE NOTICE 'Starting backfill of role-profile consistency...';
    
    -- Create missing profiles for existing tutors
    FOR v_user_record IN 
        SELECT id, email FROM users 
        WHERE role = 'tutor' 
        AND NOT EXISTS (
            SELECT 1 FROM tutor_profiles WHERE user_id = users.id
        )
    LOOP
        INSERT INTO tutor_profiles (
            user_id,
            title,
            headline,
            bio,
            description,
            hourly_rate,
            experience_years,
            languages,
            profile_status,
            is_approved,
            created_at,
            updated_at
        ) VALUES (
            v_user_record.id,
            '',
            NULL,
            NULL,
            NULL,
            1.00,
            0,
            ARRAY[]::TEXT[],
            'incomplete',
            FALSE,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        
        v_tutors_created := v_tutors_created + 1;
        RAISE NOTICE 'Backfilled tutor_profiles for user % (email: %)', v_user_record.id, v_user_record.email;
    END LOOP;
    
    -- Archive profiles for non-tutors
    UPDATE tutor_profiles tp
    SET is_approved = FALSE,
        profile_status = 'archived',
        updated_at = CURRENT_TIMESTAMP
    FROM users u
    WHERE tp.user_id = u.id 
    AND u.role != 'tutor'
    AND tp.profile_status != 'archived';
    
    GET DIAGNOSTICS v_profiles_archived = ROW_COUNT;
    
    RAISE NOTICE 'Backfill completed: % profiles created, % profiles archived', 
        v_tutors_created, v_profiles_archived;
    
    -- Verify consistency
    IF EXISTS (
        SELECT 1 FROM check_role_profile_consistency() WHERE issue_count > 0
    ) THEN
        RAISE WARNING 'Consistency issues remain after backfill. Run check_role_profile_consistency() for details.';
    ELSE
        RAISE NOTICE 'Database is now fully consistent!';
    END IF;
END $$;

-- ============================================================================
-- Step 5: Create performance indexes
-- ============================================================================

-- Index for faster consistency checks
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_user_status 
ON tutor_profiles(user_id, profile_status, is_approved);

-- Index for archived profile queries
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_archived 
ON tutor_profiles(user_id) 
WHERE profile_status = 'archived';

-- ============================================================================
-- Step 6: Add comments for documentation
-- ============================================================================

COMMENT ON FUNCTION enforce_role_profile_consistency() IS 
'Trigger function that maintains consistency between users.role and tutor_profiles. 
Automatically creates profiles when role changes to tutor, and archives profiles 
when role changes from tutor. Preserves historical data for bookings and reviews.';

COMMENT ON FUNCTION check_role_profile_consistency() IS 
'Helper function to identify role-profile inconsistencies. 
Returns two rows: tutors_without_profiles and profiles_without_tutor_role.
Usage: SELECT * FROM check_role_profile_consistency();';

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Verify migration success
DO $$
DECLARE
    v_trigger_exists BOOLEAN;
    v_function_exists BOOLEAN;
BEGIN
    -- Check trigger exists
    SELECT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_role_profile_consistency'
    ) INTO v_trigger_exists;
    
    -- Check function exists
    SELECT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = 'enforce_role_profile_consistency'
    ) INTO v_function_exists;
    
    IF v_trigger_exists AND v_function_exists THEN
        RAISE NOTICE '✅ Migration 006 completed successfully!';
        RAISE NOTICE '   - Trigger: trg_role_profile_consistency';
        RAISE NOTICE '   - Function: enforce_role_profile_consistency()';
        RAISE NOTICE '   - Helper: check_role_profile_consistency()';
    ELSE
        RAISE EXCEPTION 'Migration verification failed!';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Check for consistency issues:
-- SELECT * FROM check_role_profile_consistency();

-- Test trigger:
-- UPDATE users SET role = 'tutor' WHERE id = 123;  -- Creates profile
-- UPDATE users SET role = 'student' WHERE id = 123;  -- Archives profile

-- View trigger definition:
-- \d+ users

-- View all triggers:
-- SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'users'::regclass;
