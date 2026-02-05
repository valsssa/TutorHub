-- Migration 028: Remove timezone database logic
-- Purpose: Remove PL/pgSQL function and constraints that violate "No Logic in Database" principle
-- Date: 2026-01-28
-- Architecture Compliance: All business logic must reside in application layer (backend/core/timezone.py)

-- Drop CHECK constraints added by migration 026
DO $$
BEGIN
    -- Drop users timezone constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_timezone_format_check'
        AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users DROP CONSTRAINT users_timezone_format_check;
        RAISE NOTICE 'Dropped constraint: users_timezone_format_check';
    END IF;

    -- Drop user_profiles timezone constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'user_profiles_timezone_format_check'
        AND conrelid = 'user_profiles'::regclass
    ) THEN
        ALTER TABLE user_profiles DROP CONSTRAINT user_profiles_timezone_format_check;
        RAISE NOTICE 'Dropped constraint: user_profiles_timezone_format_check';
    END IF;

    -- Drop tutor_profiles timezone constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'tutor_profiles_timezone_format_check'
        AND conrelid = 'tutor_profiles'::regclass
    ) THEN
        ALTER TABLE tutor_profiles DROP CONSTRAINT tutor_profiles_timezone_format_check;
        RAISE NOTICE 'Dropped constraint: tutor_profiles_timezone_format_check';
    END IF;

    -- Drop bookings student_tz constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_student_tz_format_check'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings DROP CONSTRAINT bookings_student_tz_format_check;
        RAISE NOTICE 'Dropped constraint: bookings_student_tz_format_check';
    END IF;

    -- Drop bookings tutor_tz constraint
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_tutor_tz_format_check'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings DROP CONSTRAINT bookings_tutor_tz_format_check;
        RAISE NOTICE 'Dropped constraint: bookings_tutor_tz_format_check';
    END IF;
END $$;

-- Drop the timezone validation function
DROP FUNCTION IF EXISTS is_valid_timezone_format(TEXT);

-- Add comment explaining the architecture decision
COMMENT ON COLUMN users.timezone IS 'IANA timezone identifier (validated at application layer in backend/core/timezone.py)';
COMMENT ON COLUMN user_profiles.timezone IS 'IANA timezone identifier (validated at application layer in backend/core/timezone.py)';
COMMENT ON COLUMN tutor_profiles.timezone IS 'IANA timezone identifier (validated at application layer in backend/core/timezone.py)';
COMMENT ON COLUMN bookings.student_tz IS 'IANA timezone identifier (validated at application layer in backend/core/timezone.py)';
COMMENT ON COLUMN bookings.tutor_tz IS 'IANA timezone identifier (validated at application layer in backend/core/timezone.py)';

-- Note: Data cleanup from migration 026 (UTC defaults) is preserved
-- Note: Timezone validation continues via backend/core/timezone.py:is_valid_timezone()
-- Note: Pydantic validators in backend/schemas.py provide schema-level validation

DO $$
BEGIN
    RAISE NOTICE 'Migration 028_remove_timezone_db_logic completed successfully';
    RAISE NOTICE 'Timezone validation now handled by application layer only';
END $$;
