-- ============================================================================
-- Fix CASCADE DELETE: Preserve Booking History
-- Philosophy: "Never lose what a user agreed to"
-- ============================================================================

-- PROBLEM: Current schema has ON DELETE CASCADE for bookings table
-- This means if a tutor deletes their profile, all booking history is lost
-- SOLUTION: Change to SET NULL + rely on immutable snapshots

-- ============================================================================
-- Part 1: Fix Bookings Table Foreign Keys
-- ============================================================================

-- Drop existing foreign key constraints that use CASCADE
ALTER TABLE bookings 
DROP CONSTRAINT IF EXISTS bookings_tutor_profile_id_fkey;

ALTER TABLE bookings 
DROP CONSTRAINT IF EXISTS bookings_student_id_fkey;

-- Re-add with SET NULL (data preserved in snapshot fields)
ALTER TABLE bookings
ADD CONSTRAINT bookings_tutor_profile_id_fkey 
FOREIGN KEY (tutor_profile_id) 
REFERENCES tutor_profiles(id) 
ON DELETE SET NULL;

ALTER TABLE bookings
ADD CONSTRAINT bookings_student_id_fkey 
FOREIGN KEY (student_id) 
REFERENCES users(id) 
ON DELETE SET NULL;

COMMENT ON CONSTRAINT bookings_tutor_profile_id_fkey ON bookings IS
'SET NULL preserves booking history. Tutor name/rate stored in snapshot fields.';

COMMENT ON CONSTRAINT bookings_student_id_fkey ON bookings IS
'SET NULL preserves booking history. Student name stored in snapshot fields.';

-- ============================================================================
-- Part 2: Fix Reviews Table Foreign Keys
-- ============================================================================

-- Reviews should never lose context, even if booking is deleted
ALTER TABLE reviews
DROP CONSTRAINT IF EXISTS reviews_booking_id_fkey;

ALTER TABLE reviews
ADD CONSTRAINT reviews_booking_id_fkey
FOREIGN KEY (booking_id)
REFERENCES bookings(id)
ON DELETE SET NULL;

ALTER TABLE reviews
DROP CONSTRAINT IF EXISTS reviews_tutor_profile_id_fkey;

ALTER TABLE reviews
ADD CONSTRAINT reviews_tutor_profile_id_fkey
FOREIGN KEY (tutor_profile_id)
REFERENCES tutor_profiles(id)
ON DELETE SET NULL;

ALTER TABLE reviews
DROP CONSTRAINT IF EXISTS reviews_student_id_fkey;

ALTER TABLE reviews
ADD CONSTRAINT reviews_student_id_fkey
FOREIGN KEY (student_id)
REFERENCES users(id)
ON DELETE SET NULL;

COMMENT ON CONSTRAINT reviews_booking_id_fkey ON reviews IS
'SET NULL preserves review context. Booking details stored in booking_snapshot.';

-- ============================================================================
-- Part 3: Fix Messages Table
-- ============================================================================

-- Messages should preserve context even if booking deleted
ALTER TABLE messages
DROP CONSTRAINT IF EXISTS messages_booking_id_fkey;

ALTER TABLE messages
ADD CONSTRAINT messages_booking_id_fkey
FOREIGN KEY (booking_id)
REFERENCES bookings(id)
ON DELETE SET NULL;

-- ============================================================================
-- Part 4: Add Pricing Option to Bookings (if not exists)
-- ============================================================================

-- Ensure pricing_option_id is properly nullable
ALTER TABLE bookings
ALTER COLUMN pricing_option_id DROP NOT NULL;

ALTER TABLE bookings
DROP CONSTRAINT IF EXISTS bookings_pricing_option_id_fkey;

ALTER TABLE bookings
ADD CONSTRAINT bookings_pricing_option_id_fkey
FOREIGN KEY (pricing_option_id)
REFERENCES tutor_pricing_options(id)
ON DELETE SET NULL;

-- ============================================================================
-- Part 5: Add Pricing Type Field (if not exists)
-- ============================================================================

ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS pricing_type VARCHAR(20) DEFAULT 'hourly';

COMMENT ON COLUMN bookings.pricing_type IS
'Type of pricing: hourly, package, custom. Captured at booking time.';

-- ============================================================================
-- Part 6: Ensure Snapshot Fields are NOT NULL after creation
-- ============================================================================

-- Update trigger to ensure snapshot fields are always populated
CREATE OR REPLACE FUNCTION populate_booking_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    v_tutor_profile RECORD;
    v_student RECORD;
    v_subject RECORD;
    v_pricing_option RECORD;
BEGIN
    -- Only populate on INSERT (immutable snapshots)
    IF (TG_OP = 'INSERT') THEN
        -- Get tutor profile
        SELECT tp.*, u.email as tutor_email, up.first_name, up.last_name
        INTO v_tutor_profile
        FROM tutor_profiles tp
        JOIN users u ON u.id = tp.user_id
        LEFT JOIN user_profiles up ON up.user_id = tp.user_id
        WHERE tp.id = NEW.tutor_profile_id;
        
        -- Get student info
        SELECT u.email as student_email, up.first_name, up.last_name
        INTO v_student
        FROM users u
        LEFT JOIN user_profiles up ON up.user_id = u.id
        WHERE u.id = NEW.student_id;
        
        -- Get subject name
        IF NEW.subject_id IS NOT NULL THEN
            SELECT name INTO v_subject
            FROM subjects
            WHERE id = NEW.subject_id;
        END IF;
        
        -- Get pricing option if referenced
        IF NEW.pricing_option_id IS NOT NULL THEN
            SELECT * INTO v_pricing_option
            FROM tutor_pricing_options
            WHERE id = NEW.pricing_option_id;
        END IF;
        
        -- Populate snapshot fields
        NEW.tutor_name := COALESCE(
            NULLIF(TRIM(v_tutor_profile.first_name || ' ' || v_tutor_profile.last_name), ''),
            v_tutor_profile.tutor_email,
            'Tutor #' || NEW.tutor_profile_id
        );
        
        NEW.tutor_title := COALESCE(v_tutor_profile.title, 'Tutor');
        
        NEW.student_name := COALESCE(
            NULLIF(TRIM(v_student.first_name || ' ' || v_student.last_name), ''),
            v_student.student_email,
            'Student #' || NEW.student_id
        );
        
        NEW.subject_name := COALESCE(v_subject.name, 'General Tutoring');
        
        -- Create comprehensive pricing snapshot JSONB
        NEW.pricing_snapshot := jsonb_build_object(
            'hourly_rate', NEW.hourly_rate,
            'total_amount', NEW.total_amount,
            'pricing_type', COALESCE(NEW.pricing_type, 'hourly'),
            'currency', COALESCE(v_tutor_profile.currency, 'USD'),
            'pricing_option', CASE 
                WHEN v_pricing_option IS NOT NULL THEN
                    jsonb_build_object(
                        'id', v_pricing_option.id,
                        'title', v_pricing_option.title,
                        'description', v_pricing_option.description,
                        'duration_minutes', v_pricing_option.duration_minutes,
                        'price', v_pricing_option.price
                    )
                ELSE NULL
            END,
            'duration_minutes', EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) / 60,
            'snapshot_taken_at', CURRENT_TIMESTAMP,
            'tutor_hourly_rate_at_booking', NEW.hourly_rate,
            'tutor_currency', COALESCE(v_tutor_profile.currency, 'USD')
        );
        
        -- Set agreement terms
        NEW.agreement_terms := format(
            'Booking Agreement: %s (%s) will tutor %s for %s on %s. Rate: %s %s/hour. Total: %s %s',
            NEW.tutor_name,
            NEW.tutor_title,
            NEW.student_name,
            NEW.subject_name,
            to_char(NEW.start_time, 'YYYY-MM-DD HH24:MI TZ'),
            NEW.hourly_rate,
            COALESCE(v_tutor_profile.currency, 'USD'),
            NEW.total_amount,
            COALESCE(v_tutor_profile.currency, 'USD')
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION populate_booking_snapshot() IS 
'Captures complete immutable snapshot of booking agreement.
Ensures booking history preserved even if tutor/student/subject deleted.';

-- Re-create trigger to use updated function
DROP TRIGGER IF EXISTS trg_populate_booking_snapshot ON bookings;
CREATE TRIGGER trg_populate_booking_snapshot
    BEFORE INSERT ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION populate_booking_snapshot();

-- ============================================================================
-- Part 7: Enhanced View for Booking History
-- ============================================================================

CREATE OR REPLACE VIEW booking_complete_history AS
SELECT 
    b.id,
    b.tutor_name,
    b.tutor_title,
    b.student_name,
    b.subject_name,
    b.start_time,
    b.end_time,
    b.status,
    b.hourly_rate,
    b.total_amount,
    b.pricing_type,
    b.pricing_snapshot,
    b.agreement_terms,
    b.created_at,
    b.deleted_at,
    -- Current state (may be NULL if deleted)
    tp.id as current_tutor_profile_id,
    u.id as current_student_id,
    s.id as current_subject_id,
    -- Data integrity indicators
    CASE 
        WHEN b.tutor_profile_id IS NULL THEN 'Tutor removed'
        WHEN tp.deleted_at IS NOT NULL THEN 'Tutor soft-deleted'
        WHEN tp.id IS NULL THEN 'Tutor not found'
        ELSE 'Tutor active'
    END as tutor_status,
    CASE 
        WHEN b.student_id IS NULL THEN 'Student removed'
        WHEN u.deleted_at IS NOT NULL THEN 'Student soft-deleted'
        WHEN u.id IS NULL THEN 'Student not found'
        ELSE 'Student active'
    END as student_status,
    CASE 
        WHEN b.subject_id IS NULL THEN 'No subject linked'
        WHEN s.id IS NULL THEN 'Subject deleted'
        ELSE 'Subject active'
    END as subject_status,
    -- Extract currency from snapshot
    b.pricing_snapshot->>'currency' as currency
FROM bookings b
LEFT JOIN tutor_profiles tp ON b.tutor_profile_id = tp.id
LEFT JOIN users u ON b.student_id = u.id
LEFT JOIN subjects s ON b.subject_id = s.id;

COMMENT ON VIEW booking_complete_history IS 
'Complete booking history with snapshot preservation.
Shows all bookings even if tutor/student/subject deleted.
Answers: "What did they agree to?" not "What exists now?"';

-- ============================================================================
-- Part 8: Query Helper Functions
-- ============================================================================

-- Get booking history even if parties deleted
CREATE OR REPLACE FUNCTION get_booking_history(
    p_user_id INTEGER DEFAULT NULL,
    p_role VARCHAR(20) DEFAULT NULL,
    p_include_deleted BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    booking_id INTEGER,
    tutor_name VARCHAR(200),
    student_name VARCHAR(200),
    subject_name VARCHAR(100),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status VARCHAR(20),
    total_amount NUMERIC,
    currency TEXT,
    agreement_terms TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.id,
        b.tutor_name,
        b.student_name,
        b.subject_name,
        b.start_time,
        b.end_time,
        b.status,
        b.total_amount,
        b.pricing_snapshot->>'currency',
        b.agreement_terms
    FROM bookings b
    WHERE 
        (p_include_deleted OR b.deleted_at IS NULL)
        AND (
            p_user_id IS NULL 
            OR b.student_id = p_user_id
            OR b.tutor_profile_id IN (
                SELECT id FROM tutor_profiles WHERE user_id = p_user_id
            )
        )
    ORDER BY b.created_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_booking_history IS
'Get complete booking history for a user, preserving deleted records via snapshots.';

-- ============================================================================
-- Part 9: Data Integrity Checks
-- ============================================================================

-- Check for bookings missing snapshot data
CREATE OR REPLACE FUNCTION check_booking_snapshot_integrity()
RETURNS TABLE (
    issue TEXT,
    booking_count BIGINT
) AS $$
BEGIN
    -- Check for missing tutor names
    RETURN QUERY
    SELECT 
        'Bookings missing tutor_name'::TEXT,
        COUNT(*)::BIGINT
    FROM bookings
    WHERE tutor_name IS NULL AND deleted_at IS NULL;
    
    -- Check for missing student names
    RETURN QUERY
    SELECT 
        'Bookings missing student_name'::TEXT,
        COUNT(*)::BIGINT
    FROM bookings
    WHERE student_name IS NULL AND deleted_at IS NULL;
    
    -- Check for missing subject names
    RETURN QUERY
    SELECT 
        'Bookings missing subject_name'::TEXT,
        COUNT(*)::BIGINT
    FROM bookings
    WHERE subject_name IS NULL AND deleted_at IS NULL;
    
    -- Check for missing pricing snapshots
    RETURN QUERY
    SELECT 
        'Bookings missing pricing_snapshot'::TEXT,
        COUNT(*)::BIGINT
    FROM bookings
    WHERE pricing_snapshot IS NULL AND deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 10: Backfill Existing Bookings
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER := 0;
    v_total_count INTEGER := 0;
BEGIN
    -- Count bookings needing backfill
    SELECT COUNT(*) INTO v_total_count
    FROM bookings
    WHERE (
        tutor_name IS NULL 
        OR student_name IS NULL 
        OR subject_name IS NULL 
        OR pricing_snapshot IS NULL
    )
    AND deleted_at IS NULL;
    
    IF v_total_count > 0 THEN
        RAISE NOTICE 'Found % bookings needing snapshot backfill', v_total_count;
        
        -- Backfill snapshot data
        WITH updated AS (
            UPDATE bookings b
            SET 
                tutor_name = COALESCE(
                    b.tutor_name,
                    NULLIF(TRIM(up.first_name || ' ' || up.last_name), ''),
                    u.email,
                    'Tutor #' || b.tutor_profile_id
                ),
                tutor_title = COALESCE(b.tutor_title, tp.title, 'Tutor'),
                student_name = COALESCE(
                    b.student_name,
                    NULLIF(TRIM(sup.first_name || ' ' || sup.last_name), ''),
                    su.email,
                    'Student #' || b.student_id
                ),
                subject_name = COALESCE(b.subject_name, s.name, 'General Tutoring'),
                pricing_snapshot = COALESCE(
                    b.pricing_snapshot,
                    jsonb_build_object(
                        'hourly_rate', b.hourly_rate,
                        'total_amount', b.total_amount,
                        'pricing_type', COALESCE(b.pricing_type, 'hourly'),
                        'currency', COALESCE(tp.currency, 'USD'),
                        'duration_minutes', EXTRACT(EPOCH FROM (b.end_time - b.start_time)) / 60,
                        'snapshot_taken_at', CURRENT_TIMESTAMP,
                        'backfilled', TRUE
                    )
                )
            FROM tutor_profiles tp
            JOIN users u ON u.id = tp.user_id
            LEFT JOIN user_profiles up ON up.user_id = tp.user_id
            JOIN users su ON su.id = b.student_id
            LEFT JOIN user_profiles sup ON sup.user_id = su.id
            LEFT JOIN subjects s ON s.id = b.subject_id
            WHERE b.tutor_profile_id = tp.id
            AND b.deleted_at IS NULL
            AND (
                b.tutor_name IS NULL 
                OR b.student_name IS NULL 
                OR b.subject_name IS NULL 
                OR b.pricing_snapshot IS NULL
            )
            RETURNING b.*
        )
        SELECT COUNT(*) INTO v_updated_count FROM updated;
        
        RAISE NOTICE '✓ Backfilled % bookings with snapshot data', v_updated_count;
    ELSE
        RAISE NOTICE '✓ All bookings have complete snapshot data';
    END IF;
END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_check RECORD;
    v_issues_found BOOLEAN := FALSE;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 012: Fix CASCADE DELETE ===';
    RAISE NOTICE '';
    RAISE NOTICE 'Checking booking snapshot integrity...';
    
    FOR v_check IN SELECT * FROM check_booking_snapshot_integrity() LOOP
        IF v_check.booking_count > 0 THEN
            RAISE WARNING '  ⚠ %: %', v_check.issue, v_check.booking_count;
            v_issues_found := TRUE;
        ELSE
            RAISE NOTICE '  ✓ %: %', v_check.issue, v_check.booking_count;
        END IF;
    END LOOP;
    
    RAISE NOTICE '';
    IF NOT v_issues_found THEN
        RAISE NOTICE '✓ All booking snapshots complete';
    ELSE
        RAISE WARNING '⚠ Some bookings missing snapshot data (see above)';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Changes Applied ===';
    RAISE NOTICE '  ✓ Bookings preserve history (SET NULL instead of CASCADE)';
    RAISE NOTICE '  ✓ Reviews preserve context even if booking deleted';
    RAISE NOTICE '  ✓ Messages preserve booking reference';
    RAISE NOTICE '  ✓ Enhanced snapshot trigger with complete context';
    RAISE NOTICE '  ✓ booking_complete_history view created';
    RAISE NOTICE '  ✓ Helper functions: get_booking_history(), check_booking_snapshot_integrity()';
    RAISE NOTICE '';
    RAISE NOTICE 'Philosophy: "Never lose what a user agreed to"';
END $$;
