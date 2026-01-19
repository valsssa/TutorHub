-- ============================================================================
-- Booking Conflict Detection at Database Level
-- Prevents overlapping bookings for the same tutor
-- ============================================================================

-- Create function to check booking conflicts
CREATE OR REPLACE FUNCTION check_booking_conflicts()
RETURNS TRIGGER AS $$
DECLARE
    v_conflict_count INTEGER;
BEGIN
    -- Only check for pending/confirmed bookings (skip cancelled/completed/no_show)
    IF NEW.status NOT IN ('pending', 'confirmed') THEN
        RETURN NEW;
    END IF;
    
    -- Check for overlapping bookings for same tutor
    SELECT COUNT(*) INTO v_conflict_count
    FROM bookings
    WHERE tutor_profile_id = NEW.tutor_profile_id
    AND id != COALESCE(NEW.id, -1)  -- Exclude current booking on UPDATE
    AND status IN ('pending', 'confirmed')
    AND (
        -- Check if new booking overlaps with existing bookings
        (NEW.start_time, NEW.end_time) OVERLAPS (start_time, end_time)
    );
    
    IF v_conflict_count > 0 THEN
        RAISE EXCEPTION 'Booking conflict: Tutor is not available at this time. Please choose a different time slot.'
            USING ERRCODE = 'unique_violation',
                  DETAIL = format('Tutor %s has %s conflicting booking(s) between %s and %s',
                                  NEW.tutor_profile_id,
                                  v_conflict_count,
                                  NEW.start_time,
                                  NEW.end_time);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger BEFORE INSERT OR UPDATE on bookings
DROP TRIGGER IF EXISTS trg_check_booking_conflicts ON bookings;
CREATE TRIGGER trg_check_booking_conflicts
    BEFORE INSERT OR UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION check_booking_conflicts();

COMMENT ON FUNCTION check_booking_conflicts() IS 
'Database-level validation to prevent overlapping bookings for the same tutor.
Only applies to pending/confirmed bookings. Uses OVERLAPS operator for accurate time range checking.';

-- Create index to optimize conflict detection queries
CREATE INDEX IF NOT EXISTS idx_bookings_tutor_status_time 
ON bookings(tutor_profile_id, status, start_time, end_time)
WHERE status IN ('pending', 'confirmed');

COMMENT ON INDEX idx_bookings_tutor_status_time IS 
'Optimized index for booking conflict detection. 
Partial index only on active bookings (pending/confirmed) for better performance.';

-- Validate existing bookings (optional - reports conflicts but doesn't fix them)
DO $$
DECLARE
    v_conflicts TEXT;
BEGIN
    SELECT string_agg(
        format('Booking ID %s overlaps with ID %s for tutor %s',
               b1.id, b2.id, b1.tutor_profile_id),
        E'\n'
    ) INTO v_conflicts
    FROM bookings b1
    JOIN bookings b2 ON b1.tutor_profile_id = b2.tutor_profile_id
    WHERE b1.id < b2.id
    AND b1.status IN ('pending', 'confirmed')
    AND b2.status IN ('pending', 'confirmed')
    AND (b1.start_time, b1.end_time) OVERLAPS (b2.start_time, b2.end_time);
    
    IF v_conflicts IS NOT NULL THEN
        RAISE WARNING 'Existing booking conflicts detected:%', E'\n' || v_conflicts;
    ELSE
        RAISE NOTICE 'No booking conflicts found in existing data.';
    END IF;
END $$;
