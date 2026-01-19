-- ============================================================================
-- Add created_at to All Tables + Clear Non-Hourly Pricing Model
-- Critical for debugging and flexible pricing
-- ============================================================================

-- ============================================================================
-- Part 1: Add created_at to tables missing it
-- ============================================================================

-- Add created_at to tables that don't have it
ALTER TABLE favorite_tutors 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE reports 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;

ALTER TABLE session_materials 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;

-- Add indexes for time-based queries
CREATE INDEX IF NOT EXISTS idx_favorite_tutors_created_at ON favorite_tutors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_materials_created_at ON session_materials(created_at DESC);

COMMENT ON COLUMN favorite_tutors.created_at IS 'When student favorited this tutor';
COMMENT ON COLUMN reports.created_at IS 'When report was filed';
COMMENT ON COLUMN session_materials.created_at IS 'When material was uploaded';

-- ============================================================================
-- Part 2: Non-Hourly Pricing Model
-- ============================================================================

-- Add package-based pricing support to tutor profiles
ALTER TABLE tutor_profiles 
ADD COLUMN IF NOT EXISTS pricing_model VARCHAR(20) DEFAULT 'hourly' NOT NULL;

ALTER TABLE tutor_profiles
ADD CONSTRAINT IF NOT EXISTS valid_pricing_model 
CHECK (pricing_model IN ('hourly', 'package', 'session', 'hybrid'));

COMMENT ON COLUMN tutor_profiles.pricing_model IS 
'Pricing model: hourly (per hour), package (fixed sessions), session (per session), hybrid (both)';

-- Enhance tutor_pricing_options table for flexible pricing
ALTER TABLE tutor_pricing_options 
ADD COLUMN IF NOT EXISTS pricing_type VARCHAR(20) DEFAULT 'package' NOT NULL,
ADD COLUMN IF NOT EXISTS sessions_included INTEGER,
ADD COLUMN IF NOT EXISTS validity_days INTEGER,
ADD COLUMN IF NOT EXISTS is_popular BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0 NOT NULL;

ALTER TABLE tutor_pricing_options
DROP CONSTRAINT IF EXISTS valid_pricing_type;

ALTER TABLE tutor_pricing_options
ADD CONSTRAINT valid_pricing_type 
CHECK (pricing_type IN ('hourly', 'session', 'package', 'subscription'));

CREATE INDEX IF NOT EXISTS idx_tutor_pricing_popular ON tutor_pricing_options(is_popular DESC, sort_order ASC);
CREATE INDEX IF NOT EXISTS idx_tutor_pricing_sort ON tutor_pricing_options(tutor_profile_id, sort_order ASC);

COMMENT ON COLUMN tutor_pricing_options.pricing_type IS 
'Type: hourly (per hour), session (single session), package (multiple sessions), subscription (monthly)';
COMMENT ON COLUMN tutor_pricing_options.sessions_included IS 
'Number of sessions included in package/subscription (NULL for hourly)';
COMMENT ON COLUMN tutor_pricing_options.validity_days IS 
'How many days package/subscription is valid (NULL for session-based)';
COMMENT ON COLUMN tutor_pricing_options.is_popular IS 
'Mark as "Most Popular" for better conversion';
COMMENT ON COLUMN tutor_pricing_options.sort_order IS 
'Display order (0 = first, higher = later)';

-- Add booking pricing context
ALTER TABLE bookings 
ADD COLUMN IF NOT EXISTS pricing_option_id INTEGER REFERENCES tutor_pricing_options(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS package_sessions_remaining INTEGER,
ADD COLUMN IF NOT EXISTS pricing_type VARCHAR(20) DEFAULT 'hourly' NOT NULL;

ALTER TABLE bookings
DROP CONSTRAINT IF EXISTS valid_booking_pricing_type;

ALTER TABLE bookings
ADD CONSTRAINT valid_booking_pricing_type 
CHECK (pricing_type IN ('hourly', 'session', 'package', 'subscription'));

CREATE INDEX IF NOT EXISTS idx_bookings_pricing_option ON bookings(pricing_option_id);

COMMENT ON COLUMN bookings.pricing_option_id IS 
'Reference to pricing option used for this booking';
COMMENT ON COLUMN bookings.package_sessions_remaining IS 
'Sessions remaining in package after this booking';
COMMENT ON COLUMN bookings.pricing_type IS 
'How this booking was priced';

-- ============================================================================
-- Student Package Credits/Subscriptions
-- ============================================================================

CREATE TABLE IF NOT EXISTS student_packages (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_profile_id INTEGER NOT NULL REFERENCES tutor_profiles(id) ON DELETE CASCADE,
    pricing_option_id INTEGER NOT NULL REFERENCES tutor_pricing_options(id) ON DELETE RESTRICT,
    sessions_purchased INTEGER NOT NULL CHECK (sessions_purchased > 0),
    sessions_remaining INTEGER NOT NULL CHECK (sessions_remaining >= 0),
    sessions_used INTEGER DEFAULT 0 NOT NULL CHECK (sessions_used >= 0),
    purchase_price NUMERIC(10,2) NOT NULL CHECK (purchase_price > 0),
    purchased_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    payment_intent_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT valid_package_status CHECK (status IN ('active', 'expired', 'exhausted', 'refunded'))
);

CREATE INDEX IF NOT EXISTS idx_student_packages_student ON student_packages(student_id, status);
CREATE INDEX IF NOT EXISTS idx_student_packages_tutor ON student_packages(tutor_profile_id);
CREATE INDEX IF NOT EXISTS idx_student_packages_expires ON student_packages(expires_at) WHERE expires_at IS NOT NULL AND status = 'active';
CREATE INDEX IF NOT EXISTS idx_student_packages_active ON student_packages(student_id, tutor_profile_id, status) WHERE status = 'active';

COMMENT ON TABLE student_packages IS 
'Student-purchased packages and subscriptions for specific tutors';
COMMENT ON COLUMN student_packages.sessions_remaining IS 
'How many sessions left in this package';
COMMENT ON COLUMN student_packages.expires_at IS 
'When package expires (NULL = no expiration)';
COMMENT ON COLUMN student_packages.status IS 
'active (can be used), expired (past expiry date), exhausted (all sessions used), refunded (money returned)';

-- Trigger to update student_packages on usage
CREATE OR REPLACE FUNCTION update_package_usage()
RETURNS TRIGGER AS $$
BEGIN
    -- Only process completed bookings linked to packages
    IF NEW.status = 'completed' AND NEW.pricing_type IN ('package', 'subscription') THEN
        -- Decrement sessions_remaining
        UPDATE student_packages
        SET sessions_remaining = sessions_remaining - 1,
            sessions_used = sessions_used + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = (
            SELECT sp.id FROM student_packages sp
            WHERE sp.student_id = NEW.student_id
            AND sp.tutor_profile_id = NEW.tutor_profile_id
            AND sp.status = 'active'
            AND sp.sessions_remaining > 0
            AND (sp.expires_at IS NULL OR sp.expires_at > CURRENT_TIMESTAMP)
            ORDER BY sp.expires_at ASC NULLS LAST, sp.purchased_at ASC
            LIMIT 1
        );
        
        -- Mark package as exhausted if no sessions left
        UPDATE student_packages
        SET status = 'exhausted',
            updated_at = CURRENT_TIMESTAMP
        WHERE sessions_remaining = 0 AND status = 'active';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_package_usage ON bookings;
CREATE TRIGGER trg_update_package_usage
    AFTER UPDATE OF status ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION update_package_usage();

COMMENT ON FUNCTION update_package_usage() IS 
'Automatically decrements package sessions when booking is completed';

-- Function to expire old packages
CREATE OR REPLACE FUNCTION expire_old_packages()
RETURNS INTEGER AS $$
DECLARE
    v_expired_count INTEGER;
BEGIN
    WITH expired AS (
        UPDATE student_packages
        SET status = 'expired',
            updated_at = CURRENT_TIMESTAMP
        WHERE status = 'active'
        AND expires_at IS NOT NULL
        AND expires_at < CURRENT_TIMESTAMP
        RETURNING *
    )
    SELECT COUNT(*) INTO v_expired_count FROM expired;
    
    RETURN v_expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION expire_old_packages() IS 
'Marks expired packages as expired. Run daily via cron/scheduler.';

-- ============================================================================
-- Default Pricing Options (Examples)
-- ============================================================================

-- Add example pricing options for existing tutors
DO $$
DECLARE
    tutor_record RECORD;
BEGIN
    FOR tutor_record IN 
        SELECT id, hourly_rate FROM tutor_profiles WHERE is_approved = TRUE
    LOOP
        -- Check if tutor already has pricing options
        IF NOT EXISTS (
            SELECT 1 FROM tutor_pricing_options 
            WHERE tutor_profile_id = tutor_record.id
        ) THEN
            -- Add default pricing options
            
            -- Single Session
            INSERT INTO tutor_pricing_options (
                tutor_profile_id, title, description, duration_minutes, price,
                pricing_type, sessions_included, is_popular, sort_order
            ) VALUES (
                tutor_record.id,
                'Single Session',
                'Try a one-time session',
                60,
                tutor_record.hourly_rate,
                'session',
                1,
                FALSE,
                0
            );
            
            -- 5-Session Package (10% discount)
            INSERT INTO tutor_pricing_options (
                tutor_profile_id, title, description, duration_minutes, price,
                pricing_type, sessions_included, validity_days, is_popular, sort_order
            ) VALUES (
                tutor_record.id,
                '5 Session Package',
                'Save 10% with this package',
                60,
                tutor_record.hourly_rate * 5 * 0.9,
                'package',
                5,
                90,
                TRUE,
                1
            );
            
            -- 10-Session Package (20% discount)
            INSERT INTO tutor_pricing_options (
                tutor_profile_id, title, description, duration_minutes, price,
                pricing_type, sessions_included, validity_days, is_popular, sort_order
            ) VALUES (
                tutor_record.id,
                '10 Session Package',
                'Best value - Save 20%',
                60,
                tutor_record.hourly_rate * 10 * 0.8,
                'package',
                10,
                180,
                FALSE,
                2
            );
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Default pricing options created for approved tutors';
END $$;

-- ============================================================================
-- Views for Pricing
-- ============================================================================

CREATE OR REPLACE VIEW tutor_pricing_summary AS
SELECT 
    tp.id as tutor_profile_id,
    tp.user_id,
    tp.pricing_model,
    tp.hourly_rate as base_hourly_rate,
    COUNT(tpo.id) as pricing_options_count,
    MIN(tpo.price) as min_price,
    MAX(tpo.price) as max_price,
    ARRAY_AGG(tpo.pricing_type ORDER BY tpo.sort_order) as available_pricing_types
FROM tutor_profiles tp
LEFT JOIN tutor_pricing_options tpo ON tp.id = tpo.tutor_profile_id
WHERE tp.deleted_at IS NULL
GROUP BY tp.id, tp.user_id, tp.pricing_model, tp.hourly_rate;

COMMENT ON VIEW tutor_pricing_summary IS 
'Summary of tutor pricing options for quick filtering';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_tables_with_created_at INTEGER;
    v_pricing_options_count INTEGER;
    v_packages_count INTEGER;
BEGIN
    -- Verify created_at columns
    SELECT COUNT(*) INTO v_tables_with_created_at
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND column_name = 'created_at';
    
    -- Count pricing options
    SELECT COUNT(*) INTO v_pricing_options_count
    FROM tutor_pricing_options;
    
    -- Count packages
    SELECT COUNT(*) INTO v_packages_count
    FROM student_packages;
    
    RAISE NOTICE 'Migration completed:';
    RAISE NOTICE '  - Tables with created_at: %', v_tables_with_created_at;
    RAISE NOTICE '  - Pricing options: %', v_pricing_options_count;
    RAISE NOTICE '  - Student packages: %', v_packages_count;
    RAISE NOTICE '  - Pricing models: hourly, package, session, subscription, hybrid';
    RAISE NOTICE '  - Automatic package usage tracking enabled';
END $$;
