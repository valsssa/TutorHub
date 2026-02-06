-- Migration 028: Create student_notes table
-- Purpose: Allow tutors to keep private notes about their students
-- Date: 2026-01-28

CREATE TABLE student_notes (
    id SERIAL PRIMARY KEY,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Ensure one note record per tutor-student pair
    CONSTRAINT unique_tutor_student_note UNIQUE (tutor_id, student_id)
);

-- Index for faster lookups
CREATE INDEX idx_student_notes_tutor ON student_notes(tutor_id);
CREATE INDEX idx_student_notes_student ON student_notes(student_id);

-- Comment
COMMENT ON TABLE student_notes IS 'Private notes that tutors can keep about their students';
COMMENT ON COLUMN student_notes.notes IS 'Private notes visible only to the tutor';
