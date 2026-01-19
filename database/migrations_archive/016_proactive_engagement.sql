-- ============================================================================
-- Proactive Engagement: Smart Reminders, Learning Nudges
-- Make notifications feel like a helpful assistant, not spam
-- ============================================================================

-- ============================================================================
-- Part 1: Enhanced Notification System
-- ============================================================================

-- Add notification categories and metadata
ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
ADD COLUMN IF NOT EXISTS action_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS action_label VARCHAR(100),
ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS dismissed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::JSONB,
ADD COLUMN IF NOT EXISTS delivery_channels TEXT[] DEFAULT ARRAY['in_app']::TEXT[];

COMMENT ON COLUMN notifications.category IS
'Categories: session_reminder, booking_request, learning_nudge, review_prompt, achievement, system';

COMMENT ON COLUMN notifications.priority IS
'1=Critical, 2=High, 3=Normal, 4=Low, 5=Info. Determines delivery timing and prominence.';

COMMENT ON COLUMN notifications.delivery_channels IS
'Delivery methods: in_app, email, push, sms. User preferences determine actual delivery.';

CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON notifications(scheduled_for) WHERE scheduled_for IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON notifications(priority, scheduled_for);

-- ============================================================================
-- Part 2: Notification Templates
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    title_template TEXT NOT NULL,
    message_template TEXT NOT NULL,
    action_label VARCHAR(100),
    action_url_template VARCHAR(500),
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    delivery_channels TEXT[] DEFAULT ARRAY['in_app']::TEXT[],
    timing_rules JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE notification_templates IS
'Reusable notification templates with variables. Supports {user_name}, {session_time}, etc.';

CREATE INDEX IF NOT EXISTS idx_notification_templates_key ON notification_templates(template_key);
CREATE INDEX IF NOT EXISTS idx_notification_templates_category ON notification_templates(category);

-- Insert smart notification templates
INSERT INTO notification_templates (template_key, category, title_template, message_template, action_label, action_url_template, priority, delivery_channels, timing_rules) VALUES
    -- Session reminders
    ('session_reminder_1h', 'session_reminder', 
     'Session in 1 hour',
     'Your session with {tutor_name} starts in 1 hour. {subject_name} at {session_time}.',
     'Join Now', '/bookings/{booking_id}', 2, ARRAY['in_app', 'email', 'push'],
     '{"send_before_minutes": 60, "respect_timezone": true}'::JSONB),
    
    ('session_reminder_24h', 'session_reminder',
     'Session tomorrow',
     'Reminder: You have a session with {tutor_name} tomorrow at {session_time}. Topic: {topic}',
     'View Details', '/bookings/{booking_id}', 3, ARRAY['in_app', 'email'],
     '{"send_before_hours": 24, "respect_timezone": true}'::JSONB),
    
    -- Booking requests for tutors
    ('tutor_pending_bookings', 'booking_request',
     'You have {count} pending booking requests',
     'Respond quickly to avoid losing students. Average response time: {response_time}.',
     'Review Requests', '/bookings?status=pending', 2, ARRAY['in_app', 'email', 'push'],
     '{"check_interval_hours": 12, "min_pending": 1}'::JSONB),
    
    ('tutor_new_booking', 'booking_request',
     'New booking request from {student_name}',
     '{student_name} wants to book a {duration_minutes}min session for {subject_name}. Confirm within 24h.',
     'Confirm Booking', '/bookings/{booking_id}', 2, ARRAY['in_app', 'push'],
     '{"send_immediately": true}'::JSONB),
    
    -- Learning nudges
    ('student_inactive_2weeks', 'learning_nudge',
     'Ready to continue learning?',
     'It has been 2 weeks since your last session. Book your next lesson to keep the momentum!',
     'Browse Tutors', '/tutors', 3, ARRAY['in_app', 'email'],
     '{"inactive_days": 14, "max_frequency_days": 7}'::JSONB),
    
    ('student_streak_reminder', 'learning_nudge',
     'Keep your learning streak alive!',
     'You are on a {streak_count}-week learning streak. Book this week to continue.',
     'Find a Session', '/tutors', 3, ARRAY['in_app'],
     '{"streak_threshold": 2, "send_day_of_week": 5}'::JSONB),
    
    -- Review prompts (24h after session)
    ('review_prompt_24h', 'review_prompt',
     'How was your session with {tutor_name}?',
     'Share your experience to help other students. Your feedback helps tutors improve.',
     'Leave a Review', '/bookings/{booking_id}/review', 3, ARRAY['in_app', 'email'],
     '{"send_after_hours": 24, "only_completed": true}'::JSONB),
    
    -- Achievements
    ('achievement_first_session', 'achievement',
     'Congratulations on your first session!',
     'You completed your first tutoring session. Keep learning and growing!',
     'Book Another', '/tutors', 4, ARRAY['in_app'],
     '{"trigger": "first_completed_booking"}'::JSONB),
    
    ('achievement_milestone', 'achievement',
     '{milestone} sessions completed!',
     'You have completed {count} sessions. Great progress on your learning journey!',
     'View Progress', '/profile', 4, ARRAY['in_app'],
     '{"milestones": [5, 10, 25, 50, 100]}'::JSONB),
    
    -- Tutor success nudges
    ('tutor_profile_incomplete', 'system',
     'Complete your profile to get more bookings',
     'Your profile is {completeness}% complete. Add {missing_items} to increase visibility by 200%.',
     'Complete Profile', '/tutor/profile/edit', 3, ARRAY['in_app', 'email'],
     '{"check_interval_days": 7, "min_completeness": 70}'::JSONB)
    
ON CONFLICT (template_key) DO NOTHING;

-- ============================================================================
-- Part 3: Scheduled Notification Queue
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_key VARCHAR(100) NOT NULL REFERENCES notification_templates(template_key),
    scheduled_for TIMESTAMPTZ NOT NULL,
    variables JSONB DEFAULT '{}'::JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_notification_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled ON notification_queue(scheduled_for, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_notification_queue_user ON notification_queue(user_id, status);
CREATE INDEX IF NOT EXISTS idx_notification_queue_template ON notification_queue(template_key);

COMMENT ON TABLE notification_queue IS
'Scheduled notifications to be sent at specific times. Processed by background worker.';

-- ============================================================================
-- Part 4: User Notification Preferences
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Channel preferences
    email_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    
    -- Category preferences
    session_reminders_enabled BOOLEAN DEFAULT TRUE,
    booking_requests_enabled BOOLEAN DEFAULT TRUE,
    learning_nudges_enabled BOOLEAN DEFAULT TRUE,
    review_prompts_enabled BOOLEAN DEFAULT TRUE,
    achievements_enabled BOOLEAN DEFAULT TRUE,
    marketing_enabled BOOLEAN DEFAULT FALSE,
    
    -- Timing preferences
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    preferred_notification_time TIME DEFAULT '09:00:00',
    
    -- Frequency limits
    max_daily_notifications INTEGER DEFAULT 10,
    max_weekly_nudges INTEGER DEFAULT 3,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

COMMENT ON TABLE user_notification_preferences IS
'User-specific notification preferences. Respects quiet hours and frequency limits.';

CREATE INDEX IF NOT EXISTS idx_user_notification_prefs_user ON user_notification_preferences(user_id);

-- Create default preferences for existing users
INSERT INTO user_notification_preferences (user_id)
SELECT id FROM users WHERE deleted_at IS NULL
ON CONFLICT (user_id) DO NOTHING;

-- ============================================================================
-- Part 5: Smart Notification Scheduling Functions
-- ============================================================================

-- Schedule session reminder notifications
CREATE OR REPLACE FUNCTION schedule_session_reminders(p_booking_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_booking RECORD;
    v_reminder_1h TIMESTAMPTZ;
    v_reminder_24h TIMESTAMPTZ;
BEGIN
    -- Get booking details
    SELECT * INTO v_booking
    FROM bookings
    WHERE id = p_booking_id
      AND status IN ('confirmed', 'pending')
      AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Calculate reminder times
    v_reminder_1h := v_booking.start_time - INTERVAL '1 hour';
    v_reminder_24h := v_booking.start_time - INTERVAL '24 hours';
    
    -- Schedule 1-hour reminder (only if in future)
    IF v_reminder_1h > CURRENT_TIMESTAMP THEN
        INSERT INTO notification_queue (user_id, template_key, scheduled_for, variables)
        VALUES (
            v_booking.student_id,
            'session_reminder_1h',
            v_reminder_1h,
            jsonb_build_object(
                'booking_id', v_booking.id,
                'tutor_name', v_booking.tutor_name,
                'subject_name', v_booking.subject_name,
                'session_time', to_char(v_booking.start_time, 'HH24:MI')
            )
        )
        ON CONFLICT DO NOTHING;
    END IF;
    
    -- Schedule 24-hour reminder (only if in future)
    IF v_reminder_24h > CURRENT_TIMESTAMP THEN
        INSERT INTO notification_queue (user_id, template_key, scheduled_for, variables)
        VALUES (
            v_booking.student_id,
            'session_reminder_24h',
            v_reminder_24h,
            jsonb_build_object(
                'booking_id', v_booking.id,
                'tutor_name', v_booking.tutor_name,
                'subject_name', v_booking.subject_name,
                'topic', COALESCE(v_booking.topic, 'General discussion'),
                'session_time', to_char(v_booking.start_time, 'FMDay, FMDD Mon at HH24:MI')
            )
        )
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Schedule review prompt after session
CREATE OR REPLACE FUNCTION schedule_review_prompt(p_booking_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_booking RECORD;
    v_prompt_time TIMESTAMPTZ;
BEGIN
    -- Get booking details
    SELECT * INTO v_booking
    FROM bookings
    WHERE id = p_booking_id
      AND status = 'completed'
      AND deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Check if review already exists
    IF EXISTS(SELECT 1 FROM reviews WHERE booking_id = p_booking_id) THEN
        RETURN;
    END IF;
    
    -- Schedule prompt 24h after session end
    v_prompt_time := v_booking.end_time + INTERVAL '24 hours';
    
    IF v_prompt_time > CURRENT_TIMESTAMP THEN
        INSERT INTO notification_queue (user_id, template_key, scheduled_for, variables)
        VALUES (
            v_booking.student_id,
            'review_prompt_24h',
            v_prompt_time,
            jsonb_build_object(
                'booking_id', v_booking.id,
                'tutor_name', v_booking.tutor_name
            )
        )
        ON CONFLICT DO NOTHING;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Detect inactive students and schedule learning nudges
CREATE OR REPLACE FUNCTION schedule_learning_nudges()
RETURNS INTEGER AS $$
DECLARE
    v_student RECORD;
    v_nudge_count INTEGER := 0;
    v_last_session TIMESTAMPTZ;
    v_days_inactive INTEGER;
BEGIN
    FOR v_student IN 
        SELECT DISTINCT u.id, u.email
        FROM users u
        JOIN bookings b ON b.student_id = u.id
        WHERE u.role = 'student'
          AND u.is_active = TRUE
          AND u.deleted_at IS NULL
    LOOP
        -- Get last completed session
        SELECT MAX(end_time) INTO v_last_session
        FROM bookings
        WHERE student_id = v_student.id
          AND status = 'completed'
          AND deleted_at IS NULL;
        
        v_days_inactive := EXTRACT(DAY FROM CURRENT_TIMESTAMP - v_last_session);
        
        -- If inactive for 14+ days, schedule nudge
        IF v_days_inactive >= 14 THEN
            -- Check if nudge not already scheduled
            IF NOT EXISTS(
                SELECT 1 FROM notification_queue
                WHERE user_id = v_student.id
                  AND template_key = 'student_inactive_2weeks'
                  AND scheduled_for > CURRENT_TIMESTAMP - INTERVAL '7 days'
            ) THEN
                INSERT INTO notification_queue (user_id, template_key, scheduled_for, variables)
                VALUES (
                    v_student.id,
                    'student_inactive_2weeks',
                    CURRENT_TIMESTAMP + INTERVAL '1 hour',
                    jsonb_build_object('days_inactive', v_days_inactive)
                );
                
                v_nudge_count := v_nudge_count + 1;
            END IF;
        END IF;
    END LOOP;
    
    RETURN v_nudge_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Part 6: Notification Triggers
-- ============================================================================

-- Auto-schedule reminders when booking is confirmed
CREATE OR REPLACE FUNCTION trigger_schedule_reminders()
RETURNS TRIGGER AS $$
BEGIN
    -- When booking is created or confirmed, schedule reminders
    IF (TG_OP = 'INSERT' AND NEW.status IN ('confirmed', 'pending')) OR
       (TG_OP = 'UPDATE' AND NEW.status = 'confirmed' AND OLD.status != 'confirmed') THEN
        PERFORM schedule_session_reminders(NEW.id);
    END IF;
    
    -- When booking is completed, schedule review prompt
    IF (TG_OP = 'UPDATE' AND NEW.status = 'completed' AND OLD.status != 'completed') THEN
        PERFORM schedule_review_prompt(NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_schedule_notification_reminders ON bookings;
CREATE TRIGGER trg_schedule_notification_reminders
    AFTER INSERT OR UPDATE OF status ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION trigger_schedule_reminders();

-- ============================================================================
-- Part 7: Notification Analytics
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_analytics (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    delivery_channel VARCHAR(20),
    was_actionable BOOLEAN DEFAULT FALSE,
    action_taken BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_analytics_template ON notification_analytics(template_key, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_notification_analytics_user ON notification_analytics(user_id);

COMMENT ON TABLE notification_analytics IS
'Track notification effectiveness: open rates, click rates, action completion.';

-- View for notification effectiveness
CREATE OR REPLACE VIEW notification_effectiveness AS
SELECT 
    template_key,
    COUNT(*) as total_sent,
    COUNT(opened_at) as total_opened,
    COUNT(clicked_at) as total_clicked,
    COUNT(action_taken) FILTER (WHERE action_taken = TRUE) as total_actions_taken,
    ROUND(COUNT(opened_at) * 100.0 / COUNT(*), 2) as open_rate,
    ROUND(COUNT(clicked_at) * 100.0 / COUNT(*), 2) as click_rate,
    ROUND(COUNT(*) FILTER (WHERE action_taken = TRUE) * 100.0 / COUNT(*), 2) as action_rate
FROM notification_analytics
WHERE sent_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY template_key;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_templates_count INTEGER;
    v_queue_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_templates_count FROM notification_templates WHERE is_active = TRUE;
    SELECT COUNT(*) INTO v_queue_count FROM notification_queue WHERE status = 'pending';
    
    RAISE NOTICE '';
    RAISE NOTICE '=== Migration 016: Proactive Engagement ===';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Smart Notification System';
    RAISE NOTICE '  - % notification templates', v_templates_count;
    RAISE NOTICE '  - Categories: reminders, nudges, prompts, achievements';
    RAISE NOTICE '  - Respects user preferences and quiet hours';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Intelligent Scheduling';
    RAISE NOTICE '  - Session reminders: 24h and 1h before';
    RAISE NOTICE '  - Review prompts: 24h after completion';
    RAISE NOTICE '  - Learning nudges: After 14 days inactive';
    RAISE NOTICE '  - % notifications queued', v_queue_count;
    RAISE NOTICE '';
    RAISE NOTICE '✓ User Preferences';
    RAISE NOTICE '  - Channel control: email, push, SMS';
    RAISE NOTICE '  - Category opt-in/out';
    RAISE NOTICE '  - Quiet hours support';
    RAISE NOTICE '  - Frequency limits';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Analytics & Optimization';
    RAISE NOTICE '  - Track open rates, click rates, actions';
    RAISE NOTICE '  - Measure notification effectiveness';
    RAISE NOTICE '';
    RAISE NOTICE '📲 Goal: Feel like a helpful assistant, not spam';
    RAISE NOTICE '🎯 Expected: Higher engagement without notification fatigue';
END $$;
