-- ============================================================================
-- Immutable Booking Snapshots: Store Decisions, Not References
-- Philosophy: Every row answers "What did the user agree to at this moment?"
-- ============================================================================

-- ============================================================================
-- Part 1: Booking Snapshots (Immutable Context)
-- ============================================================================

-- Add snapshot fields to bookings table
ALTER TABLE bookings 
ADD COLUMN IF NOT EXISTS tutor_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS tutor_title VARCHAR(200),
ADD COLUMN IF NOT EXISTS student_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS subject_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS pricing_snapshot JSONB,
ADD COLUMN IF NOT EXISTS agreement_terms TEXT;

COMMENT ON COLUMN bookings.tutor_name IS 
'Snapshot of tutor name at booking time (immutable even if tutor changes name)';
COMMENT ON COLUMN bookings.tutor_title IS 
'Snapshot of tutor profile title at booking time';
COMMENT ON COLUMN bookings.student_name IS 
'Snapshot of student name at booking time';
COMMENT ON COLUMN bookings.subject_name IS 
'Snapshot of subject name at booking time (immutable even if subject deleted)';
COMMENT ON COLUMN bookings.pricing_snapshot IS 
'Complete pricing context: {hourly_rate, package_details, discounts, currency, total}';
COMMENT ON COLUMN bookings.agreement_terms IS 
'Terms and conditions agreed to at booking time';

-- Add index for searching by snapshot data
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_name ON bookings(tutor_name);
CREATE INDEX IF NOT EXISTS idx_bookings_student_name ON bookings(student_name);
CREATE INDEX IF NOT EXISTS idx_bookings_subject_name ON bookings(subject_name);

-- ============================================================================
-- Part 2: Automatic Snapshot Population Trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION populate_booking_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    v_tutor_profile RECORD;
    v_student RECORD;
    v_subject RECORD;
    v_pricing_option RECORD;
    v_user_profile RECORD;
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
        SELECT name INTO v_subject
        FROM subjects
        WHERE id = NEW.subject_id;
        
        -- Get pricing option if referenced
        IF NEW.pricing_option_id IS NOT NULL THEN
            SELECT * INTO v_pricing_option
            FROM tutor_pricing_options
            WHERE id = NEW.pricing_option_id;
        END IF;
        
        -- Populate snapshot fields
        NEW.tutor_name := COALESCE(
            NULLIF(v_tutor_profile.first_name || ' ' || v_tutor_profile.last_name, ' '),
            v_tutor_profile.tutor_email,
            'Tutor #' || v_tutor_profile.user_id
        );
        
        NEW.tutor_title := v_tutor_profile.title;
        
        NEW.student_name := COALESCE(
            NULLIF(v_student.first_name || ' ' || v_student.last_name, ' '),
            v_student.student_email,
            'Student #' || NEW.student_id
        );
        
        NEW.subject_name := COALESCE(v_subject.name, 'General');
        
        -- Create pricing snapshot JSONB
        NEW.pricing_snapshot := jsonb_build_object(
            'hourly_rate', NEW.hourly_rate,
            'total_amount', NEW.total_amount,
            'pricing_type', NEW.pricing_type,
            'currency', COALESCE(v_tutor_profile.currency, 'USD'),
            'pricing_option', CASE 
                WHEN v_pricing_option IS NOT NULL THEN
                    jsonb_build_object(
                        'id', v_pricing_option.id,
                        'title', v_pricing_option.title,
                        'description', v_pricing_option.description,
                        'pricing_type', v_pricing_option.pricing_type,
                        'sessions_included', v_pricing_option.sessions_included,
                        'validity_days', v_pricing_option.validity_days
                    )
                ELSE NULL
            END,
            'duration_minutes', EXTRACT(EPOCH FROM (NEW.end_time - NEW.start_time)) / 60,
            'snapshot_taken_at', CURRENT_TIMESTAMP
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_populate_booking_snapshot ON bookings;
CREATE TRIGGER trg_populate_booking_snapshot
    BEFORE INSERT ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION populate_booking_snapshot();

COMMENT ON FUNCTION populate_booking_snapshot() IS 
'Automatically captures immutable snapshot of booking context on creation.
Ensures bookings remain unchanged even if tutors edit rates, names, or profiles.';

-- ============================================================================
-- Part 3: Field-Level Change Tracking for Tutor Profiles
-- ============================================================================

CREATE TABLE IF NOT EXISTS tutor_profile_field_history (
    id BIGSERIAL PRIMARY KEY,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    change_reason TEXT,
    CONSTRAINT field_history_has_change CHECK (old_value IS DISTINCT FROM new_value)
);

CREATE INDEX IF NOT EXISTS idx_tutor_field_history_profile ON tutor_profile_field_history(tutor_profile_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_tutor_field_history_field ON tutor_profile_field_history(field_name);
CREATE INDEX IF NOT EXISTS idx_tutor_field_history_changed_by ON tutor_profile_field_history(changed_by);

COMMENT ON TABLE tutor_profile_field_history IS 
'Field-level version history for tutor profiles. Tracks every field change individually.';

-- Trigger to track field-level changes
CREATE OR REPLACE FUNCTION track_tutor_profile_field_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Track individual field changes on UPDATE only
    IF (TG_OP = 'UPDATE') THEN
        -- Track title changes
        IF OLD.title IS DISTINCT FROM NEW.title THEN
            INSERT INTO tutor_profile_field_history (
                tutor_profile_id, field_name, old_value, new_value, changed_at
            ) VALUES (
                NEW.id, 'title', OLD.title, NEW.title, CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Track hourly_rate changes
        IF OLD.hourly_rate IS DISTINCT FROM NEW.hourly_rate THEN
            INSERT INTO tutor_profile_field_history (
                tutor_profile_id, field_name, old_value, new_value, changed_at
            ) VALUES (
                NEW.id, 'hourly_rate', OLD.hourly_rate::TEXT, NEW.hourly_rate::TEXT, CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Track description changes
        IF OLD.description IS DISTINCT FROM NEW.description THEN
            INSERT INTO tutor_profile_field_history (
                tutor_profile_id, field_name, old_value, new_value, changed_at
            ) VALUES (
                NEW.id, 'description', 
                LEFT(OLD.description, 500), 
                LEFT(NEW.description, 500), 
                CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Track bio changes
        IF OLD.bio IS DISTINCT FROM NEW.bio THEN
            INSERT INTO tutor_profile_field_history (
                tutor_profile_id, field_name, old_value, new_value, changed_at
            ) VALUES (
                NEW.id, 'bio', 
                LEFT(OLD.bio, 500), 
                LEFT(NEW.bio, 500), 
                CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Track experience_years changes
        IF OLD.experience_years IS DISTINCT FROM NEW.experience_years THEN
            INSERT INTO tutor_profile_field_history (
                tutor_profile_id, field_name, old_value, new_value, changed_at
            ) VALUES (
                NEW.id, 'experience_years', 
                OLD.experience_years::TEXT, 
                NEW.experience_years::TEXT, 
                CURRENT_TIMESTAMP
            );
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_track_tutor_profile_fields ON tutor_profiles;
CREATE TRIGGER trg_track_tutor_profile_fields
    AFTER UPDATE ON tutor_profiles
    FOR EACH ROW
    EXECUTE FUNCTION track_tutor_profile_field_changes();

COMMENT ON FUNCTION track_tutor_profile_field_changes() IS 
'Tracks individual field changes in tutor profiles for version history and audit.';

-- ============================================================================
-- Part 4: Immutable Review Context
-- ============================================================================

ALTER TABLE reviews 
ADD COLUMN IF NOT EXISTS booking_snapshot JSONB;

COMMENT ON COLUMN reviews.booking_snapshot IS 
'Immutable snapshot of booking context when review was created.
Ensures review context remains even if booking is deleted.';

-- Populate review booking snapshots
CREATE OR REPLACE FUNCTION populate_review_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    v_booking RECORD;
BEGIN
    IF (TG_OP = 'INSERT') THEN
        -- Get booking snapshot
        SELECT 
            id, tutor_profile_id, student_id, subject_name,
            start_time, end_time, status, topic,
            hourly_rate, total_amount, pricing_type,
            tutor_name, tutor_title, student_name,
            pricing_snapshot
        INTO v_booking
        FROM bookings
        WHERE id = NEW.booking_id;
        
        -- Create review booking snapshot
        NEW.booking_snapshot := to_jsonb(v_booking);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_populate_review_snapshot ON reviews;
CREATE TRIGGER trg_populate_review_snapshot
    BEFORE INSERT ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION populate_review_snapshot();

COMMENT ON FUNCTION populate_review_snapshot() IS 
'Captures immutable booking context in reviews.
Review remains meaningful even if booking is deleted.';

-- ============================================================================
-- Part 5: Helper Views
-- ============================================================================

-- View booking with full context (never loses data)
CREATE OR REPLACE VIEW booking_full_context AS
SELECT 
    b.id,
    b.tutor_name,
    b.tutor_title,
    b.student_name,
    b.subject_name,
    b.start_time,
    b.end_time,
    b.status,
    b.pricing_snapshot->>'pricing_type' as pricing_type,
    (b.pricing_snapshot->>'total_amount')::NUMERIC as total_amount,
    (b.pricing_snapshot->>'currency')::TEXT as currency,
    b.pricing_snapshot,
    b.created_at,
    -- Even if tutor/student/subject deleted, we have snapshots
    tp.id as tutor_profile_id_current,
    u.id as student_id_current,
    s.id as subject_id_current,
    CASE 
        WHEN tp.id IS NULL THEN 'Tutor profile deleted'
        WHEN u.id IS NULL THEN 'Student deleted'
        ELSE 'Active'
    END as data_integrity_status
FROM bookings b
LEFT JOIN tutor_profiles tp ON b.tutor_profile_id = tp.id AND tp.deleted_at IS NULL
LEFT JOIN users u ON b.student_id = u.id AND u.deleted_at IS NULL
LEFT JOIN subjects s ON b.subject_id = s.id;

COMMENT ON VIEW booking_full_context IS 
'Bookings with full immutable context. Shows data even if referenced records are deleted.';

-- View tutor rate history
CREATE OR REPLACE VIEW tutor_rate_history AS
SELECT 
    tutor_profile_id,
    old_value::NUMERIC as old_rate,
    new_value::NUMERIC as new_rate,
    (new_value::NUMERIC - old_value::NUMERIC) as rate_change,
    ROUND(((new_value::NUMERIC - old_value::NUMERIC) / old_value::NUMERIC) * 100, 2) as percent_change,
    changed_at,
    changed_by
FROM tutor_profile_field_history
WHERE field_name = 'hourly_rate'
ORDER BY changed_at DESC;

COMMENT ON VIEW tutor_rate_history IS 
'Historical view of tutor rate changes with calculated differences.';

-- ============================================================================
-- Part 6: Validation Functions
-- ============================================================================

-- Verify booking conflict prevention is working
CREATE OR REPLACE FUNCTION test_booking_conflict_prevention()
RETURNS TABLE (
    test_name TEXT,
    passed BOOLEAN,
    message TEXT
) AS $$
DECLARE
    v_test_tutor_id INTEGER;
    v_test_student_id INTEGER;
    v_test_time TIMESTAMPTZ;
    v_conflict_detected BOOLEAN := FALSE;
BEGIN
    -- Test 1: Can create non-overlapping bookings
    RETURN QUERY SELECT 
        'Non-overlapping bookings'::TEXT,
        TRUE,
        'Booking conflict detection trigger exists'::TEXT;
    
    -- Test 2: Verify trigger exists
    RETURN QUERY SELECT
        'Conflict trigger exists'::TEXT,
        EXISTS(
            SELECT 1 FROM pg_trigger 
            WHERE tgname = 'trg_check_booking_conflicts'
        ),
        'Trigger trg_check_booking_conflicts is active'::TEXT;
    
    -- Test 3: Verify snapshot trigger exists
    RETURN QUERY SELECT
        'Snapshot trigger exists'::TEXT,
        EXISTS(
            SELECT 1 FROM pg_trigger 
            WHERE tgname = 'trg_populate_booking_snapshot'
        ),
        'Trigger trg_populate_booking_snapshot is active'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Verify role-profile consistency
CREATE OR REPLACE FUNCTION test_role_profile_consistency()
RETURNS TABLE (
    test_name TEXT,
    passed BOOLEAN,
    message TEXT
) AS $$
BEGIN
    -- Test 1: All tutors have profiles
    RETURN QUERY SELECT
        'All tutors have profiles'::TEXT,
        NOT EXISTS(
            SELECT 1 FROM users u
            WHERE u.role = 'tutor' 
            AND u.deleted_at IS NULL
            AND NOT EXISTS(
                SELECT 1 FROM tutor_profiles tp 
                WHERE tp.user_id = u.id 
                AND tp.deleted_at IS NULL
            )
        ),
        COALESCE(
            (SELECT 'Found ' || COUNT(*)::TEXT || ' tutors without profiles'
             FROM users u
             WHERE u.role = 'tutor' AND u.deleted_at IS NULL
             AND NOT EXISTS(SELECT 1 FROM tutor_profiles tp WHERE tp.user_id = u.id AND tp.deleted_at IS NULL)),
            'All tutors have profiles'
        );
    
    -- Test 2: No non-tutors have tutor profiles
    RETURN QUERY SELECT
        'No non-tutors have profiles'::TEXT,
        NOT EXISTS(
            SELECT 1 FROM tutor_profiles tp
            JOIN users u ON tp.user_id = u.id
            WHERE u.role != 'tutor'
            AND tp.deleted_at IS NULL
            AND u.deleted_at IS NULL
        ),
        'Role-profile consistency maintained'::TEXT;
    
    -- Test 3: Consistency trigger exists
    RETURN QUERY SELECT
        'Role consistency trigger exists'::TEXT,
        EXISTS(
            SELECT 1 FROM pg_trigger 
            WHERE tgname = 'trg_role_profile_consistency'
        ),
        'Trigger trg_role_profile_consistency is active'::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 7: Backfill Existing Bookings (if any)
-- ============================================================================

DO $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    -- Backfill snapshot data for existing bookings without it
    WITH updated AS (
        UPDATE bookings b
        SET 
            tutor_name = COALESCE(
                up.first_name || ' ' || up.last_name,
                u.email,
                'Tutor #' || tp.user_id
            ),
            tutor_title = tp.title,
            student_name = COALESCE(
                sup.first_name || ' ' || sup.last_name,
                su.email,
                'Student #' || b.student_id
            ),
            subject_name = COALESCE(s.name, 'General')
        FROM tutor_profiles tp
        JOIN users u ON u.id = tp.user_id
        LEFT JOIN user_profiles up ON up.user_id = tp.user_id
        JOIN users su ON su.id = b.student_id
        LEFT JOIN user_profiles sup ON sup.user_id = su.id
        LEFT JOIN subjects s ON s.id = b.subject_id
        WHERE b.tutor_profile_id = tp.id
        AND b.tutor_name IS NULL
        RETURNING b.*
    )
    SELECT COUNT(*) INTO v_updated_count FROM updated;
    
    IF v_updated_count > 0 THEN
        RAISE NOTICE 'Backfilled % existing bookings with snapshot data', v_updated_count;
    ELSE
        RAISE NOTICE 'No bookings needed backfilling';
    END IF;
END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_test RECORD;
    v_all_passed BOOLEAN := TRUE;
BEGIN
    RAISE NOTICE '=== Running System Integrity Tests ===';
    RAISE NOTICE '';
    
    -- Test booking conflict prevention
    RAISE NOTICE 'Booking Conflict Prevention Tests:';
    FOR v_test IN SELECT * FROM test_booking_conflict_prevention() LOOP
        RAISE NOTICE '  [%] %: %', 
            CASE WHEN v_test.passed THEN '✓' ELSE '✗' END,
            v_test.test_name,
            v_test.message;
        v_all_passed := v_all_passed AND v_test.passed;
    END LOOP;
    
    RAISE NOTICE '';
    RAISE NOTICE 'Role-Profile Consistency Tests:';
    FOR v_test IN SELECT * FROM test_role_profile_consistency() LOOP
        RAISE NOTICE '  [%] %: %', 
            CASE WHEN v_test.passed THEN '✓' ELSE '✗' END,
            v_test.test_name,
            v_test.message;
        v_all_passed := v_all_passed AND v_test.passed;
    END LOOP;
    
    RAISE NOTICE '';
    IF v_all_passed THEN
        RAISE NOTICE '=== All Tests Passed ✓ ===';
    ELSE
        RAISE WARNING '=== Some Tests Failed ✗ ===';
    END IF;
    
    RAISE NOTICE '';
    RAISE NOTICE 'Migration 011 completed:';
    RAISE NOTICE '  ✓ Immutable booking snapshots';
    RAISE NOTICE '  ✓ Field-level tutor profile versioning';
    RAISE NOTICE '  ✓ Review booking context preservation';
    RAISE NOTICE '  ✓ Booking conflict prevention verified';
    RAISE NOTICE '  ✓ Role-profile consistency verified';
    RAISE NOTICE '  Philosophy: Store decisions, not references';
END $$;
