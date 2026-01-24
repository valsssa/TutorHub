-- Add teaching_philosophy column to tutor_profiles
-- This enhances tutor card display with personal teaching philosophy snippets

ALTER TABLE tutor_profiles 
ADD COLUMN IF NOT EXISTS teaching_philosophy TEXT;

COMMENT ON COLUMN tutor_profiles.teaching_philosophy IS 'Tutor''s teaching philosophy or approach (displayed on tutor cards)';
