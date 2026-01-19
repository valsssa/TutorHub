-- Migration: Add onboarding fields to user_profiles
-- Phase 3: Multi-step tutor onboarding support
-- Created: 2025-01-11

-- Add new columns to user_profiles table
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS country_of_birth VARCHAR(2),  -- ISO 3166-1 alpha-2 code
ADD COLUMN IF NOT EXISTS phone_country_code VARCHAR(5),  -- E.164 format (+1 to +999)
ADD COLUMN IF NOT EXISTS date_of_birth DATE,  -- For age verification
ADD COLUMN IF NOT EXISTS age_confirmed BOOLEAN DEFAULT FALSE NOT NULL;  -- 18+ confirmation checkbox

-- Add comments for documentation
COMMENT ON COLUMN user_profiles.country_of_birth IS 'ISO 3166-1 alpha-2 country code (e.g., US, GB, AL)';
COMMENT ON COLUMN user_profiles.phone_country_code IS 'E.164 phone country code (e.g., +1, +44, +355)';
COMMENT ON COLUMN user_profiles.date_of_birth IS 'User date of birth for age verification';
COMMENT ON COLUMN user_profiles.age_confirmed IS 'User confirmed they are 18+ years old';

-- Create index for country-based queries
CREATE INDEX IF NOT EXISTS idx_user_profiles_country ON user_profiles(country_of_birth) WHERE country_of_birth IS NOT NULL;
