-- Migration: 035_create_webhook_events
-- Description: Create webhook_events table for Stripe webhook idempotency
-- Created: 2026-01-29

-- Create webhook_events table to track processed Stripe webhook events
-- This prevents duplicate processing when Stripe retries webhook delivery

CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create index for fast lookup by stripe_event_id
CREATE INDEX IF NOT EXISTS idx_webhook_events_stripe_event_id ON webhook_events(stripe_event_id);

-- Add comment for documentation
COMMENT ON TABLE webhook_events IS 'Tracks processed Stripe webhook events for idempotency';
COMMENT ON COLUMN webhook_events.stripe_event_id IS 'Unique Stripe event ID (e.g., evt_xxx)';
COMMENT ON COLUMN webhook_events.event_type IS 'Stripe event type (e.g., checkout.session.completed)';
COMMENT ON COLUMN webhook_events.processed_at IS 'Timestamp when the event was processed';
