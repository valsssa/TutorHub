-- ============================================================================
-- Soft Deletes + Audit Trail Implementation
-- Operational maturity: data recovery, compliance, analytics
-- ============================================================================

-- Add soft delete columns to major tables
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE tutor_profiles 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE student_profiles 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE bookings 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE reviews 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE messages 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS deleted_by INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Create indexes for soft delete queries
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_deleted_at ON tutor_profiles(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_deleted_at ON bookings(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_reviews_deleted_at ON reviews(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_messages_deleted_at ON messages(deleted_at) WHERE deleted_at IS NULL;

-- ============================================================================
-- Audit Trail Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_address INET,
    user_agent TEXT,
    CONSTRAINT valid_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'SOFT_DELETE', 'RESTORE'))
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit_log(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);

COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all data changes';
COMMENT ON COLUMN audit_log.old_data IS 'JSON snapshot of record before change';
COMMENT ON COLUMN audit_log.new_data IS 'JSON snapshot of record after change';

-- ============================================================================
-- Audit Trigger Function
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_action VARCHAR(20);
BEGIN
    -- Determine action type
    IF (TG_OP = 'INSERT') THEN
        v_action := 'INSERT';
        v_old_data := NULL;
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Check if it's a soft delete
        IF (NEW.deleted_at IS NOT NULL AND OLD.deleted_at IS NULL) THEN
            v_action := 'SOFT_DELETE';
        -- Check if it's a restore
        ELSIF (NEW.deleted_at IS NULL AND OLD.deleted_at IS NOT NULL) THEN
            v_action := 'RESTORE';
        ELSE
            v_action := 'UPDATE';
        END IF;
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
    ELSIF (TG_OP = 'DELETE') THEN
        v_action := 'DELETE';
        v_old_data := to_jsonb(OLD);
        v_new_data := NULL;
    END IF;

    -- Insert audit record
    INSERT INTO audit_log (
        table_name,
        record_id,
        action,
        old_data,
        new_data,
        changed_by,
        changed_at
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        v_action,
        v_old_data,
        v_new_data,
        COALESCE(NEW.deleted_by, OLD.deleted_by, 
                 NULLIF(current_setting('app.current_user_id', TRUE), '')::INTEGER),
        CURRENT_TIMESTAMP
    );

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION audit_trigger_func() IS 
'Automatic audit logging for INSERT, UPDATE, DELETE, SOFT_DELETE, and RESTORE operations';

-- ============================================================================
-- Apply Audit Triggers to Major Tables
-- ============================================================================

-- Users table
DROP TRIGGER IF EXISTS audit_users_trigger ON users;
CREATE TRIGGER audit_users_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Tutor profiles
DROP TRIGGER IF EXISTS audit_tutor_profiles_trigger ON tutor_profiles;
CREATE TRIGGER audit_tutor_profiles_trigger
    AFTER INSERT OR UPDATE OR DELETE ON tutor_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Bookings
DROP TRIGGER IF EXISTS audit_bookings_trigger ON bookings;
CREATE TRIGGER audit_bookings_trigger
    AFTER INSERT OR UPDATE OR DELETE ON bookings
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Reviews
DROP TRIGGER IF EXISTS audit_reviews_trigger ON reviews;
CREATE TRIGGER audit_reviews_trigger
    AFTER INSERT OR UPDATE OR DELETE ON reviews
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Messages
DROP TRIGGER IF EXISTS audit_messages_trigger ON messages;
CREATE TRIGGER audit_messages_trigger
    AFTER INSERT OR UPDATE OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to soft delete a user
CREATE OR REPLACE FUNCTION soft_delete_user(
    p_user_id INTEGER,
    p_deleted_by INTEGER
) RETURNS VOID AS $$
BEGIN
    -- Set app context for audit
    PERFORM set_config('app.current_user_id', p_deleted_by::TEXT, TRUE);
    
    -- Soft delete user
    UPDATE users 
    SET deleted_at = CURRENT_TIMESTAMP,
        deleted_by = p_deleted_by,
        is_active = FALSE
    WHERE id = p_user_id
    AND deleted_at IS NULL;
    
    -- Cascade soft delete to related records
    UPDATE tutor_profiles 
    SET deleted_at = CURRENT_TIMESTAMP,
        deleted_by = p_deleted_by
    WHERE user_id = p_user_id
    AND deleted_at IS NULL;
    
    UPDATE student_profiles 
    SET deleted_at = CURRENT_TIMESTAMP,
        deleted_by = p_deleted_by
    WHERE user_id = p_user_id
    AND deleted_at IS NULL;
    
    RAISE NOTICE 'User % soft deleted by %', p_user_id, p_deleted_by;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to restore a soft-deleted user
CREATE OR REPLACE FUNCTION restore_user(
    p_user_id INTEGER,
    p_restored_by INTEGER
) RETURNS VOID AS $$
BEGIN
    -- Set app context for audit
    PERFORM set_config('app.current_user_id', p_restored_by::TEXT, TRUE);
    
    -- Restore user
    UPDATE users 
    SET deleted_at = NULL,
        deleted_by = NULL,
        is_active = TRUE
    WHERE id = p_user_id
    AND deleted_at IS NOT NULL;
    
    -- Restore related records
    UPDATE tutor_profiles 
    SET deleted_at = NULL,
        deleted_by = NULL
    WHERE user_id = p_user_id
    AND deleted_at IS NOT NULL;
    
    UPDATE student_profiles 
    SET deleted_at = NULL,
        deleted_by = NULL
    WHERE user_id = p_user_id
    AND deleted_at IS NOT NULL;
    
    RAISE NOTICE 'User % restored by %', p_user_id, p_restored_by;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to permanently delete old soft-deleted records (GDPR compliance)
CREATE OR REPLACE FUNCTION purge_old_soft_deletes(
    p_days_threshold INTEGER DEFAULT 90
) RETURNS TABLE (
    table_name TEXT,
    records_purged BIGINT
) AS $$
DECLARE
    v_cutoff_date TIMESTAMPTZ;
    v_deleted_count BIGINT;
BEGIN
    v_cutoff_date := CURRENT_TIMESTAMP - (p_days_threshold || ' days')::INTERVAL;
    
    -- Purge old users
    WITH deleted AS (
        DELETE FROM users
        WHERE deleted_at < v_cutoff_date
        AND deleted_at IS NOT NULL
        RETURNING *
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY SELECT 'users'::TEXT, v_deleted_count;
    
    -- Purge old bookings
    WITH deleted AS (
        DELETE FROM bookings
        WHERE deleted_at < v_cutoff_date
        AND deleted_at IS NOT NULL
        RETURNING *
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY SELECT 'bookings'::TEXT, v_deleted_count;
    
    -- Purge old reviews
    WITH deleted AS (
        DELETE FROM reviews
        WHERE deleted_at < v_cutoff_date
        AND deleted_at IS NOT NULL
        RETURNING *
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY SELECT 'reviews'::TEXT, v_deleted_count;
    
    -- Purge old messages
    WITH deleted AS (
        DELETE FROM messages
        WHERE deleted_at < v_cutoff_date
        AND deleted_at IS NOT NULL
        RETURNING *
    )
    SELECT COUNT(*) INTO v_deleted_count FROM deleted;
    
    RETURN QUERY SELECT 'messages'::TEXT, v_deleted_count;
    
    RAISE NOTICE 'Purged records older than % days', p_days_threshold;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION purge_old_soft_deletes IS 
'Permanently delete soft-deleted records older than threshold (default 90 days) for GDPR compliance';

-- ============================================================================
-- Views for Active Records Only
-- ============================================================================

-- View for active users only
CREATE OR REPLACE VIEW active_users AS
SELECT * FROM users WHERE deleted_at IS NULL;

-- View for active tutors only
CREATE OR REPLACE VIEW active_tutor_profiles AS
SELECT * FROM tutor_profiles WHERE deleted_at IS NULL;

-- View for active bookings only
CREATE OR REPLACE VIEW active_bookings AS
SELECT * FROM bookings WHERE deleted_at IS NULL;

COMMENT ON VIEW active_users IS 'Users excluding soft-deleted records';
COMMENT ON VIEW active_tutor_profiles IS 'Tutor profiles excluding soft-deleted records';
COMMENT ON VIEW active_bookings IS 'Bookings excluding soft-deleted records';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_audit_count BIGINT;
BEGIN
    -- Check audit log table
    SELECT COUNT(*) INTO v_audit_count FROM audit_log;
    
    RAISE NOTICE 'Soft delete migration completed';
    RAISE NOTICE '  - Audit log records: %', v_audit_count;
    RAISE NOTICE '  - Soft delete columns added to major tables';
    RAISE NOTICE '  - Audit triggers applied';
    RAISE NOTICE '  - Helper functions created (soft_delete_user, restore_user, purge_old_soft_deletes)';
    RAISE NOTICE '  - Views created for active records';
END $$;
