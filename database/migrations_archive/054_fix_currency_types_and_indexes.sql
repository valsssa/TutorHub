-- Migration 054: Fix currency type inconsistency and add missing composite indexes
-- Purpose: Standardize all currency columns to VARCHAR(3) and add performance indexes
-- Date: 2026-02-05
--
-- Problem 1: Currency Type Inconsistency
-- CHAR(3) pads with spaces causing comparison failures: 'USD' != 'USD '
-- - bookings.currency: CHAR(3) -> VARCHAR(3)
-- - payments.currency: CHAR(3) -> VARCHAR(3)
-- - refunds.currency: CHAR(3) -> VARCHAR(3)
-- - payouts.currency: CHAR(3) -> VARCHAR(3)
--
-- Problem 2: Missing Composite Indexes for common query patterns
-- - Payment lookups by student + status + date
-- - Wallet transaction queries by wallet + type + status
-- - Notification queries by user + read status + date
-- - Message search in conversations (with soft delete filter)
-- - Student packages by expiry (with sessions remaining filter)

-- ============================================================================
-- PART 1: FIX CURRENCY TYPE INCONSISTENCY (CHAR(3) -> VARCHAR(3))
-- ============================================================================

-- 1.1 Trim any existing padded spaces in currency columns
-- This must happen BEFORE type conversion to prevent constraint violations

DO $$
BEGIN
    -- Trim bookings.currency
    UPDATE bookings SET currency = TRIM(currency) WHERE currency != TRIM(currency);
    RAISE NOTICE 'Trimmed padded spaces in bookings.currency';
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'bookings.currency column does not exist, skipping trim';
END $$;

DO $$
BEGIN
    -- Trim payments.currency
    UPDATE payments SET currency = TRIM(currency) WHERE currency != TRIM(currency);
    RAISE NOTICE 'Trimmed padded spaces in payments.currency';
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'payments.currency column does not exist, skipping trim';
END $$;

DO $$
BEGIN
    -- Trim refunds.currency
    UPDATE refunds SET currency = TRIM(currency) WHERE currency != TRIM(currency);
    RAISE NOTICE 'Trimmed padded spaces in refunds.currency';
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'refunds.currency column does not exist, skipping trim';
END $$;

DO $$
BEGIN
    -- Trim payouts.currency
    UPDATE payouts SET currency = TRIM(currency) WHERE currency != TRIM(currency);
    RAISE NOTICE 'Trimmed padded spaces in payouts.currency';
EXCEPTION WHEN undefined_column THEN
    RAISE NOTICE 'payouts.currency column does not exist, skipping trim';
END $$;

-- 1.2 Convert CHAR(3) columns to VARCHAR(3)
-- Note: We need to drop and recreate constraints that reference these columns

-- Bookings currency conversion
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'bookings'
        AND column_name = 'currency'
        AND data_type = 'character'
        AND character_maximum_length = 3
    ) THEN
        -- Drop existing constraint if present
        ALTER TABLE bookings DROP CONSTRAINT IF EXISTS bookings_valid_currency_format;

        -- Convert type
        ALTER TABLE bookings ALTER COLUMN currency TYPE VARCHAR(3);

        -- Re-add constraint
        ALTER TABLE bookings ADD CONSTRAINT bookings_valid_currency_format
            CHECK (currency ~ '^[A-Z]{3}$');

        RAISE NOTICE 'Converted bookings.currency from CHAR(3) to VARCHAR(3)';
    ELSE
        RAISE NOTICE 'bookings.currency already VARCHAR(3) or does not exist';
    END IF;
END $$;

-- Payments currency conversion
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'payments'
        AND column_name = 'currency'
        AND data_type = 'character'
        AND character_maximum_length = 3
    ) THEN
        -- Drop existing constraint if present
        ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_valid_currency_format;
        ALTER TABLE payments DROP CONSTRAINT IF EXISTS valid_payment_currency;

        -- Convert type
        ALTER TABLE payments ALTER COLUMN currency TYPE VARCHAR(3);

        -- Re-add constraint
        ALTER TABLE payments ADD CONSTRAINT valid_payment_currency
            CHECK (currency ~ '^[A-Z]{3}$');

        RAISE NOTICE 'Converted payments.currency from CHAR(3) to VARCHAR(3)';
    ELSE
        RAISE NOTICE 'payments.currency already VARCHAR(3) or does not exist';
    END IF;
END $$;

-- Refunds currency conversion
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'refunds'
        AND column_name = 'currency'
        AND data_type = 'character'
        AND character_maximum_length = 3
    ) THEN
        -- Drop existing constraint if present
        ALTER TABLE refunds DROP CONSTRAINT IF EXISTS refunds_valid_currency_format;
        ALTER TABLE refunds DROP CONSTRAINT IF EXISTS valid_refund_currency;

        -- Convert type
        ALTER TABLE refunds ALTER COLUMN currency TYPE VARCHAR(3);

        -- Re-add constraint
        ALTER TABLE refunds ADD CONSTRAINT valid_refund_currency
            CHECK (currency ~ '^[A-Z]{3}$');

        RAISE NOTICE 'Converted refunds.currency from CHAR(3) to VARCHAR(3)';
    ELSE
        RAISE NOTICE 'refunds.currency already VARCHAR(3) or does not exist';
    END IF;
END $$;

-- Payouts currency conversion
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'payouts'
        AND column_name = 'currency'
        AND data_type = 'character'
        AND character_maximum_length = 3
    ) THEN
        -- Drop existing constraint if present
        ALTER TABLE payouts DROP CONSTRAINT IF EXISTS payouts_valid_currency_format;
        ALTER TABLE payouts DROP CONSTRAINT IF EXISTS valid_payout_currency;

        -- Convert type
        ALTER TABLE payouts ALTER COLUMN currency TYPE VARCHAR(3);

        -- Re-add constraint
        ALTER TABLE payouts ADD CONSTRAINT valid_payout_currency
            CHECK (currency ~ '^[A-Z]{3}$');

        RAISE NOTICE 'Converted payouts.currency from CHAR(3) to VARCHAR(3)';
    ELSE
        RAISE NOTICE 'payouts.currency already VARCHAR(3) or does not exist';
    END IF;
END $$;

-- ============================================================================
-- PART 2: ADD MISSING COMPOSITE INDEXES
-- ============================================================================

-- 2.1 Payment lookups by student + status + date
-- Usage: Student payment history queries, filtered by status
-- Statistics: Optimizes queries like:
--   SELECT * FROM payments WHERE student_id = ? AND status = ? ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_payments_student_status_created
    ON payments(student_id, status, created_at DESC);

COMMENT ON INDEX idx_payments_student_status_created IS
    'Composite index for student payment history queries with status filter and date ordering';

-- 2.2 Wallet transaction queries by wallet + type + status
-- Usage: Wallet transaction filtering (deposits, withdrawals, etc.)
-- Statistics: Optimizes queries like:
--   SELECT * FROM wallet_transactions WHERE wallet_id = ? AND type = ? AND status = ?
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_wallet_type_status
    ON wallet_transactions(wallet_id, type, status);

COMMENT ON INDEX idx_wallet_transactions_wallet_type_status IS
    'Composite index for wallet transaction queries filtered by type and status';

-- 2.3 Notification queries by user + read status + date
-- Usage: Unread notification counts, notification lists
-- Statistics: Optimizes queries like:
--   SELECT * FROM notifications WHERE user_id = ? AND is_read = FALSE ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created
    ON notifications(user_id, is_read, created_at DESC);

COMMENT ON INDEX idx_notifications_user_read_created IS
    'Composite index for user notification queries with read status filter and date ordering';

-- 2.4 Message search in conversations (with soft delete filter)
-- Usage: Loading conversation message history
-- Statistics: Optimizes queries like:
--   SELECT * FROM messages WHERE conversation_id = ? AND deleted_at IS NULL ORDER BY created_at DESC
-- Note: Partial index excludes soft-deleted messages for better performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
    ON messages(conversation_id, created_at DESC)
    WHERE deleted_at IS NULL;

COMMENT ON INDEX idx_messages_conversation_created IS
    'Partial composite index for conversation message queries, excluding soft-deleted messages';

-- 2.5 Student packages by expiry (with sessions remaining filter)
-- Usage: Finding expiring packages that still have sessions
-- Statistics: Optimizes queries like:
--   SELECT * FROM student_packages WHERE expires_at < ? AND sessions_remaining > 0
-- Note: Partial index only includes packages with remaining sessions
CREATE INDEX IF NOT EXISTS idx_student_packages_expiry
    ON student_packages(expires_at)
    WHERE sessions_remaining > 0;

COMMENT ON INDEX idx_student_packages_expiry IS
    'Partial index for finding expiring packages with remaining sessions';

-- ============================================================================
-- PART 3: VERIFICATION
-- ============================================================================

-- Verify currency column types
DO $$
DECLARE
    bookings_type TEXT;
    payments_type TEXT;
    refunds_type TEXT;
    payouts_type TEXT;
BEGIN
    -- Check bookings.currency
    SELECT data_type INTO bookings_type
    FROM information_schema.columns
    WHERE table_name = 'bookings' AND column_name = 'currency';

    -- Check payments.currency
    SELECT data_type INTO payments_type
    FROM information_schema.columns
    WHERE table_name = 'payments' AND column_name = 'currency';

    -- Check refunds.currency
    SELECT data_type INTO refunds_type
    FROM information_schema.columns
    WHERE table_name = 'refunds' AND column_name = 'currency';

    -- Check payouts.currency
    SELECT data_type INTO payouts_type
    FROM information_schema.columns
    WHERE table_name = 'payouts' AND column_name = 'currency';

    RAISE NOTICE '=== Currency Column Type Verification ===';
    RAISE NOTICE 'bookings.currency: %', COALESCE(bookings_type, 'NOT FOUND');
    RAISE NOTICE 'payments.currency: %', COALESCE(payments_type, 'NOT FOUND');
    RAISE NOTICE 'refunds.currency: %', COALESCE(refunds_type, 'NOT FOUND');
    RAISE NOTICE 'payouts.currency: %', COALESCE(payouts_type, 'NOT FOUND');
    RAISE NOTICE '=========================================';
END $$;

-- Verify indexes were created
DO $$
DECLARE
    idx_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO idx_count
    FROM pg_indexes
    WHERE indexname IN (
        'idx_payments_student_status_created',
        'idx_wallet_transactions_wallet_type_status',
        'idx_notifications_user_read_created',
        'idx_messages_conversation_created',
        'idx_student_packages_expiry'
    );

    RAISE NOTICE '=== New Composite Indexes Created: % of 5 ===', idx_count;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migration 054 completed successfully';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Type Changes:';
    RAISE NOTICE '  - bookings.currency: CHAR(3) -> VARCHAR(3)';
    RAISE NOTICE '  - payments.currency: CHAR(3) -> VARCHAR(3)';
    RAISE NOTICE '  - refunds.currency: CHAR(3) -> VARCHAR(3)';
    RAISE NOTICE '  - payouts.currency: CHAR(3) -> VARCHAR(3)';
    RAISE NOTICE '';
    RAISE NOTICE 'New Composite Indexes:';
    RAISE NOTICE '  - idx_payments_student_status_created';
    RAISE NOTICE '  - idx_wallet_transactions_wallet_type_status';
    RAISE NOTICE '  - idx_notifications_user_read_created';
    RAISE NOTICE '  - idx_messages_conversation_created (partial)';
    RAISE NOTICE '  - idx_student_packages_expiry (partial)';
    RAISE NOTICE '';
    RAISE NOTICE '=================================================';
END $$;
