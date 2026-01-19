-- ============================================================================
-- Phase 3 Migration: struct.txt Compliance
-- Adds missing fields for tutor profile requirements
-- Date: 2025-10-10
-- ============================================================================

-- ============================================================================
-- 1. Update user_profiles for phone validation and country of birth
-- ============================================================================

-- Add country_of_birth (ISO 3166-1 alpha-2)
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS country_of_birth VARCHAR(2),
ADD COLUMN IF NOT EXISTS phone_country_code VARCHAR(5),
ADD COLUMN IF NOT EXISTS date_of_birth DATE,
ADD COLUMN IF NOT EXISTS age_confirmed BOOLEAN DEFAULT FALSE NOT NULL;

-- Add constraints for country code (must be 2-letter ISO code)
ALTER TABLE user_profiles
ADD CONSTRAINT chk_country_of_birth_format CHECK (
    country_of_birth IS NULL OR
    (country_of_birth ~ '^[A-Z]{2}$')
);

-- Add constraint for phone country code (E.164 format: +1 to +999...)
ALTER TABLE user_profiles
ADD CONSTRAINT chk_phone_country_code_format CHECK (
    phone_country_code IS NULL OR
    (phone_country_code ~ '^\+[0-9]{1,3}$')
);

-- Add constraint for age (must be 18+)
ALTER TABLE user_profiles
ADD CONSTRAINT chk_age_18_plus CHECK (
    date_of_birth IS NULL OR
    (date_of_birth <= CURRENT_DATE - INTERVAL '18 years')
);

-- Create index for country lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country_of_birth);

-- ============================================================================
-- 2. Update tutor_subjects for CEFR proficiency levels
-- ============================================================================

-- Drop old proficiency constraint
ALTER TABLE tutor_subjects DROP CONSTRAINT IF EXISTS valid_proficiency;

-- Add new CEFR-compliant proficiency constraint
ALTER TABLE tutor_subjects
ADD CONSTRAINT valid_proficiency CHECK (
    proficiency_level IN ('Native', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1')
);

-- Update default to CEFR standard
ALTER TABLE tutor_subjects
ALTER COLUMN proficiency_level SET DEFAULT 'B2';

-- ============================================================================
-- 3. Add timezone field to tutor_profiles
-- ============================================================================

ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) DEFAULT 'UTC';

CREATE INDEX IF NOT EXISTS idx_tutor_profiles_timezone ON tutor_profiles(timezone);

-- ============================================================================
-- 4. Update phone field length for E.164 format
-- ============================================================================

-- E.164 format: + followed by up to 15 digits
ALTER TABLE user_profiles
ALTER COLUMN phone TYPE VARCHAR(20);

-- ============================================================================
-- 5. Add data migration for existing proficiency levels
-- ============================================================================

-- Map old proficiency levels to CEFR equivalents
UPDATE tutor_subjects
SET proficiency_level = CASE
    WHEN proficiency_level = 'beginner' THEN 'A2'
    WHEN proficiency_level = 'intermediate' THEN 'B2'
    WHEN proficiency_level = 'advanced' THEN 'C1'
    WHEN proficiency_level = 'expert' THEN 'Native'
    ELSE 'B2'  -- Default fallback
END
WHERE proficiency_level NOT IN ('Native', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1');

-- ============================================================================
-- 6. Add comments for documentation
-- ============================================================================

COMMENT ON COLUMN user_profiles.country_of_birth IS 'ISO 3166-1 alpha-2 country code (e.g., US, GB, FR)';
COMMENT ON COLUMN user_profiles.phone_country_code IS 'ITU E.164 phone country code (e.g., +1, +44, +33)';
COMMENT ON COLUMN user_profiles.date_of_birth IS 'User date of birth (must be 18+)';
COMMENT ON COLUMN user_profiles.age_confirmed IS 'User has confirmed they are 18 years or older';
COMMENT ON COLUMN tutor_profiles.timezone IS 'Tutor timezone (IANA timezone identifier)';
COMMENT ON COLUMN tutor_subjects.proficiency_level IS 'CEFR proficiency level: Native, C2 (Mastery), C1 (Advanced), B2 (Upper Intermediate), B1 (Intermediate), A2 (Elementary), A1 (Beginner)';

-- ============================================================================
-- Migration Complete
-- ============================================================================
