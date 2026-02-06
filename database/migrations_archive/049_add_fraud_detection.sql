-- Migration: Add fraud detection for trial abuse prevention
-- Purpose: Track registration signals to detect users creating multiple accounts for free trials

-- Add fraud detection columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS registration_ip INET,
ADD COLUMN IF NOT EXISTS trial_restricted BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS fraud_flags JSONB DEFAULT '[]'::JSONB;

-- Create index for efficient IP-based lookups
CREATE INDEX IF NOT EXISTS idx_users_registration_ip
ON users (registration_ip)
WHERE registration_ip IS NOT NULL;

-- Create index for trial-restricted users
CREATE INDEX IF NOT EXISTS idx_users_trial_restricted
ON users (trial_restricted)
WHERE trial_restricted = TRUE;

-- Create fraud signals table for tracking registration patterns
CREATE TABLE IF NOT EXISTS registration_fraud_signals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    signal_type VARCHAR(50) NOT NULL,
    signal_value TEXT NOT NULL,
    confidence_score NUMERIC(3,2) DEFAULT 0.50 CHECK (confidence_score BETWEEN 0 AND 1),
    detected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMPTZ,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    review_outcome VARCHAR(20),
    review_notes TEXT,
    CONSTRAINT valid_signal_type CHECK (signal_type IN ('ip_address', 'device_fingerprint', 'email_pattern', 'browser_fingerprint', 'behavioral')),
    CONSTRAINT valid_review_outcome CHECK (review_outcome IS NULL OR review_outcome IN ('legitimate', 'fraudulent', 'suspicious'))
);

-- Index for finding signals by user
CREATE INDEX IF NOT EXISTS idx_fraud_signals_user
ON registration_fraud_signals (user_id, detected_at DESC);

-- Index for finding signals by IP/fingerprint value
CREATE INDEX IF NOT EXISTS idx_fraud_signals_value
ON registration_fraud_signals (signal_type, signal_value, detected_at DESC);

-- Index for pending reviews
CREATE INDEX IF NOT EXISTS idx_fraud_signals_pending_review
ON registration_fraud_signals (reviewed_at, detected_at DESC)
WHERE reviewed_at IS NULL;

-- Comments for documentation
COMMENT ON COLUMN users.registration_ip IS 'IP address at registration time for fraud detection';
COMMENT ON COLUMN users.trial_restricted IS 'TRUE if user flagged for potential trial abuse - prevents automatic trial grant';
COMMENT ON COLUMN users.fraud_flags IS 'JSON array of fraud signal types detected for this user';

COMMENT ON TABLE registration_fraud_signals IS 'Tracks fraud signals detected during registration for trial abuse prevention';
COMMENT ON COLUMN registration_fraud_signals.signal_type IS 'Type of signal: ip_address, device_fingerprint, email_pattern, browser_fingerprint, behavioral';
COMMENT ON COLUMN registration_fraud_signals.signal_value IS 'The actual value (e.g., IP address, fingerprint hash)';
COMMENT ON COLUMN registration_fraud_signals.confidence_score IS 'Confidence that this signal indicates fraud (0-1)';

-- Record migration
INSERT INTO schema_migrations (version, description)
VALUES ('039', 'Add fraud detection for trial abuse prevention')
ON CONFLICT (version) DO NOTHING;
