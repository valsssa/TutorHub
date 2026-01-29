-- Migration: Add timezone column to tutor_availabilities for DST-safe time handling
--
-- Problem: TutorAvailability stores naive Time objects without timezone info.
-- When DST changes, the UTC offset shifts but stored times don't adjust,
-- causing availability to shift by 1 hour unexpectedly.
--
-- Solution: Store the timezone in which availability times are expressed.
-- When generating slots, convert times using the stored timezone for proper DST handling.

-- Add timezone column with UTC default for backward compatibility
ALTER TABLE tutor_availabilities
ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC';

-- Add comment explaining the column
COMMENT ON COLUMN tutor_availabilities.timezone IS
    'IANA timezone identifier (e.g., America/New_York) in which start_time/end_time are expressed. Used for proper DST handling when converting to UTC.';

-- Create index for timezone column (useful for filtering by timezone)
CREATE INDEX IF NOT EXISTS idx_tutor_availability_timezone ON tutor_availabilities(timezone);

-- Update existing records to use tutor profile timezone where available
-- This is a one-time data migration to populate timezone from tutor's user profile
UPDATE tutor_availabilities ta
SET timezone = COALESCE(
    (SELECT up.timezone
     FROM tutor_profiles tp
     JOIN user_profiles up ON tp.user_id = up.user_id
     WHERE tp.id = ta.tutor_profile_id
     AND up.timezone IS NOT NULL),
    'UTC'
)
WHERE ta.timezone = 'UTC';
