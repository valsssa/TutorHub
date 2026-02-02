-- Migration: Add wallet and wallet_transactions tables
-- Description: Creates tables for user wallets and transaction history

-- Wallets table: stores user wallet balances
CREATE TABLE IF NOT EXISTS wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    balance_cents INTEGER NOT NULL DEFAULT 0,
    pending_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_wallet_per_currency UNIQUE (user_id, currency),
    CONSTRAINT non_negative_wallet_balance CHECK (balance_cents >= 0),
    CONSTRAINT non_negative_pending_balance CHECK (pending_cents >= 0)
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS ix_wallets_user_id ON wallets(user_id);

-- Wallet transactions table: tracks all wallet operations
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE RESTRICT,
    type VARCHAR(20) NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    description TEXT,
    reference_id VARCHAR(255) UNIQUE,
    transaction_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT valid_transaction_type CHECK (
        type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'REFUND', 'PAYOUT', 'PAYMENT', 'FEE')
    ),
    CONSTRAINT valid_transaction_status CHECK (
        status IN ('PENDING', 'COMPLETED', 'FAILED', 'CANCELLED')
    )
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_created_at ON wallet_transactions(created_at);
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_reference_id ON wallet_transactions(reference_id);
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_status ON wallet_transactions(status);

-- Comments for documentation
COMMENT ON TABLE wallets IS 'User wallets for storing credits and making payments';
COMMENT ON TABLE wallet_transactions IS 'Transaction history for wallet operations';
COMMENT ON COLUMN wallets.balance_cents IS 'Available balance in cents';
COMMENT ON COLUMN wallets.pending_cents IS 'Balance pending release (e.g., in escrow)';
COMMENT ON COLUMN wallet_transactions.reference_id IS 'External reference for idempotency checks';
