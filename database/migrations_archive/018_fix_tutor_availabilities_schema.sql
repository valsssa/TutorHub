-- ============================================================================
-- Migration 018: Fix tutor_availabilities schema consistency
-- ============================================================================
-- 
-- This migration ensures tutor_availabilities table matches the correct schema:
-- - Uses tutor_profile_id (not tutor_id)
-- - Uses day_of_week (not weekday)  
-- - Uses start_time/end_time TIME fields (not start_minute/end_minute integers)
-- - Includes is_recurring boolean field
--
-- Safe to run multiple times (idempotent)
-- ============================================================================

BEGIN;

-- Check if table exists and needs migration
DO $$
DECLARE
    has_tutor_id BOOLEAN;
    has_tutor_profile_id BOOLEAN;
    has_weekday BOOLEAN;
    has_day_of_week BOOLEAN;
    has_start_minute BOOLEAN;
    has_start_time BOOLEAN;
BEGIN
    -- Check which columns exist
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'tutor_id'
    ) INTO has_tutor_id;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'tutor_profile_id'
    ) INTO has_tutor_profile_id;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'weekday'
    ) INTO has_weekday;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'day_of_week'
    ) INTO has_day_of_week;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'start_minute'
    ) INTO has_start_minute;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tutor_availabilities' AND column_name = 'start_time'
    ) INTO has_start_time;

    -- Log current state
    RAISE NOTICE 'Current schema state:';
    RAISE NOTICE '  has_tutor_id: %', has_tutor_id;
    RAISE NOTICE '  has_tutor_profile_id: %', has_tutor_profile_id;
    RAISE NOTICE '  has_weekday: %', has_weekday;
    RAISE NOTICE '  has_day_of_week: %', has_day_of_week;
    RAISE NOTICE '  has_start_minute: %', has_start_minute;
    RAISE NOTICE '  has_start_time: %', has_start_time;

    -- If table has old schema (tutor_id), migrate it
    IF has_tutor_id AND NOT has_tutor_profile_id THEN
        RAISE NOTICE 'Migrating from old schema (tutor_id) to new schema (tutor_profile_id)';
        
        -- Create temp table with new schema
        CREATE TEMP TABLE tutor_availabilities_new (
            id SERIAL PRIMARY KEY,
            tutor_profile_id INTEGER NOT NULL,
            day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            is_recurring BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
        
        -- Migrate data: convert user_id to tutor_profile_id
        INSERT INTO tutor_availabilities_new (
            tutor_profile_id, 
            day_of_week, 
            start_time, 
            end_time, 
            is_recurring,
            created_at
        )
        SELECT 
            tp.id as tutor_profile_id,
            ta.weekday as day_of_week,
            MAKE_TIME(ta.start_minute / 60, ta.start_minute % 60, 0) as start_time,
            MAKE_TIME(ta.end_minute / 60, ta.end_minute % 60, 0) as end_time,
            TRUE as is_recurring,
            ta.created_at
        FROM tutor_availabilities ta
        JOIN tutor_profiles tp ON tp.user_id = ta.tutor_id;
        
        -- Drop old table and rename new one
        DROP TABLE tutor_availabilities CASCADE;
        ALTER TABLE tutor_availabilities_new RENAME TO tutor_availabilities;
        
        -- Recreate foreign key constraint
        ALTER TABLE tutor_availabilities 
            ADD CONSTRAINT tutor_availabilities_tutor_profile_id_fkey 
            FOREIGN KEY (tutor_profile_id) 
            REFERENCES tutor_profiles(id) ON DELETE CASCADE;
        
        -- Recreate indexes
        CREATE INDEX idx_tutor_availability_profile_day 
            ON tutor_availabilities(tutor_profile_id, day_of_week);
        
        -- Recreate unique constraint
        ALTER TABLE tutor_availabilities 
            ADD CONSTRAINT uq_tutor_availability_slot 
            UNIQUE (tutor_profile_id, day_of_week, start_time, end_time);
        
        RAISE NOTICE 'Migration completed successfully';
        
    ELSIF has_tutor_profile_id AND has_day_of_week AND has_start_time THEN
        RAISE NOTICE 'Schema is already correct, no migration needed';
    ELSE
        RAISE NOTICE 'Unexpected schema state - manual intervention may be required';
    END IF;
    
END $$;

COMMIT;

-- Verify final schema
DO $$
BEGIN
    RAISE NOTICE 'Final schema verification:';
    RAISE NOTICE 'Run: \d tutor_availabilities to verify structure';
END $$;
