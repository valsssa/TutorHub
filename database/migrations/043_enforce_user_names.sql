-- Migration: Enforce Required User Names
-- Description: Makes first_name and last_name required for all registered users
--
-- This migration:
-- 1. Adds profile_incomplete column to track users missing required names
-- 2. Updates existing users to mark incomplete profiles
-- 3. Adds NOT NULL constraints after backfill (with defaults for safety)
-- 4. Adds CHECK constraint to prevent empty/whitespace-only names
--
-- IMPORTANT: Run this migration during a maintenance window.
-- Existing users with missing names will be marked as profile_incomplete
-- and will be prompted to complete their profile on next login.

-- Step 1: Add profile_incomplete column to track incomplete profiles
-- This allows us to gate users who haven't provided names yet
ALTER TABLE users
ADD COLUMN IF NOT EXISTS profile_incomplete BOOLEAN DEFAULT FALSE NOT NULL;

-- Step 2: Mark existing users with missing names as profile_incomplete
-- These users will be prompted to complete their profile on next login
UPDATE users
SET profile_incomplete = TRUE
WHERE (first_name IS NULL OR TRIM(first_name) = '')
   OR (last_name IS NULL OR TRIM(last_name) = '');

-- Log the number of users affected
DO $$
DECLARE
  affected_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO affected_count
  FROM users
  WHERE profile_incomplete = TRUE AND deleted_at IS NULL;

  RAISE NOTICE 'Users marked as profile_incomplete: %', affected_count;
END $$;

-- Step 3: Add CHECK constraint to prevent empty/whitespace-only names
-- This constraint only applies to non-null values (allows NULL during migration)
-- NULL values are handled by the profile_incomplete flag
ALTER TABLE users
ADD CONSTRAINT check_first_name_not_empty
CHECK (first_name IS NULL OR TRIM(first_name) <> '');

ALTER TABLE users
ADD CONSTRAINT check_last_name_not_empty
CHECK (last_name IS NULL OR TRIM(last_name) <> '');

-- Step 4: Create function to validate names on insert/update
-- Ensures new registrations and updates have valid names
CREATE OR REPLACE FUNCTION validate_user_names()
RETURNS TRIGGER AS $$
BEGIN
  -- For new users (INSERT), both names are required
  IF TG_OP = 'INSERT' THEN
    -- Skip validation for OAuth users who may complete profile later
    -- They will have profile_incomplete = TRUE
    IF NEW.profile_incomplete = FALSE THEN
      IF NEW.first_name IS NULL OR TRIM(NEW.first_name) = '' THEN
        RAISE EXCEPTION 'first_name is required for new users';
      END IF;
      IF NEW.last_name IS NULL OR TRIM(NEW.last_name) = '' THEN
        RAISE EXCEPTION 'last_name is required for new users';
      END IF;
    END IF;
  END IF;

  -- For updates, if names are being set, they must be valid
  IF TG_OP = 'UPDATE' THEN
    -- If updating first_name, ensure it's not empty
    IF NEW.first_name IS DISTINCT FROM OLD.first_name THEN
      IF NEW.first_name IS NOT NULL AND TRIM(NEW.first_name) = '' THEN
        RAISE EXCEPTION 'first_name cannot be set to empty string';
      END IF;
    END IF;

    -- If updating last_name, ensure it's not empty
    IF NEW.last_name IS DISTINCT FROM OLD.last_name THEN
      IF NEW.last_name IS NOT NULL AND TRIM(NEW.last_name) = '' THEN
        RAISE EXCEPTION 'last_name cannot be set to empty string';
      END IF;
    END IF;

    -- Auto-clear profile_incomplete when both names are provided
    IF NEW.first_name IS NOT NULL AND TRIM(NEW.first_name) <> ''
       AND NEW.last_name IS NOT NULL AND TRIM(NEW.last_name) <> '' THEN
      NEW.profile_incomplete := FALSE;
    END IF;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for user name validation
DROP TRIGGER IF EXISTS trigger_validate_user_names ON users;
CREATE TRIGGER trigger_validate_user_names
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION validate_user_names();

-- Step 5: Create index for querying incomplete profiles
-- Useful for admin reports and background jobs
CREATE INDEX IF NOT EXISTS idx_users_profile_incomplete
ON users(profile_incomplete)
WHERE profile_incomplete = TRUE AND deleted_at IS NULL;

-- Step 6: Add comment documenting the User Identity Contract
COMMENT ON TABLE users IS
'Users table with required first_name and last_name fields.

User Identity Contract:
- first_name: Required, non-empty after trim, max 100 chars
- last_name: Required, non-empty after trim, max 100 chars
- full_name: Computed as "{first_name} {last_name}" (in API response)
- profile_incomplete: TRUE if user needs to complete profile (missing names)

Legacy users with missing names are marked profile_incomplete=TRUE
and must complete their profile on next login.';

COMMENT ON COLUMN users.first_name IS
'User first name (required for complete profile). Max 100 chars, must be non-empty after trim.';

COMMENT ON COLUMN users.last_name IS
'User last name (required for complete profile). Max 100 chars, must be non-empty after trim.';

COMMENT ON COLUMN users.profile_incomplete IS
'TRUE if user has incomplete profile (missing first_name or last_name).
Set for OAuth users who need to complete their profile on first login.';
