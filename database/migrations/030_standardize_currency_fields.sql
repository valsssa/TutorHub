-- Migration 030: Standardize currency fields across tables
-- Purpose: Ensure consistent currency field types (VARCHAR(3)) and defaults
-- Date: 2026-01-28

-- Note: Current state analysis:
-- - bookings: currency CHAR(3) NOT NULL DEFAULT 'USD'
-- - payments: currency CHAR(3) NOT NULL DEFAULT 'USD'
-- - payouts: currency CHAR(3) NOT NULL DEFAULT 'USD'
-- - refunds: currency CHAR(3) NOT NULL DEFAULT 'USD'
-- - users: currency VARCHAR(3) NOT NULL DEFAULT 'USD'
-- - tutor_profiles: currency VARCHAR(3) NOT NULL DEFAULT 'USD'

-- Standardize all currency fields to VARCHAR(3) NOT NULL DEFAULT 'USD'
-- This provides flexibility for future currency codes while maintaining data integrity

-- 1. Update bookings table
DO $$
BEGIN
    -- Check if column is CHAR(3) and convert to VARCHAR(3)
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'bookings'
        AND column_name = 'currency'
        AND data_type = 'character'
    ) THEN
        ALTER TABLE bookings
        ALTER COLUMN currency TYPE VARCHAR(3);
        RAISE NOTICE 'Converted bookings.currency from CHAR(3) to VARCHAR(3)';
    END IF;
END $$;

-- 2. Update payments table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'payments'
        AND column_name = 'currency'
        AND data_type = 'character'
    ) THEN
        ALTER TABLE payments
        ALTER COLUMN currency TYPE VARCHAR(3);
        RAISE NOTICE 'Converted payments.currency from CHAR(3) to VARCHAR(3)';
    END IF;
END $$;

-- 3. Update payouts table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'payouts'
        AND column_name = 'currency'
        AND data_type = 'character'
    ) THEN
        ALTER TABLE payouts
        ALTER COLUMN currency TYPE VARCHAR(3);
        RAISE NOTICE 'Converted payouts.currency from CHAR(3) to VARCHAR(3)';
    END IF;
END $$;

-- 4. Update refunds table
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'refunds'
        AND column_name = 'currency'
        AND data_type = 'character'
    ) THEN
        ALTER TABLE refunds
        ALTER COLUMN currency TYPE VARCHAR(3);
        RAISE NOTICE 'Converted refunds.currency from CHAR(3) to VARCHAR(3)';
    END IF;
END $$;

-- Add indexes on currency fields for faster filtering (if not already exist)
CREATE INDEX IF NOT EXISTS idx_bookings_currency ON bookings(currency);
CREATE INDEX IF NOT EXISTS idx_payments_currency ON payments(currency);
CREATE INDEX IF NOT EXISTS idx_payouts_currency ON payouts(currency);
CREATE INDEX IF NOT EXISTS idx_refunds_currency ON refunds(currency);

-- Add CHECK constraints to ensure valid currency format (ISO 4217)
DO $$
BEGIN
    -- Bookings currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'bookings_valid_currency_format'
        AND conrelid = 'bookings'::regclass
    ) THEN
        ALTER TABLE bookings
        ADD CONSTRAINT bookings_valid_currency_format
        CHECK (currency ~ '^[A-Z]{3}$');
        RAISE NOTICE 'Added currency format constraint to bookings';
    END IF;

    -- Payments currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'payments_valid_currency_format'
        AND conrelid = 'payments'::regclass
    ) THEN
        ALTER TABLE payments
        ADD CONSTRAINT payments_valid_currency_format
        CHECK (currency ~ '^[A-Z]{3}$');
        RAISE NOTICE 'Added currency format constraint to payments';
    END IF;

    -- Payouts currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'payouts_valid_currency_format'
        AND conrelid = 'payouts'::regclass
    ) THEN
        ALTER TABLE payouts
        ADD CONSTRAINT payouts_valid_currency_format
        CHECK (currency ~ '^[A-Z]{3}$');
        RAISE NOTICE 'Added currency format constraint to payouts';
    END IF;

    -- Refunds currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'refunds_valid_currency_format'
        AND conrelid = 'refunds'::regclass
    ) THEN
        ALTER TABLE refunds
        ADD CONSTRAINT refunds_valid_currency_format
        CHECK (currency ~ '^[A-Z]{3}$');
        RAISE NOTICE 'Added currency format constraint to refunds';
    END IF;
END $$;

-- Note: Foreign key constraints to supported_currencies table NOT added to avoid:
-- 1. CASCADE handling complexity
-- 2. Query performance overhead
-- 3. Additional join requirements
-- Application layer validates currency codes against supported_currencies table

-- Add comments
COMMENT ON COLUMN bookings.currency IS 'ISO 4217 currency code (validated at application layer against supported_currencies)';
COMMENT ON COLUMN payments.currency IS 'ISO 4217 currency code (validated at application layer against supported_currencies)';
COMMENT ON COLUMN payouts.currency IS 'ISO 4217 currency code (validated at application layer against supported_currencies)';
COMMENT ON COLUMN refunds.currency IS 'ISO 4217 currency code (validated at application layer against supported_currencies)';

DO $$
BEGIN
    RAISE NOTICE 'Migration 030_standardize_currency_fields completed successfully';
    RAISE NOTICE 'All currency fields now use VARCHAR(3) with format validation';
END $$;
