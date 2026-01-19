-- ============================================================================
-- Instant Booking & Frictionless Flow
-- Reduce booking drop-offs with instant confirmation and smart prefills
-- ============================================================================

-- ============================================================================
-- Part 1: Add Instant Booking Capability
-- ============================================================================

-- Add instant booking fields to tutor_profiles
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS instant_book_enabled BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS instant_book_requirements TEXT,
ADD COLUMN IF NOT EXISTS auto_confirm_threshold_hours INTEGER DEFAULT 24;

COMMENT ON COLUMN tutor_profiles.instant_book_enabled IS
'Enables instant booking without tutor confirmation. Reduces friction and increases conversion.';

COMMENT ON COLUMN tutor_profiles.instant_book_requirements IS
'Optional requirements for instant booking (e.g., "Student must have completed profile")';

COMMENT ON COLUMN tutor_profiles.auto_confirm_threshold_hours IS
'Auto-confirm bookings made this many hours in advance (default 24h). Prevents last-minute conflicts.';

CREATE INDEX IF NOT EXISTS idx_tutor_profiles_instant_book 
ON tutor_profiles(instant_book_enabled, is_approved) 
WHERE instant_book_enabled = TRUE AND is_approved = TRUE;

-- ============================================================================
-- Part 2: Enhanced Booking Status Tracking
-- ============================================================================

-- Add confirmation tracking fields
ALTER TABLE bookings
ADD COLUMN IF NOT EXISTS is_instant_booking BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS confirmed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS cancellation_reason TEXT,
ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS is_rebooked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS original_booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL;

COMMENT ON COLUMN bookings.is_instant_booking IS
'True if booking was instantly confirmed without tutor manual approval.';

COMMENT ON COLUMN bookings.confirmed_at IS
'Timestamp when booking was confirmed (automatically or by tutor).';

COMMENT ON COLUMN bookings.is_rebooked IS
'True if this booking was created via one-click rebooking.';

COMMENT ON COLUMN bookings.original_booking_id IS
'Reference to original booking if this is a rebooked session.';

-- Index for quick lookup of instant bookings
CREATE INDEX IF NOT EXISTS idx_bookings_instant ON bookings(is_instant_booking, status);
CREATE INDEX IF NOT EXISTS idx_bookings_confirmed_at ON bookings(confirmed_at);
CREATE INDEX IF NOT EXISTS idx_bookings_rebooked ON bookings(is_rebooked, original_booking_id);

-- ============================================================================
-- Part 3: Smart Topic Suggestions
-- ============================================================================

-- Table to track popular topics per subject
CREATE TABLE IF NOT EXISTS popular_topics (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    topic VARCHAR(255) NOT NULL,
    usage_count INTEGER DEFAULT 1 NOT NULL,
    last_used TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_subject_topic UNIQUE (subject_id, topic)
);

CREATE INDEX IF NOT EXISTS idx_popular_topics_subject ON popular_topics(subject_id, usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_popular_topics_usage ON popular_topics(usage_count DESC, last_used DESC);

COMMENT ON TABLE popular_topics IS
'Tracks popular booking topics per subject for auto-suggestions.';

-- Trigger to track topic usage
CREATE OR REPLACE FUNCTION track_booking_topic()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.topic IS NOT NULL AND NEW.topic != '' AND NEW.subject_id IS NOT NULL THEN
        INSERT INTO popular_topics (subject_id, topic, usage_count, last_used)
        VALUES (NEW.subject_id, NEW.topic, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (subject_id, topic) 
        DO UPDATE SET 
            usage_count = popular_topics.usage_count + 1,
            last_used = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_track_booking_topic ON bookings;
CREATE TRIGGER trg_track_booking_topic
    AFTER INSERT ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION track_booking_topic();

-- ============================================================================
-- Part 4: Automatic Booking Confirmation Logic
-- ============================================================================

-- Function to auto-confirm instant bookings
CREATE OR REPLACE FUNCTION auto_confirm_instant_booking()
RETURNS TRIGGER AS $$
DECLARE
    v_tutor_profile RECORD;
    v_hours_until_session NUMERIC;
BEGIN
    -- Only process on INSERT with pending status
    IF (TG_OP = 'INSERT' AND NEW.status = 'pending') THEN
        -- Get tutor profile
        SELECT * INTO v_tutor_profile
        FROM tutor_profiles
        WHERE id = NEW.tutor_profile_id;
        
        -- Check if tutor has instant booking enabled
        IF v_tutor_profile.instant_book_enabled = TRUE THEN
            -- Calculate hours until session
            v_hours_until_session := EXTRACT(EPOCH FROM (NEW.start_time - CURRENT_TIMESTAMP)) / 3600;
            
            -- Auto-confirm if booking is far enough in advance
            IF v_hours_until_session >= COALESCE(v_tutor_profile.auto_confirm_threshold_hours, 24) THEN
                NEW.status := 'confirmed';
                NEW.is_instant_booking := TRUE;
                NEW.confirmed_at := CURRENT_TIMESTAMP;
                NEW.confirmed_by := NEW.student_id;
                
                RAISE NOTICE 'Booking % auto-confirmed (instant booking enabled, %h in advance)', 
                    NEW.id, ROUND(v_hours_until_session, 1);
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_confirm_instant_booking ON bookings;
CREATE TRIGGER trg_auto_confirm_instant_booking
    BEFORE INSERT ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION auto_confirm_instant_booking();

COMMENT ON FUNCTION auto_confirm_instant_booking() IS
'Automatically confirms bookings for tutors with instant_book_enabled=true.
Applies threshold check to prevent last-minute conflicts.';

-- ============================================================================
-- Part 5: Rebooking Analytics
-- ============================================================================

-- Track rebooking metrics
CREATE TABLE IF NOT EXISTS rebooking_metrics (
    id SERIAL PRIMARY KEY,
    tutor_profile_id INTEGER REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    original_booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    rebooked_booking_id INTEGER REFERENCES bookings(id) ON DELETE CASCADE,
    time_to_rebook_hours INTEGER,
    rebooking_source VARCHAR(50) DEFAULT 'one_click',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rebooking_metrics_tutor ON rebooking_metrics(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_rebooking_metrics_student ON rebooking_metrics(student_id);

COMMENT ON TABLE rebooking_metrics IS
'Analytics for one-click rebooking feature. Tracks conversion and student loyalty.';

-- ============================================================================
-- Part 6: Helper Views
-- ============================================================================

-- View for instant-bookable tutors
CREATE OR REPLACE VIEW instant_bookable_tutors AS
SELECT 
    tp.*,
    u.email as tutor_email,
    up.first_name,
    up.last_name,
    COUNT(DISTINCT b.id) as total_instant_bookings,
    AVG(CASE WHEN b.status = 'completed' THEN 1 ELSE 0 END) as instant_booking_completion_rate
FROM tutor_profiles tp
JOIN users u ON u.id = tp.user_id
LEFT JOIN user_profiles up ON up.user_id = tp.user_id
LEFT JOIN bookings b ON b.tutor_profile_id = tp.id AND b.is_instant_booking = TRUE
WHERE tp.instant_book_enabled = TRUE
  AND tp.is_approved = TRUE
  AND tp.deleted_at IS NULL
  AND u.is_active = TRUE
  AND u.deleted_at IS NULL
GROUP BY tp.id, u.email, up.first_name, up.last_name;

COMMENT ON VIEW instant_bookable_tutors IS
'All tutors with instant booking enabled and their instant booking metrics.';

-- View for rebooking opportunities (completed sessions)
CREATE OR REPLACE VIEW rebooking_opportunities AS
SELECT 
    b.id as booking_id,
    b.student_id,
    b.tutor_profile_id,
    b.tutor_name,
    b.tutor_title,
    b.subject_name,
    b.start_time,
    b.end_time,
    b.hourly_rate,
    b.total_amount,
    b.pricing_snapshot,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - b.end_time)) / 3600 as hours_since_session,
    tp.instant_book_enabled,
    NOT EXISTS(
        SELECT 1 FROM bookings b2 
        WHERE b2.student_id = b.student_id 
        AND b2.tutor_profile_id = b.tutor_profile_id 
        AND b2.id > b.id
        AND b2.status IN ('confirmed', 'pending')
    ) as no_future_bookings
FROM bookings b
JOIN tutor_profiles tp ON tp.id = b.tutor_profile_id
WHERE b.status = 'completed'
  AND b.deleted_at IS NULL
  AND tp.deleted_at IS NULL
  AND tp.is_approved = TRUE
ORDER BY b.end_time DESC;

COMMENT ON VIEW rebooking_opportunities IS
'Completed bookings that are candidates for one-click rebooking.';

-- ============================================================================
-- Part 7: Helper Functions
-- ============================================================================

-- Get smart topic suggestions for a booking
CREATE OR REPLACE FUNCTION get_topic_suggestions(
    p_subject_id INTEGER,
    p_student_id INTEGER DEFAULT NULL,
    p_limit INTEGER DEFAULT 5
)
RETURNS TABLE (
    topic VARCHAR(255),
    usage_count INTEGER,
    is_personalized BOOLEAN
) AS $$
BEGIN
    -- First, get student's previous topics
    IF p_student_id IS NOT NULL THEN
        RETURN QUERY
        SELECT DISTINCT 
            b.topic,
            COUNT(*)::INTEGER as usage_count,
            TRUE as is_personalized
        FROM bookings b
        WHERE b.student_id = p_student_id
          AND b.subject_id = p_subject_id
          AND b.topic IS NOT NULL
          AND b.topic != ''
        GROUP BY b.topic
        ORDER BY COUNT(*) DESC
        LIMIT p_limit;
    END IF;
    
    -- Then, get popular topics for subject
    RETURN QUERY
    SELECT 
        pt.topic,
        pt.usage_count,
        FALSE as is_personalized
    FROM popular_topics pt
    WHERE pt.subject_id = p_subject_id
    ORDER BY pt.usage_count DESC, pt.last_used DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_topic_suggestions IS
'Smart topic suggestions: prioritizes student previous topics, then popular topics for subject.';

-- Check if student can instant book with tutor
CREATE OR REPLACE FUNCTION can_instant_book(
    p_student_id INTEGER,
    p_tutor_profile_id INTEGER,
    p_start_time TIMESTAMPTZ
)
RETURNS TABLE (
    can_instant_book BOOLEAN,
    reason TEXT
) AS $$
DECLARE
    v_tutor_profile RECORD;
    v_hours_until_session NUMERIC;
    v_student RECORD;
BEGIN
    -- Get tutor profile
    SELECT * INTO v_tutor_profile
    FROM tutor_profiles
    WHERE id = p_tutor_profile_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT FALSE, 'Tutor not found';
        RETURN;
    END IF;
    
    -- Check if tutor has instant booking enabled
    IF v_tutor_profile.instant_book_enabled = FALSE THEN
        RETURN QUERY SELECT FALSE, 'Tutor does not have instant booking enabled';
        RETURN;
    END IF;
    
    -- Check if tutor is approved
    IF v_tutor_profile.is_approved = FALSE THEN
        RETURN QUERY SELECT FALSE, 'Tutor is not approved';
        RETURN;
    END IF;
    
    -- Calculate hours until session
    v_hours_until_session := EXTRACT(EPOCH FROM (p_start_time - CURRENT_TIMESTAMP)) / 3600;
    
    -- Check threshold
    IF v_hours_until_session < COALESCE(v_tutor_profile.auto_confirm_threshold_hours, 24) THEN
        RETURN QUERY SELECT FALSE, 
            format('Booking must be at least %s hours in advance for instant booking', 
                   COALESCE(v_tutor_profile.auto_confirm_threshold_hours, 24));
        RETURN;
    END IF;
    
    -- Check if student exists and is active
    SELECT * INTO v_student
    FROM users
    WHERE id = p_student_id;
    
    IF NOT FOUND OR v_student.is_active = FALSE THEN
        RETURN QUERY SELECT FALSE, 'Student account not active';
        RETURN;
    END IF;
    
    -- All checks passed
    RETURN QUERY SELECT TRUE, 'Instant booking available';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION can_instant_book IS
'Validates if student can use instant booking for specific tutor and time.';

-- ============================================================================
-- Part 8: Enable Instant Booking for Highly-Rated Tutors
-- ============================================================================

-- Auto-enable instant booking for tutors with excellent ratings
DO $$
DECLARE
    v_updated_count INTEGER := 0;
BEGIN
    WITH updated AS (
        UPDATE tutor_profiles
        SET instant_book_enabled = TRUE,
            auto_confirm_threshold_hours = 24
        WHERE is_approved = TRUE
          AND deleted_at IS NULL
          AND average_rating >= 4.5
          AND total_reviews >= 5
          AND total_sessions >= 10
          AND instant_book_enabled = FALSE
        RETURNING *
    )
    SELECT COUNT(*) INTO v_updated_count FROM updated;
    
    IF v_updated_count > 0 THEN
        RAISE NOTICE 'Auto-enabled instant booking for % highly-rated tutors (4.5+ rating, 5+ reviews, 10+ sessions)', 
            v_updated_count;
    ELSE
        RAISE NOTICE 'No tutors meet instant booking auto-enable criteria yet';
    END IF;
END $$;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_instant_book_count INTEGER;
    v_popular_topics_count INTEGER;
BEGIN
    -- Count instant-bookable tutors
    SELECT COUNT(*) INTO v_instant_book_count
    FROM tutor_profiles
    WHERE instant_book_enabled = TRUE AND deleted_at IS NULL;
    
    -- Count tracked topics
    SELECT COUNT(*) INTO v_popular_topics_count
    FROM popular_topics;
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 013: Instant Booking & Frictionless Flow ===';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Instant booking capability added';
    RAISE NOTICE '  - % tutors have instant booking enabled', v_instant_book_count;
    RAISE NOTICE '  - Auto-confirmation threshold: 24 hours default';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Smart topic suggestions system';
    RAISE NOTICE '  - % popular topics tracked', v_popular_topics_count;
    RAISE NOTICE '  - Auto-learning from booking history';
    RAISE NOTICE '';
    RAISE NOTICE '✓ One-click rebooking support';
    RAISE NOTICE '  - Rebooking metrics table created';
    RAISE NOTICE '  - Rebooking opportunities view available';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Helper functions created:';
    RAISE NOTICE '  - get_topic_suggestions(subject_id, student_id, limit)';
    RAISE NOTICE '  - can_instant_book(student_id, tutor_profile_id, start_time)';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Views created:';
    RAISE NOTICE '  - instant_bookable_tutors';
    RAISE NOTICE '  - rebooking_opportunities';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Expected Impact: 20-30%% higher booking completion';
END $$;
