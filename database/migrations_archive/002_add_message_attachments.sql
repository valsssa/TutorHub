-- Migration 002: Add Message Attachments Support
-- Adds secure file attachment capabilities to messages

-- Create message_attachments table
CREATE TABLE IF NOT EXISTS message_attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_key VARCHAR(500) NOT NULL,  -- S3/MinIO object key
    original_filename VARCHAR(255) NOT NULL,  -- User's original filename (sanitized)
    file_size BIGINT NOT NULL,  -- Size in bytes
    mime_type VARCHAR(100) NOT NULL,  -- e.g., image/jpeg, application/pdf
    file_category VARCHAR(50) NOT NULL,  -- 'image', 'document', 'other'
    
    -- Security & Access Control
    uploaded_by INTEGER NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    is_scanned BOOLEAN DEFAULT FALSE NOT NULL,  -- Virus scan status
    scan_result VARCHAR(50),  -- 'clean', 'infected', 'pending'
    is_public BOOLEAN DEFAULT FALSE NOT NULL,  -- Public or private access
    
    -- Metadata
    width INTEGER,  -- For images
    height INTEGER,  -- For images
    duration_seconds INTEGER,  -- For videos/audio
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,  -- Soft delete
    
    -- Constraints
    CONSTRAINT valid_file_size CHECK (file_size > 0 AND file_size <= 10485760),  -- Max 10MB
    CONSTRAINT valid_file_category CHECK (file_category IN ('image', 'document', 'video', 'audio', 'other'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_message_attachments_message_id ON message_attachments(message_id);
CREATE INDEX IF NOT EXISTS idx_message_attachments_uploaded_by ON message_attachments(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_message_attachments_created_at ON message_attachments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_attachments_file_key ON message_attachments(file_key);

-- Index for finding unscanned files
CREATE INDEX IF NOT EXISTS idx_message_attachments_scan_status 
ON message_attachments(is_scanned, scan_result) 
WHERE deleted_at IS NULL AND scan_result = 'pending';

-- Comments for documentation
COMMENT ON TABLE message_attachments IS 'Secure file attachments for messages with virus scanning and access control';
COMMENT ON COLUMN message_attachments.file_key IS 'S3/MinIO object key for retrieving the file';
COMMENT ON COLUMN message_attachments.is_scanned IS 'Whether file has been scanned for viruses';
COMMENT ON COLUMN message_attachments.scan_result IS 'Result of virus scan: clean, infected, pending';
COMMENT ON COLUMN message_attachments.is_public IS 'Whether file is publicly accessible or requires authentication';

