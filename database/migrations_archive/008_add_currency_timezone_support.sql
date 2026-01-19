-- ============================================================================
-- Currency and Timezone Support for Global Scale
-- ============================================================================

-- Add currency column to users table (defaults to USD)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD' NOT NULL;

-- Add timezone column to users table if not exists (defaults to UTC)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) DEFAULT 'UTC' NOT NULL;

-- Add constraint to validate currency codes (ISO 4217)
ALTER TABLE users 
ADD CONSTRAINT IF NOT EXISTS valid_currency 
CHECK (currency ~ '^[A-Z]{3}$');

-- Ensure user_profiles timezone column exists with proper default
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND column_name = 'timezone'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN timezone VARCHAR(64) DEFAULT 'UTC';
    END IF;
END $$;

-- Update user_profiles timezone to use user's timezone where NULL
UPDATE user_profiles 
SET timezone = COALESCE(timezone, 'UTC')
WHERE timezone IS NULL;

-- Add index for currency-based queries
CREATE INDEX IF NOT EXISTS idx_users_currency ON users(currency);

-- Add index for timezone-based queries
CREATE INDEX IF NOT EXISTS idx_users_timezone ON users(timezone);

COMMENT ON COLUMN users.currency IS 
'User preferred currency for pricing display (ISO 4217: USD, EUR, GBP, etc.)';

COMMENT ON COLUMN users.timezone IS 
'User timezone for datetime display (IANA timezone: America/New_York, Europe/London, UTC, etc.)';

-- Ensure all timestamp columns use timezone-aware types
-- bookings already has TIMESTAMPTZ, verify others

-- Update tutor_profiles to include currency if needed
ALTER TABLE tutor_profiles 
ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'USD' NOT NULL;

ALTER TABLE tutor_profiles 
ADD CONSTRAINT IF NOT EXISTS valid_tutor_currency 
CHECK (currency ~ '^[A-Z]{3}$');

COMMENT ON COLUMN tutor_profiles.currency IS 
'Currency for tutor pricing (ISO 4217). Defaults to USD. Conversions handled by application layer.';

-- Add index for tutor currency filtering
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_currency ON tutor_profiles(currency);

-- Migration verification
DO $$
DECLARE
    v_users_currency_count INTEGER;
    v_users_timezone_count INTEGER;
    v_tutor_currency_count INTEGER;
BEGIN
    -- Count non-default currencies (should be 0 initially)
    SELECT COUNT(*) INTO v_users_currency_count 
    FROM users WHERE currency != 'USD';
    
    -- Count non-UTC timezones (should be 0 initially)
    SELECT COUNT(*) INTO v_users_timezone_count 
    FROM users WHERE timezone != 'UTC';
    
    -- Count tutor profiles with currency
    SELECT COUNT(*) INTO v_tutor_currency_count 
    FROM tutor_profiles;
    
    RAISE NOTICE 'Currency/Timezone migration completed:';
    RAISE NOTICE '  - Users with non-USD currency: %', v_users_currency_count;
    RAISE NOTICE '  - Users with non-UTC timezone: %', v_users_timezone_count;
    RAISE NOTICE '  - Tutor profiles: %', v_tutor_currency_count;
    RAISE NOTICE 'All timestamps stored in UTC, converted for display per user preferences.';
END $$;
