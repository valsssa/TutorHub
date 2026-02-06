-- Migration: Add conversations table and update messages table
-- Description: Creates conversations table to track message threads between students and tutors,
--              and adds conversation_id, is_system_message, and attachment_url to messages table.

BEGIN;

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tutor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    last_message_at TIMESTAMPTZ,
    student_unread_count INTEGER NOT NULL DEFAULT 0,
    tutor_unread_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_conversation_participants UNIQUE (student_id, tutor_id, booking_id)
);

-- Create indexes for conversations
CREATE INDEX IF NOT EXISTS idx_conversations_student ON conversations(student_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tutor ON conversations(tutor_id);
CREATE INDEX IF NOT EXISTS idx_conversations_booking ON conversations(booking_id);
CREATE INDEX IF NOT EXISTS idx_conversations_last_message ON conversations(last_message_at DESC NULLS LAST);

-- Add new columns to messages table
ALTER TABLE messages
    ADD COLUMN IF NOT EXISTS conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS is_system_message BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS attachment_url VARCHAR(500);

-- Create index for conversation_id on messages
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at DESC);

-- Record migration
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (
    '045',
    'Add conversations table and update messages table',
    CURRENT_TIMESTAMP
) ON CONFLICT (version) DO NOTHING;

COMMIT;
