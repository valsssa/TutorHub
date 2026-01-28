-- Migration 023: Add category field to subjects table
-- Compatibility fix: API returns category but database didn't have it

ALTER TABLE subjects
  ADD COLUMN IF NOT EXISTS category VARCHAR(50);

COMMENT ON COLUMN subjects.category IS 'Subject category (e.g., STEM, Languages, Arts, Business)';

-- Update existing subjects with default categories (optional - can be done manually)
-- UPDATE subjects SET category = 'STEM' WHERE name ILIKE '%math%' OR name ILIKE '%science%' OR name ILIKE '%physics%' OR name ILIKE '%chemistry%';
-- UPDATE subjects SET category = 'Languages' WHERE name ILIKE '%language%' OR name ILIKE '%english%' OR name ILIKE '%spanish%';
-- UPDATE subjects SET category = 'Arts' WHERE name ILIKE '%art%' OR name ILIKE '%music%' OR name ILIKE '%drama%';
-- UPDATE subjects SET category = 'Business' WHERE name ILIKE '%business%' OR name ILIKE '%economics%' OR name ILIKE '%finance%';
