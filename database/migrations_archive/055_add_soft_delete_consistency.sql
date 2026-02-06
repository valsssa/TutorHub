-- ============================================================================
-- Migration 055: Add Soft Delete Consistency Across All Tables
-- ============================================================================
--
-- Problem: Soft delete (deleted_at column) is inconsistently applied across tables.
--
-- Tables already WITH deleted_at:
--   - users, tutor_profiles, student_profiles, bookings, reviews, messages, message_attachments
--
-- Tables that NEED deleted_at (this migration):
--   - tutor_subjects, tutor_availabilities, tutor_certifications, tutor_education
--   - student_packages, payments, refunds
--   - wallets, wallet_transactions, payouts
--   - notifications, favorite_tutors, conversations
--
-- Tables that should NOT have soft delete (excluded):
--   - schema_migrations (system table)
--   - audit_log (immutable by design)
--   - Lookup/reference tables (subjects, supported_languages, etc.)
--   - Analytics tables (tutor_metrics, rebooking_metrics, etc.)
--   - System tables (webhook_events, notification_templates, etc.)
--
-- ============================================================================

-- ============================================================================
-- TUTOR-RELATED TABLES
-- ============================================================================

-- tutor_subjects
ALTER TABLE tutor_subjects
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE tutor_subjects
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_subjects_active
ON tutor_subjects(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_subjects_deleted_at
ON tutor_subjects(deleted_at) WHERE deleted_at IS NULL;

-- tutor_availabilities
ALTER TABLE tutor_availabilities
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE tutor_availabilities
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_availabilities_active
ON tutor_availabilities(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_availabilities_deleted_at
ON tutor_availabilities(deleted_at) WHERE deleted_at IS NULL;

-- tutor_certifications
ALTER TABLE tutor_certifications
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE tutor_certifications
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_certifications_active
ON tutor_certifications(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_certifications_deleted_at
ON tutor_certifications(deleted_at) WHERE deleted_at IS NULL;

-- tutor_education
ALTER TABLE tutor_education
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE tutor_education
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_education_active
ON tutor_education(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_education_deleted_at
ON tutor_education(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- STUDENT-RELATED TABLES
-- ============================================================================

-- student_packages
ALTER TABLE student_packages
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE student_packages
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_student_packages_active_id
ON student_packages(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_student_packages_deleted_at
ON student_packages(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- PAYMENT TABLES
-- ============================================================================

-- payments
ALTER TABLE payments
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE payments
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_payments_active
ON payments(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_payments_deleted_at
ON payments(deleted_at) WHERE deleted_at IS NULL;

-- refunds
ALTER TABLE refunds
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE refunds
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_refunds_active
ON refunds(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_refunds_deleted_at
ON refunds(deleted_at) WHERE deleted_at IS NULL;

-- wallets
ALTER TABLE wallets
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE wallets
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_wallets_active
ON wallets(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_wallets_deleted_at
ON wallets(deleted_at) WHERE deleted_at IS NULL;

-- wallet_transactions
ALTER TABLE wallet_transactions
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE wallet_transactions
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_wallet_transactions_active
ON wallet_transactions(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_wallet_transactions_deleted_at
ON wallet_transactions(deleted_at) WHERE deleted_at IS NULL;

-- payouts
ALTER TABLE payouts
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE payouts
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_payouts_active
ON payouts(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_payouts_deleted_at
ON payouts(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- COMMUNICATION TABLES
-- ============================================================================

-- notifications
ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_notifications_active
ON notifications(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_notifications_deleted_at
ON notifications(deleted_at) WHERE deleted_at IS NULL;

-- conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_active
ON conversations(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at
ON conversations(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- FEATURE TABLES
-- ============================================================================

-- favorite_tutors
ALTER TABLE favorite_tutors
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL;

ALTER TABLE favorite_tutors
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_favorite_tutors_active
ON favorite_tutors(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_favorite_tutors_deleted_at
ON favorite_tutors(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- ACTIVE RECORD VIEWS
-- ============================================================================
-- These views provide easy access to non-deleted records

-- Tutor-related views
CREATE OR REPLACE VIEW active_tutor_subjects AS
SELECT * FROM tutor_subjects WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_availabilities AS
SELECT * FROM tutor_availabilities WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_certifications AS
SELECT * FROM tutor_certifications WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_tutor_education AS
SELECT * FROM tutor_education WHERE deleted_at IS NULL;

-- Student-related views
CREATE OR REPLACE VIEW active_student_packages AS
SELECT * FROM student_packages WHERE deleted_at IS NULL;

-- Payment-related views
CREATE OR REPLACE VIEW active_payments AS
SELECT * FROM payments WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_refunds AS
SELECT * FROM refunds WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_wallets AS
SELECT * FROM wallets WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_wallet_transactions AS
SELECT * FROM wallet_transactions WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_payouts AS
SELECT * FROM payouts WHERE deleted_at IS NULL;

-- Communication-related views
CREATE OR REPLACE VIEW active_notifications AS
SELECT * FROM notifications WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_conversations AS
SELECT * FROM conversations WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_messages AS
SELECT * FROM messages WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_message_attachments AS
SELECT * FROM message_attachments WHERE deleted_at IS NULL;

-- Feature-related views
CREATE OR REPLACE VIEW active_favorite_tutors AS
SELECT * FROM favorite_tutors WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_reviews AS
SELECT * FROM reviews WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_student_profiles AS
SELECT * FROM student_profiles WHERE deleted_at IS NULL;

-- ============================================================================
-- RECORD MIGRATION VERSION
-- ============================================================================

INSERT INTO schema_migrations (version, description)
VALUES ('055', 'Add soft delete consistency across all tables')
ON CONFLICT (version) DO NOTHING;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Migration 055: Soft Delete Consistency - Complete';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE '  Tables Updated with deleted_at/deleted_by:';
    RAISE NOTICE '  • tutor_subjects';
    RAISE NOTICE '  • tutor_availabilities';
    RAISE NOTICE '  • tutor_certifications';
    RAISE NOTICE '  • tutor_education';
    RAISE NOTICE '  • student_packages';
    RAISE NOTICE '  • payments';
    RAISE NOTICE '  • refunds';
    RAISE NOTICE '  • wallets';
    RAISE NOTICE '  • wallet_transactions';
    RAISE NOTICE '  • payouts';
    RAISE NOTICE '  • notifications';
    RAISE NOTICE '  • conversations';
    RAISE NOTICE '  • favorite_tutors';
    RAISE NOTICE '';
    RAISE NOTICE '  Views Created:';
    RAISE NOTICE '  • active_tutor_subjects';
    RAISE NOTICE '  • active_tutor_availabilities';
    RAISE NOTICE '  • active_tutor_certifications';
    RAISE NOTICE '  • active_tutor_education';
    RAISE NOTICE '  • active_student_packages';
    RAISE NOTICE '  • active_payments';
    RAISE NOTICE '  • active_refunds';
    RAISE NOTICE '  • active_wallets';
    RAISE NOTICE '  • active_wallet_transactions';
    RAISE NOTICE '  • active_payouts';
    RAISE NOTICE '  • active_notifications';
    RAISE NOTICE '  • active_conversations';
    RAISE NOTICE '  • active_messages';
    RAISE NOTICE '  • active_message_attachments';
    RAISE NOTICE '  • active_favorite_tutors';
    RAISE NOTICE '  • active_reviews';
    RAISE NOTICE '  • active_student_profiles';
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;
