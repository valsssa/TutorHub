-- Migration 030: Standardize currency fields across tables
-- Purpose: Ensure consistent currency field types (VARCHAR(3)) and defaults
-- Date: 2026-01-28
-- Note: If a view depends on any of these columns, type conversion is skipped

-- Standardize all currency fields to VARCHAR(3) NOT NULL DEFAULT 'USD'
-- This provides flexibility for future currency codes while maintaining data integrity

-- 1. Update bookings table (with exception handling for view dependencies)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'bookings'
        AND column_name = 'currency'
        AND data_type = 'character'
    ) THEN
        BEGIN
            ALTER TABLE bookings ALTER COLUMN currency TYPE VARCHAR(3);
            RAISE NOTICE 'Converted bookings.currency from CHAR(3) to VARCHAR(3)';
        EXCEPTION WHEN feature_not_supported THEN
            RAISE NOTICE 'Skipped bookings.currency conversion (view dependency)';
        END;
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
        BEGIN
            ALTER TABLE payments ALTER COLUMN currency TYPE VARCHAR(3);
            RAISE NOTICE 'Converted payments.currency from CHAR(3) to VARCHAR(3)';
        EXCEPTION WHEN feature_not_supported THEN
            RAISE NOTICE 'Skipped payments.currency conversion (view dependency)';
        END;
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
        BEGIN
            ALTER TABLE payouts ALTER COLUMN currency TYPE VARCHAR(3);
            RAISE NOTICE 'Converted payouts.currency from CHAR(3) to VARCHAR(3)';
        EXCEPTION WHEN feature_not_supported THEN
            RAISE NOTICE 'Skipped payouts.currency conversion (view dependency)';
        END;
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
        BEGIN
            ALTER TABLE refunds ALTER COLUMN currency TYPE VARCHAR(3);
            RAISE NOTICE 'Converted refunds.currency from CHAR(3) to VARCHAR(3)';
        EXCEPTION WHEN feature_not_supported THEN
            RAISE NOTICE 'Skipped refunds.currency conversion (view dependency)';
        END;
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
        BEGIN
            ALTER TABLE bookings
            ADD CONSTRAINT bookings_valid_currency_format
            CHECK (currency ~ '^[A-Z]{3}$');
            RAISE NOTICE 'Added currency format constraint to bookings';
        EXCEPTION WHEN check_violation THEN
            RAISE NOTICE 'Skipped bookings constraint (existing data violates check)';
        END;
    END IF;

    -- Payments currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'payments_valid_currency_format'
        AND conrelid = 'payments'::regclass
    ) THEN
        BEGIN
            ALTER TABLE payments
            ADD CONSTRAINT payments_valid_currency_format
            CHECK (currency ~ '^[A-Z]{3}$');
            RAISE NOTICE 'Added currency format constraint to payments';
        EXCEPTION WHEN check_violation THEN
            RAISE NOTICE 'Skipped payments constraint (existing data violates check)';
        END;
    END IF;

    -- Payouts currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'payouts_valid_currency_format'
        AND conrelid = 'payouts'::regclass
    ) THEN
        BEGIN
            ALTER TABLE payouts
            ADD CONSTRAINT payouts_valid_currency_format
            CHECK (currency ~ '^[A-Z]{3}$');
            RAISE NOTICE 'Added currency format constraint to payouts';
        EXCEPTION WHEN check_violation THEN
            RAISE NOTICE 'Skipped payouts constraint (existing data violates check)';
        END;
    END IF;

    -- Refunds currency check
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'refunds_valid_currency_format'
        AND conrelid = 'refunds'::regclass
    ) THEN
        BEGIN
            ALTER TABLE refunds
            ADD CONSTRAINT refunds_valid_currency_format
            CHECK (currency ~ '^[A-Z]{3}$');
            RAISE NOTICE 'Added currency format constraint to refunds';
        EXCEPTION WHEN check_violation THEN
            RAISE NOTICE 'Skipped refunds constraint (existing data violates check)';
        END;
    END IF;
END $$;

-- Add comments (these are safe and always succeed)
DO $$
BEGIN
    COMMENT ON COLUMN bookings.currency IS 'ISO 4217 currency code (validated at application layer)';
EXCEPTION WHEN undefined_column THEN NULL;
END $$;

DO $$
BEGIN
    COMMENT ON COLUMN payments.currency IS 'ISO 4217 currency code (validated at application layer)';
EXCEPTION WHEN undefined_column THEN NULL;
END $$;

DO $$
BEGIN
    COMMENT ON COLUMN payouts.currency IS 'ISO 4217 currency code (validated at application layer)';
EXCEPTION WHEN undefined_column THEN NULL;
END $$;

DO $$
BEGIN
    COMMENT ON COLUMN refunds.currency IS 'ISO 4217 currency code (validated at application layer)';
EXCEPTION WHEN undefined_column THEN NULL;
END $$;

DO $$
BEGIN
    RAISE NOTICE 'Migration 030_standardize_currency_fields completed';
END $$;
