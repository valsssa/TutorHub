-- Migration: Add IANA timezone validation function and constraint
-- This ensures all timezone values stored are valid IANA timezone identifiers

-- Create a function to validate timezone format (basic validation)
-- Note: Full IANA validation would require a list of all valid timezones,
-- which is better handled at the application layer. This provides basic format checking.
CREATE OR REPLACE FUNCTION is_valid_timezone_format(tz TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check for valid timezone format patterns:
    -- 1. "UTC" or simple timezone like "GMT"
    -- 2. "Continent/City" format (e.g., "America/New_York", "Europe/London")
    -- 3. "Continent/Region/City" format (e.g., "America/Indiana/Indianapolis")

    IF tz IS NULL OR tz = '' THEN
        RETURN FALSE;
    END IF;

    -- Allow UTC and common abbreviations
    IF tz IN ('UTC', 'GMT') THEN
        RETURN TRUE;
    END IF;

    -- Check for standard IANA format: Continent/City or Continent/Region/City
    -- Must start with capital letter, contain at least one slash
    IF tz ~ '^[A-Z][a-zA-Z]+/[A-Z][a-zA-Z_]+(/[A-Z][a-zA-Z_]+)?$' THEN
        RETURN TRUE;
    END IF;

    -- Also allow Etc/... timezones and Pacific/... etc
    IF tz ~ '^(Etc|Pacific|Atlantic|Indian|Arctic|Antarctica)/[A-Za-z0-9_+-]+$' THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add check constraint to users table
-- First check if constraint exists to make migration idempotent
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_timezone_format_check'
        AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
        ADD CONSTRAINT users_timezone_format_check
        CHECK (timezone IS NULL OR is_valid_timezone_format(timezone));
    END IF;
END $$;

-- Add check constraint to user_profiles table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_profiles_timezone_format_check'
        AND conrelid = 'user_profiles'::regclass
    ) THEN
        ALTER TABLE user_profiles
        ADD CONSTRAINT user_profiles_timezone_format_check
        CHECK (timezone IS NULL OR is_valid_timezone_format(timezone));
    END IF;
END $$;

-- Add check constraint to tutor_profiles table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tutor_profiles_timezone_format_check'
        AND conrelid = 'tutor_profiles'::regclass
    ) THEN
        ALTER TABLE tutor_profiles
        ADD CONSTRAINT tutor_profiles_timezone_format_check
        CHECK (timezone IS NULL OR is_valid_timezone_format(timezone));
    END IF;
END $$;

-- Add check constraint to bookings table (for student_tz and tutor_tz)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_student_tz_format_check'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_student_tz_format_check
        CHECK (student_tz IS NULL OR is_valid_timezone_format(student_tz));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_tutor_tz_format_check'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_tutor_tz_format_check
        CHECK (tutor_tz IS NULL OR is_valid_timezone_format(tutor_tz));
    END IF;
END $$;

-- Update any NULL or empty timezones to 'UTC' (data cleanup)
UPDATE users SET timezone = 'UTC' WHERE timezone IS NULL OR timezone = '';
UPDATE user_profiles SET timezone = 'UTC' WHERE timezone IS NULL OR timezone = '';
UPDATE tutor_profiles SET timezone = 'UTC' WHERE timezone IS NULL OR timezone = '';
UPDATE bookings SET student_tz = 'UTC' WHERE student_tz IS NULL OR student_tz = '';
UPDATE bookings SET tutor_tz = 'UTC' WHERE tutor_tz IS NULL OR tutor_tz = '';

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 026_timezone_validation completed successfully';
END $$;
