-- ============================================================================
-- Migration: Add profile_status to tutor_profiles
-- Description: Track tutor profile approval workflow
-- Statuses: incomplete, pending_approval, under_review, approved, rejected
-- ============================================================================

-- Add profile_status column to tutor_profiles
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS profile_status VARCHAR(20) DEFAULT 'incomplete' NOT NULL;

-- Add rejection_reason column for admin feedback
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Add approved_at timestamp
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;

-- Add approved_by admin reference (no FK to avoid ambiguity with user_id)
ALTER TABLE tutor_profiles
ADD COLUMN IF NOT EXISTS approved_by INTEGER;

-- Add check constraint for valid status values
ALTER TABLE tutor_profiles
ADD CONSTRAINT valid_profile_status
CHECK (profile_status IN ('incomplete', 'pending_approval', 'under_review', 'approved', 'rejected'));

-- Create index for filtering by status
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_status ON tutor_profiles(profile_status);

-- Create index for pending/review profiles (for admin moderation)
CREATE INDEX IF NOT EXISTS idx_tutor_profiles_pending_review
ON tutor_profiles(profile_status, created_at DESC)
WHERE profile_status IN ('pending_approval', 'under_review');

-- Update existing tutor profiles
-- If is_approved = TRUE, set status to 'approved'
-- Otherwise, if they have basic info, set to 'incomplete'
UPDATE tutor_profiles
SET profile_status = CASE
    WHEN is_approved = TRUE THEN 'approved'
    ELSE 'incomplete'
END;

-- Add comment to column
COMMENT ON COLUMN tutor_profiles.profile_status IS
'Tutor profile approval status: incomplete, pending_approval, under_review, approved, rejected';

COMMENT ON COLUMN tutor_profiles.rejection_reason IS
'Admin feedback when profile is rejected';

COMMENT ON COLUMN tutor_profiles.approved_at IS
'Timestamp when profile was approved';

COMMENT ON COLUMN tutor_profiles.approved_by IS
'Admin user ID who approved the profile';
