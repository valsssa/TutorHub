-- Migration: 051_fix_monetary_constraints.sql
-- Description: Add NOT NULL and CHECK constraints to monetary fields for data integrity
-- Author: Claude
-- Date: 2026-02-05
--
-- Issues Fixed:
-- 1. bookings.rate_cents - Can be NULL, needs NOT NULL + positive check
-- 2. bookings.currency - Has DEFAULT but can be NULL, needs NOT NULL
-- 3. bookings.platform_fee_cents - Can be negative, needs >= 0 check
-- 4. bookings.tutor_earnings_cents - Can be negative, needs >= 0 check
-- 5. wallet_transactions.reference_id - Allows NULL breaking idempotency

BEGIN;

-- =============================================================================
-- STEP 1: Fix existing NULL/invalid values BEFORE adding constraints
-- =============================================================================

-- Fix NULL rate_cents: Calculate from hourly_rate if missing
-- hourly_rate is in dollars, rate_cents should be in cents
UPDATE bookings
SET rate_cents = COALESCE(
    rate_cents,
    (hourly_rate * 100)::INTEGER
)
WHERE rate_cents IS NULL AND hourly_rate IS NOT NULL;

-- For any remaining NULLs (shouldn't happen if hourly_rate exists), set to 0
-- This is a fallback - in practice hourly_rate should always be present
UPDATE bookings
SET rate_cents = 0
WHERE rate_cents IS NULL;

-- Fix NULL currency: Use default 'USD'
UPDATE bookings
SET currency = 'USD'
WHERE currency IS NULL;

-- Fix negative platform_fee_cents: Set to 0 (no fee)
UPDATE bookings
SET platform_fee_cents = 0
WHERE platform_fee_cents IS NULL OR platform_fee_cents < 0;

-- Fix negative tutor_earnings_cents: Set to 0
UPDATE bookings
SET tutor_earnings_cents = 0
WHERE tutor_earnings_cents IS NULL OR tutor_earnings_cents < 0;

-- Fix NULL reference_id in wallet_transactions: Generate UUID for existing NULLs
-- This ensures idempotency going forward
UPDATE wallet_transactions
SET reference_id = 'legacy_' || id::TEXT || '_' || gen_random_uuid()::TEXT
WHERE reference_id IS NULL;

-- =============================================================================
-- STEP 2: Add NOT NULL constraints to bookings monetary fields
-- =============================================================================

-- bookings.rate_cents: Make NOT NULL
ALTER TABLE bookings
    ALTER COLUMN rate_cents SET NOT NULL;

-- bookings.currency: Make NOT NULL (already has DEFAULT 'USD')
ALTER TABLE bookings
    ALTER COLUMN currency SET NOT NULL;

-- bookings.platform_fee_cents: Make NOT NULL with DEFAULT 0
ALTER TABLE bookings
    ALTER COLUMN platform_fee_cents SET DEFAULT 0,
    ALTER COLUMN platform_fee_cents SET NOT NULL;

-- bookings.tutor_earnings_cents: Make NOT NULL with DEFAULT 0
ALTER TABLE bookings
    ALTER COLUMN tutor_earnings_cents SET DEFAULT 0,
    ALTER COLUMN tutor_earnings_cents SET NOT NULL;

-- =============================================================================
-- STEP 3: Add CHECK constraints for monetary field validation
-- =============================================================================

-- bookings.rate_cents: Must be >= 0 (0 for free trial sessions)
ALTER TABLE bookings
    DROP CONSTRAINT IF EXISTS chk_rate_cents_non_negative;
ALTER TABLE bookings
    ADD CONSTRAINT chk_rate_cents_non_negative CHECK (rate_cents >= 0);

-- bookings.platform_fee_cents: Must be >= 0
ALTER TABLE bookings
    DROP CONSTRAINT IF EXISTS chk_platform_fee_cents_non_negative;
ALTER TABLE bookings
    ADD CONSTRAINT chk_platform_fee_cents_non_negative CHECK (platform_fee_cents >= 0);

-- bookings.tutor_earnings_cents: Must be >= 0
ALTER TABLE bookings
    DROP CONSTRAINT IF EXISTS chk_tutor_earnings_cents_non_negative;
ALTER TABLE bookings
    ADD CONSTRAINT chk_tutor_earnings_cents_non_negative CHECK (tutor_earnings_cents >= 0);

-- bookings.currency: Valid 3-letter currency code
ALTER TABLE bookings
    DROP CONSTRAINT IF EXISTS chk_booking_currency_format;
ALTER TABLE bookings
    ADD CONSTRAINT chk_booking_currency_format CHECK (currency ~ '^[A-Z]{3}$');

-- =============================================================================
-- STEP 4: Fix wallet_transactions.reference_id for idempotency
-- =============================================================================

-- Make reference_id NOT NULL to enforce idempotency
ALTER TABLE wallet_transactions
    ALTER COLUMN reference_id SET NOT NULL;

-- =============================================================================
-- STEP 5: Verification
-- =============================================================================

DO $$
DECLARE
    null_count INTEGER;
    invalid_count INTEGER;
BEGIN
    -- Verify no NULL values remain in critical columns
    SELECT COUNT(*) INTO null_count FROM bookings WHERE rate_cents IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % bookings still have NULL rate_cents', null_count;
    END IF;

    SELECT COUNT(*) INTO null_count FROM bookings WHERE currency IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % bookings still have NULL currency', null_count;
    END IF;

    SELECT COUNT(*) INTO null_count FROM wallet_transactions WHERE reference_id IS NULL;
    IF null_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % wallet_transactions still have NULL reference_id', null_count;
    END IF;

    -- Verify no negative monetary values
    SELECT COUNT(*) INTO invalid_count FROM bookings WHERE rate_cents < 0;
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % bookings have negative rate_cents', invalid_count;
    END IF;

    SELECT COUNT(*) INTO invalid_count FROM bookings WHERE platform_fee_cents < 0;
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % bookings have negative platform_fee_cents', invalid_count;
    END IF;

    SELECT COUNT(*) INTO invalid_count FROM bookings WHERE tutor_earnings_cents < 0;
    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Migration 051 failed: % bookings have negative tutor_earnings_cents', invalid_count;
    END IF;

    RAISE NOTICE 'Migration 051 completed successfully: All monetary constraints applied';
    RAISE NOTICE '  - bookings.rate_cents: NOT NULL, >= 0';
    RAISE NOTICE '  - bookings.currency: NOT NULL, valid format';
    RAISE NOTICE '  - bookings.platform_fee_cents: NOT NULL DEFAULT 0, >= 0';
    RAISE NOTICE '  - bookings.tutor_earnings_cents: NOT NULL DEFAULT 0, >= 0';
    RAISE NOTICE '  - wallet_transactions.reference_id: NOT NULL (idempotency enforced)';
END $$;

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('051', 'Add NOT NULL and CHECK constraints to monetary fields')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- =============================================================================
-- ROLLBACK Section (if needed, run manually)
-- =============================================================================
--
-- BEGIN;
--
-- -- Remove CHECK constraints
-- ALTER TABLE bookings DROP CONSTRAINT IF EXISTS chk_rate_cents_non_negative;
-- ALTER TABLE bookings DROP CONSTRAINT IF EXISTS chk_platform_fee_cents_non_negative;
-- ALTER TABLE bookings DROP CONSTRAINT IF EXISTS chk_tutor_earnings_cents_non_negative;
-- ALTER TABLE bookings DROP CONSTRAINT IF EXISTS chk_booking_currency_format;
--
-- -- Remove NOT NULL constraints
-- ALTER TABLE bookings ALTER COLUMN rate_cents DROP NOT NULL;
-- ALTER TABLE bookings ALTER COLUMN currency DROP NOT NULL;
-- ALTER TABLE bookings ALTER COLUMN platform_fee_cents DROP NOT NULL;
-- ALTER TABLE bookings ALTER COLUMN tutor_earnings_cents DROP NOT NULL;
-- ALTER TABLE wallet_transactions ALTER COLUMN reference_id DROP NOT NULL;
--
-- -- Remove defaults (optional - keeping defaults is usually fine)
-- -- ALTER TABLE bookings ALTER COLUMN platform_fee_cents DROP DEFAULT;
-- -- ALTER TABLE bookings ALTER COLUMN tutor_earnings_cents DROP DEFAULT;
--
-- -- Remove migration record
-- DELETE FROM schema_migrations WHERE version = '051';
--
-- COMMIT;
-- =============================================================================
