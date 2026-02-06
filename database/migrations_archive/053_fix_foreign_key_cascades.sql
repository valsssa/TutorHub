-- ============================================================================
-- Migration 053: Fix Foreign Key CASCADE Rules for User Deletion
-- ============================================================================
--
-- Problem: Six tables use ON DELETE RESTRICT, blocking user deletion (GDPR issue)
--   - student_packages.pricing_option_id → ON DELETE RESTRICT
--   - payments.student_id → ON DELETE RESTRICT
--   - refunds.payment_id → ON DELETE RESTRICT
--   - wallets.user_id → ON DELETE RESTRICT
--   - wallet_transactions.wallet_id → ON DELETE RESTRICT
--   - payouts.tutor_id → ON DELETE RESTRICT
--
-- Solution Strategy:
--   1. payments, payouts → ON DELETE SET NULL with archived_*_id backup columns
--   2. wallets, wallet_transactions → ON DELETE CASCADE (wallet goes with user)
--   3. refunds → ON DELETE CASCADE (refund references are preserved via payment archive)
--   4. student_packages → ON DELETE CASCADE (packages go with student)
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- STEP 1: Add Archive Columns for Financial Records
-- ============================================================================
-- These columns preserve the original user ID even after the user is deleted

-- Add archived_student_id to payments table
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS archived_student_id INTEGER;

COMMENT ON COLUMN payments.archived_student_id IS 'Preserves original student_id after user deletion for financial records';

-- Add archived_tutor_id to payouts table
ALTER TABLE payouts
ADD COLUMN IF NOT EXISTS archived_tutor_id INTEGER;

COMMENT ON COLUMN payouts.archived_tutor_id IS 'Preserves original tutor_id after user deletion for financial records';

-- ============================================================================
-- STEP 2: Create Archive Trigger Function
-- ============================================================================
-- This function copies the user reference to the archived column before it's set to NULL

CREATE OR REPLACE FUNCTION archive_user_reference()
RETURNS TRIGGER AS $$
BEGIN
    -- Only act when the user reference is being set to NULL (user deletion)
    IF TG_TABLE_NAME = 'payments' THEN
        -- When student_id is about to become NULL, preserve it in archived_student_id
        IF OLD.student_id IS NOT NULL AND NEW.student_id IS NULL THEN
            NEW.archived_student_id := OLD.student_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'payouts' THEN
        -- When tutor_id is about to become NULL, preserve it in archived_tutor_id
        IF OLD.tutor_id IS NOT NULL AND NEW.tutor_id IS NULL THEN
            NEW.archived_tutor_id := OLD.tutor_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION archive_user_reference() IS 'Preserves user IDs in archived columns before ON DELETE SET NULL takes effect';

-- ============================================================================
-- STEP 3: Create Triggers on payments and payouts Tables
-- ============================================================================

-- Trigger for payments table
DROP TRIGGER IF EXISTS trg_archive_payment_student ON payments;
CREATE TRIGGER trg_archive_payment_student
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION archive_user_reference();

-- Trigger for payouts table
DROP TRIGGER IF EXISTS trg_archive_payout_tutor ON payouts;
CREATE TRIGGER trg_archive_payout_tutor
    BEFORE UPDATE ON payouts
    FOR EACH ROW
    EXECUTE FUNCTION archive_user_reference();

-- ============================================================================
-- STEP 4: Pre-populate Archive Columns (Preserve Existing Data)
-- ============================================================================
-- Copy current values to archived columns for any existing records
-- This ensures we don't lose data for records that were created before this migration

UPDATE payments
SET archived_student_id = student_id
WHERE archived_student_id IS NULL AND student_id IS NOT NULL;

UPDATE payouts
SET archived_tutor_id = tutor_id
WHERE archived_tutor_id IS NULL AND tutor_id IS NOT NULL;

-- ============================================================================
-- STEP 5: Drop and Recreate Foreign Keys with Correct CASCADE Rules
-- ============================================================================

-- 5.1 student_packages.pricing_option_id: RESTRICT → CASCADE
-- Rationale: When a student is deleted, their package purchases should go with them
ALTER TABLE student_packages
DROP CONSTRAINT IF EXISTS student_packages_pricing_option_id_fkey;

ALTER TABLE student_packages
ADD CONSTRAINT student_packages_pricing_option_id_fkey
FOREIGN KEY (pricing_option_id) REFERENCES tutor_pricing_options(id) ON DELETE CASCADE;

-- 5.2 payments.student_id: RESTRICT → SET NULL
-- Rationale: Preserve payment history for accounting, but allow user deletion
ALTER TABLE payments
DROP CONSTRAINT IF EXISTS payments_student_id_fkey;

ALTER TABLE payments
ADD CONSTRAINT payments_student_id_fkey
FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE SET NULL;

-- Also make student_id nullable since we're using SET NULL
ALTER TABLE payments
ALTER COLUMN student_id DROP NOT NULL;

-- 5.3 refunds.payment_id: RESTRICT → CASCADE
-- Rationale: If payment is deleted, refund records should cascade
-- (Though payments typically won't be deleted - they use SET NULL for user reference)
ALTER TABLE refunds
DROP CONSTRAINT IF EXISTS refunds_payment_id_fkey;

ALTER TABLE refunds
ADD CONSTRAINT refunds_payment_id_fkey
FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE CASCADE;

-- 5.4 wallets.user_id: RESTRICT → CASCADE
-- Rationale: Wallet is integral to user; when user is deleted, wallet goes too
ALTER TABLE wallets
DROP CONSTRAINT IF EXISTS wallets_user_id_fkey;

ALTER TABLE wallets
ADD CONSTRAINT wallets_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 5.5 wallet_transactions.wallet_id: RESTRICT → CASCADE
-- Rationale: Transactions belong to wallet; when wallet is deleted, transactions go too
ALTER TABLE wallet_transactions
DROP CONSTRAINT IF EXISTS wallet_transactions_wallet_id_fkey;

ALTER TABLE wallet_transactions
ADD CONSTRAINT wallet_transactions_wallet_id_fkey
FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE;

-- 5.6 payouts.tutor_id: RESTRICT → SET NULL
-- Rationale: Preserve payout history for tax/accounting, but allow user deletion
ALTER TABLE payouts
DROP CONSTRAINT IF EXISTS payouts_tutor_id_fkey;

ALTER TABLE payouts
ADD CONSTRAINT payouts_tutor_id_fkey
FOREIGN KEY (tutor_id) REFERENCES users(id) ON DELETE SET NULL;

-- Also make tutor_id nullable since we're using SET NULL
ALTER TABLE payouts
ALTER COLUMN tutor_id DROP NOT NULL;

-- ============================================================================
-- STEP 6: Add Indexes for Archive Columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_payments_archived_student ON payments(archived_student_id)
WHERE archived_student_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_payouts_archived_tutor ON payouts(archived_tutor_id)
WHERE archived_tutor_id IS NOT NULL;

-- ============================================================================
-- STEP 7: Add Helper Views for Financial Reporting
-- ============================================================================

-- View that always shows the student ID (current or archived)
CREATE OR REPLACE VIEW payments_with_student AS
SELECT
    p.*,
    COALESCE(p.student_id, p.archived_student_id) AS effective_student_id
FROM payments p;

COMMENT ON VIEW payments_with_student IS 'Payments view that shows effective_student_id even after user deletion';

-- View that always shows the tutor ID (current or archived)
CREATE OR REPLACE VIEW payouts_with_tutor AS
SELECT
    p.*,
    COALESCE(p.tutor_id, p.archived_tutor_id) AS effective_tutor_id
FROM payouts p;

COMMENT ON VIEW payouts_with_tutor IS 'Payouts view that shows effective_tutor_id even after user deletion';

-- ============================================================================
-- STEP 8: Record Migration
-- ============================================================================

INSERT INTO schema_migrations (version, description)
VALUES ('053', 'Fix foreign key CASCADE rules for GDPR-compliant user deletion')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (Run manually if needed)
-- ============================================================================
/*
BEGIN;

-- Remove views
DROP VIEW IF EXISTS payouts_with_tutor;
DROP VIEW IF EXISTS payments_with_student;

-- Remove indexes
DROP INDEX IF EXISTS idx_payouts_archived_tutor;
DROP INDEX IF EXISTS idx_payments_archived_student;

-- Restore original foreign key constraints (RESTRICT)
ALTER TABLE payouts
DROP CONSTRAINT IF EXISTS payouts_tutor_id_fkey;
ALTER TABLE payouts
ADD CONSTRAINT payouts_tutor_id_fkey
FOREIGN KEY (tutor_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE payouts ALTER COLUMN tutor_id SET NOT NULL;

ALTER TABLE wallet_transactions
DROP CONSTRAINT IF EXISTS wallet_transactions_wallet_id_fkey;
ALTER TABLE wallet_transactions
ADD CONSTRAINT wallet_transactions_wallet_id_fkey
FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE RESTRICT;

ALTER TABLE wallets
DROP CONSTRAINT IF EXISTS wallets_user_id_fkey;
ALTER TABLE wallets
ADD CONSTRAINT wallets_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;

ALTER TABLE refunds
DROP CONSTRAINT IF EXISTS refunds_payment_id_fkey;
ALTER TABLE refunds
ADD CONSTRAINT refunds_payment_id_fkey
FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE RESTRICT;

ALTER TABLE payments
DROP CONSTRAINT IF EXISTS payments_student_id_fkey;
ALTER TABLE payments
ADD CONSTRAINT payments_student_id_fkey
FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE payments ALTER COLUMN student_id SET NOT NULL;

ALTER TABLE student_packages
DROP CONSTRAINT IF EXISTS student_packages_pricing_option_id_fkey;
ALTER TABLE student_packages
ADD CONSTRAINT student_packages_pricing_option_id_fkey
FOREIGN KEY (pricing_option_id) REFERENCES tutor_pricing_options(id) ON DELETE RESTRICT;

-- Remove triggers
DROP TRIGGER IF EXISTS trg_archive_payout_tutor ON payouts;
DROP TRIGGER IF EXISTS trg_archive_payment_student ON payments;

-- Remove function
DROP FUNCTION IF EXISTS archive_user_reference();

-- Remove archive columns
ALTER TABLE payouts DROP COLUMN IF EXISTS archived_tutor_id;
ALTER TABLE payments DROP COLUMN IF EXISTS archived_student_id;

-- Remove migration record
DELETE FROM schema_migrations WHERE version = '053';

COMMIT;
*/

-- ============================================================================
-- Summary of Changes:
-- ============================================================================
--
-- Table: student_packages
--   pricing_option_id: RESTRICT → CASCADE
--   Rationale: Package purchases cascade with the student
--
-- Table: payments
--   student_id: RESTRICT → SET NULL (made nullable)
--   Added: archived_student_id column with trigger
--   Rationale: Preserve payment records for accounting
--
-- Table: refunds
--   payment_id: RESTRICT → CASCADE
--   Rationale: Refunds cascade with their parent payment
--
-- Table: wallets
--   user_id: RESTRICT → CASCADE
--   Rationale: Wallet is integral to user identity
--
-- Table: wallet_transactions
--   wallet_id: RESTRICT → CASCADE
--   Rationale: Transactions cascade with their wallet
--
-- Table: payouts
--   tutor_id: RESTRICT → SET NULL (made nullable)
--   Added: archived_tutor_id column with trigger
--   Rationale: Preserve payout history for tax/accounting
--
-- ============================================================================
