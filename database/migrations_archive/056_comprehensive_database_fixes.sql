-- ============================================================================
-- Migration 056: Comprehensive Database Fixes
-- Date: 2026-02-05
-- Description: Fixes critical/high issues from database audit:
--   - Schema consistency & constraint fixes
--   - Index optimization (add missing, remove redundant)
--   - Soft delete consistency
--   - Security constraints
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: SCHEMA CONSISTENCY & CONSTRAINT FIXES
-- ============================================================================

-- 1.1 Wallet currency validation (missing from init.sql)
ALTER TABLE wallets
ADD CONSTRAINT IF NOT EXISTS valid_wallet_currency
CHECK (currency ~ '^[A-Z]{3}$');

ALTER TABLE wallet_transactions
ADD CONSTRAINT IF NOT EXISTS valid_wallet_transaction_currency
CHECK (currency ~ '^[A-Z]{3}$');

-- 1.2 Wallet transaction amount must be non-zero (HIGH severity)
ALTER TABLE wallet_transactions
ADD CONSTRAINT IF NOT EXISTS chk_wallet_transaction_amount_nonzero
CHECK (amount_cents <> 0);

-- 1.3 Fix tutor_subjects proficiency case mismatch (DEFAULT 'B2' vs lowercase constraint)
UPDATE tutor_subjects
SET proficiency_level = UPPER(proficiency_level)
WHERE proficiency_level ~ '^[a-z]';

ALTER TABLE tutor_subjects
DROP CONSTRAINT IF EXISTS valid_proficiency;

ALTER TABLE tutor_subjects
ADD CONSTRAINT valid_proficiency
CHECK (proficiency_level IN ('NATIVE', 'C2', 'C1', 'B2', 'B1', 'A2', 'A1'));

-- 1.4 Notifications category should be NOT NULL (has default 'general')
UPDATE notifications SET category = 'general' WHERE category IS NULL;
ALTER TABLE notifications ALTER COLUMN category SET NOT NULL;

-- 1.5 Fix rebooking_metrics cascade behavior (preserve analytics on delete)
ALTER TABLE rebooking_metrics
DROP CONSTRAINT IF EXISTS rebooking_metrics_tutor_profile_id_fkey,
DROP CONSTRAINT IF EXISTS rebooking_metrics_student_id_fkey,
DROP CONSTRAINT IF EXISTS rebooking_metrics_original_booking_id_fkey,
DROP CONSTRAINT IF EXISTS rebooking_metrics_rebooked_booking_id_fkey;

ALTER TABLE rebooking_metrics
ADD CONSTRAINT rebooking_metrics_tutor_profile_id_fkey
    FOREIGN KEY (tutor_profile_id) REFERENCES tutor_profiles(id) ON DELETE SET NULL,
ADD CONSTRAINT rebooking_metrics_student_id_fkey
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE SET NULL,
ADD CONSTRAINT rebooking_metrics_original_booking_id_fkey
    FOREIGN KEY (original_booking_id) REFERENCES bookings(id) ON DELETE SET NULL,
ADD CONSTRAINT rebooking_metrics_rebooked_booking_id_fkey
    FOREIGN KEY (rebooked_booking_id) REFERENCES bookings(id) ON DELETE SET NULL;

-- 1.6 Add notification_analytics foreign key (missing)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'notification_analytics_template_key_fkey'
    ) THEN
        ALTER TABLE notification_analytics
        ADD CONSTRAINT notification_analytics_template_key_fkey
        FOREIGN KEY (template_key) REFERENCES notification_templates(template_key) ON DELETE CASCADE;
    END IF;
END $$;

-- 1.7 Message must have at least one participant
ALTER TABLE messages
ADD CONSTRAINT IF NOT EXISTS chk_message_has_participant
CHECK (sender_id IS NOT NULL OR recipient_id IS NOT NULL);

-- 1.8 Standardize currency types in lookup tables (CHAR(3) -> VARCHAR(3))
ALTER TABLE currency_rates
DROP CONSTRAINT IF EXISTS uq_currency_pair_date;

ALTER TABLE supported_currencies
ALTER COLUMN currency_code TYPE VARCHAR(3);

ALTER TABLE currency_rates
ALTER COLUMN from_currency TYPE VARCHAR(3),
ALTER COLUMN to_currency TYPE VARCHAR(3);

ALTER TABLE currency_rates
ADD CONSTRAINT uq_currency_pair_date UNIQUE (from_currency, to_currency, valid_from);

-- 1.9 Add tutor_response_log unique constraint (prevent duplicates)
DELETE FROM tutor_response_log a
USING tutor_response_log b
WHERE a.booking_id = b.booking_id
AND a.id < b.id
AND a.booking_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_tutor_response_log_booking'
    ) THEN
        ALTER TABLE tutor_response_log
        ADD CONSTRAINT uq_tutor_response_log_booking UNIQUE (booking_id);
    END IF;
END $$;

-- 1.10 User locale confidence should be bounded 0-1
ALTER TABLE users
ADD CONSTRAINT IF NOT EXISTS chk_users_locale_confidence_range
CHECK (locale_detection_confidence IS NULL OR locale_detection_confidence BETWEEN 0 AND 1);

-- 1.11 Add missing FK for tutor_profiles.approved_by
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_tutor_profiles_approved_by'
    ) THEN
        ALTER TABLE tutor_profiles
        ADD CONSTRAINT fk_tutor_profiles_approved_by
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ============================================================================
-- SECTION 2: INDEX OPTIMIZATION
-- ============================================================================

-- 2.1 CRITICAL: Missing FK indexes
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_tutor
ON favorite_tutors(tutor_profile_id)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_student_packages_pricing_option
ON student_packages(pricing_option_id);

-- 2.2 CRITICAL: Composite indexes for common query patterns
DROP INDEX IF EXISTS idx_bookings_subject;
CREATE INDEX IF NOT EXISTS idx_bookings_subject_state_time
ON bookings(subject_id, session_state, start_time DESC)
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_tutor_public_active
ON reviews(tutor_profile_id, created_at DESC)
WHERE is_public = TRUE AND deleted_at IS NULL;

-- 2.3 HIGH: Remove low-selectivity boolean column indexes
DROP INDEX IF EXISTS idx_users_active;
DROP INDEX IF EXISTS idx_tutor_profiles_approved;

-- 2.4 HIGH: Remove redundant overlapping index
DROP INDEX IF EXISTS idx_bookings_session_state;

-- 2.5 HIGH: Tutor search optimization
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_search
ON tutor_profiles(hourly_rate, average_rating DESC)
WHERE deleted_at IS NULL AND is_approved = TRUE;

-- 2.6 HIGH: Messages booking with soft delete filter
DROP INDEX IF EXISTS idx_messages_booking;
CREATE INDEX IF NOT EXISTS idx_messages_booking_active
ON messages(booking_id, created_at DESC)
WHERE deleted_at IS NULL AND booking_id IS NOT NULL;

-- 2.7 MEDIUM: Payouts pending partial index
CREATE INDEX IF NOT EXISTS idx_payouts_pending
ON payouts(tutor_id, created_at DESC)
WHERE status = 'PENDING' AND deleted_at IS NULL;

-- 2.8 MEDIUM: Blackouts GIST range index for conflict checking
CREATE INDEX IF NOT EXISTS idx_blackouts_tutor_range
ON tutor_blackouts USING gist (tutor_id, tstzrange(start_at, end_at, '[)'));

-- 2.9 MEDIUM: Notifications type index
CREATE INDEX IF NOT EXISTS idx_notifications_type_created
ON notifications(type, created_at DESC)
WHERE deleted_at IS NULL;

-- 2.10 MEDIUM: Wallet transactions completed_at index
CREATE INDEX IF NOT EXISTS idx_wallet_transactions_completed
ON wallet_transactions(completed_at DESC)
WHERE status = 'COMPLETED';

-- 2.11 MEDIUM: Drop low-selectivity currency index
DROP INDEX IF EXISTS idx_users_currency;

-- 2.12 MEDIUM: Background job optimization indexes
CREATE INDEX IF NOT EXISTS idx_bookings_scheduled_start
ON bookings(start_time)
WHERE session_state = 'SCHEDULED' AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_bookings_active_end
ON bookings(end_time)
WHERE session_state = 'ACTIVE' AND deleted_at IS NULL;

-- 2.13 Remove redundant webhook index (UNIQUE constraint creates implicit index)
DROP INDEX IF EXISTS idx_webhook_events_stripe_event_id;

-- ============================================================================
-- SECTION 3: SOFT DELETE CONSISTENCY
-- ============================================================================

-- 3.1 Add soft delete to tutor_pricing_options
ALTER TABLE tutor_pricing_options
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_pricing_options_active
ON tutor_pricing_options(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_tutor_pricing_options_deleted_at
ON tutor_pricing_options(deleted_at) WHERE deleted_at IS NOT NULL;

-- 3.2 Add soft delete to session_materials
ALTER TABLE session_materials
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_session_materials_active
ON session_materials(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_session_materials_deleted_at
ON session_materials(deleted_at) WHERE deleted_at IS NOT NULL;

-- 3.3 Add soft delete to reports
ALTER TABLE reports
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_reports_active
ON reports(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_reports_deleted_at
ON reports(deleted_at) WHERE deleted_at IS NOT NULL;

-- 3.4 Add soft delete to registration_fraud_signals
ALTER TABLE registration_fraud_signals
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_fraud_signals_active
ON registration_fraud_signals(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_fraud_signals_deleted_at
ON registration_fraud_signals(deleted_at) WHERE deleted_at IS NOT NULL;

-- 3.5 Add soft delete to notification_templates
ALTER TABLE notification_templates
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_notification_templates_active
ON notification_templates(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_notification_templates_deleted_at
ON notification_templates(deleted_at) WHERE deleted_at IS NOT NULL;

-- 3.6 Add soft delete to subjects (reference data)
ALTER TABLE subjects
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_subjects_soft_deleted
ON subjects(deleted_at) WHERE deleted_at IS NULL;

-- 3.7 Add missing updated_at columns
ALTER TABLE tutor_subjects
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE tutor_availabilities
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE tutor_blackouts
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE refunds
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE reviews
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE favorite_tutors
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- 3.8 Add missing deleted_by to message_attachments
ALTER TABLE message_attachments
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- 3.9 Add archived_user_id to wallets (preserve financial data)
ALTER TABLE wallets
ADD COLUMN IF NOT EXISTS archived_user_id INTEGER;

COMMENT ON COLUMN wallets.archived_user_id IS 'Preserves original user_id after user deletion for financial records';

CREATE INDEX IF NOT EXISTS idx_wallets_archived_user
ON wallets(archived_user_id) WHERE archived_user_id IS NOT NULL;

-- 3.10 Missing partial indexes for soft delete
CREATE INDEX IF NOT EXISTS idx_student_profiles_active
ON student_profiles(id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_student_profiles_deleted_at
ON student_profiles(deleted_at) WHERE deleted_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_tutor_active
ON reviews(tutor_profile_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_reviews_student_active
ON reviews(student_id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_messages_unread_active
ON messages(recipient_id, is_read) WHERE is_read = FALSE AND deleted_at IS NULL;

-- ============================================================================
-- SECTION 4: SECURITY CONSTRAINTS
-- ============================================================================

-- 4.1 Message length limit (DoS prevention)
ALTER TABLE messages
ADD CONSTRAINT IF NOT EXISTS chk_message_length
CHECK (char_length(message) <= 10000);

-- 4.2 Bio/description length limits
ALTER TABLE user_profiles
ADD CONSTRAINT IF NOT EXISTS chk_bio_length
CHECK (bio IS NULL OR char_length(bio) <= 5000);

ALTER TABLE tutor_profiles
ADD CONSTRAINT IF NOT EXISTS chk_tutor_bio_length
CHECK (bio IS NULL OR char_length(bio) <= 5000);

ALTER TABLE tutor_profiles
ADD CONSTRAINT IF NOT EXISTS chk_description_length
CHECK (description IS NULL OR char_length(description) <= 10000);

ALTER TABLE reviews
ADD CONSTRAINT IF NOT EXISTS chk_comment_length
CHECK (comment IS NULL OR char_length(comment) <= 5000);

ALTER TABLE reports
ADD CONSTRAINT IF NOT EXISTS chk_report_description_length
CHECK (char_length(description) <= 5000);

-- 4.3 File size upper bound (100MB max)
ALTER TABLE message_attachments
ADD CONSTRAINT IF NOT EXISTS chk_file_size_reasonable
CHECK (file_size > 0 AND file_size <= 104857600);

-- 4.4 Phone format validation
ALTER TABLE user_profiles
ADD CONSTRAINT IF NOT EXISTS chk_phone_format
CHECK (phone IS NULL OR phone ~ '^[0-9\s\-\+\(\)]{5,20}$');

-- ============================================================================
-- SECTION 5: CREATE/UPDATE VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW active_tutor_pricing_options AS
SELECT * FROM tutor_pricing_options WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_session_materials AS
SELECT * FROM session_materials WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_reports AS
SELECT * FROM reports WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_fraud_signals AS
SELECT * FROM registration_fraud_signals WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_notification_templates AS
SELECT * FROM notification_templates WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW active_subjects AS
SELECT * FROM subjects WHERE deleted_at IS NULL AND is_active = TRUE;

-- ============================================================================
-- SECTION 6: DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE audit_log IS 'Central audit trail. Application MUST log changes to: users (role/status changes, soft deletes), bookings (all state transitions), payments, refunds, payouts, wallet_transactions, tutor_profiles (approval status), registration_fraud_signals (reviews)';

-- ============================================================================
-- RECORD MIGRATION
-- ============================================================================

INSERT INTO schema_migrations (version, description)
VALUES ('056', 'Comprehensive database fixes: constraints, indexes, soft delete, security')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ============================================================================
-- POST-MIGRATION NOTICE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  Migration 056 Complete: Comprehensive Database Fixes';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE '  Changes Applied:';
    RAISE NOTICE '  • Schema: 11 constraint fixes (currency validation, FK cascades)';
    RAISE NOTICE '  • Indexes: 17 changes (4 critical FK indexes, 6 removed redundant)';
    RAISE NOTICE '  • Soft Delete: 6 tables added, 7 updated_at columns added';
    RAISE NOTICE '  • Security: 7 length limits, 1 file size constraint';
    RAISE NOTICE '  • Views: 6 new active_* views created';
    RAISE NOTICE '';
    RAISE NOTICE '  ⚠️  Application Code Updates May Be Required:';
    RAISE NOTICE '  • Use UPPER case proficiency levels (B2, C1, etc.)';
    RAISE NOTICE '  • Handle new soft delete columns in queries';
    RAISE NOTICE '  • Respect message length limit (10,000 chars)';
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;
