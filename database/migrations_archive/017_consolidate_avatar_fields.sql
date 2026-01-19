-- ============================================================================
-- Migration 017: Consolidate Avatar Fields
-- Purpose: Remove redundant avatar fields and use single avatar_key from users table
-- GDPR/CCPA Compliance: Single source of truth for profile photos
-- ============================================================================

-- Migration notes:
-- 1. Keep only users.avatar_key as the single source of profile photo
-- 2. Remove user_profiles.avatar_url (redundant)
-- 3. Remove tutor_profiles.profile_photo_url (redundant)
-- 4. Migrate any existing data to users.avatar_key before dropping columns

BEGIN;

-- Step 1: Migrate existing avatar_url from user_profiles to users.avatar_key
-- Only migrate if user doesn't already have an avatar_key
UPDATE users u
SET avatar_key = up.avatar_url
FROM user_profiles up
WHERE u.id = up.user_id
  AND up.avatar_url IS NOT NULL
  AND up.avatar_url != ''
  AND u.avatar_key IS NULL;

-- Step 2: Migrate existing profile_photo_url from tutor_profiles to users.avatar_key
-- Only migrate if user doesn't already have an avatar_key
UPDATE users u
SET avatar_key = tp.profile_photo_url
FROM tutor_profiles tp
WHERE u.id = tp.user_id
  AND tp.profile_photo_url IS NOT NULL
  AND tp.profile_photo_url != ''
  AND u.avatar_key IS NULL;

-- Step 3: Drop views that depend on the columns we're removing
DROP VIEW IF EXISTS active_tutor_profiles CASCADE;
DROP VIEW IF EXISTS active_users CASCADE;
DROP VIEW IF EXISTS active_bookings CASCADE;

-- Step 4: Drop redundant columns
ALTER TABLE user_profiles DROP COLUMN IF EXISTS avatar_url;
ALTER TABLE tutor_profiles DROP COLUMN IF EXISTS profile_photo_url;

-- Step 5: Recreate views
CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_profiles AS
SELECT * FROM tutor_profiles WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_bookings AS
SELECT * FROM bookings WHERE deleted_at IS NULL;

-- Log migration
DO $$
BEGIN
    RAISE NOTICE '✓ Migration 017: Avatar fields consolidated successfully';
    RAISE NOTICE '  - Removed: user_profiles.avatar_url';
    RAISE NOTICE '  - Removed: tutor_profiles.profile_photo_url';
    RAISE NOTICE '  - Single source: users.avatar_key';
END $$;

COMMIT;
