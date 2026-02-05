// Backend transaction types (uppercase)
export type BackendTransactionType = 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER' | 'REFUND' | 'PAYOUT' | 'PAYMENT' | 'FEE';

// Frontend-friendly transaction types (lowercase, mapped)
export type TransactionType = 'deposit' | 'withdrawal' | 'refund' | 'payout' | 'payment' | 'fee' | 'transfer';

export type TransactionStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

export type WithdrawalStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export type PaymentMethodType = 'bank_account' | 'paypal' | 'stripe';

// Backend returns simpler balance response
export interface WalletBalance {
  balance_cents: number;
  currency: string;
}

// Backend transaction response (raw from API)
export interface BackendTransaction {
  id: number;
  type: BackendTransactionType;
  amount_cents: number;
  currency: string;
  description: string | null;
  status: string;
  reference_id?: string | null;
  created_at: string;
  completed_at?: string | null;
}

// Frontend transaction (transformed for display)
export interface Transaction {
  id: number;
  type: TransactionType;
  amount: number;
  currency: string;
  description: string;
  status: TransactionStatus;
  reference_id?: string;
  created_at: string;
  completed_at?: string;
}

// Transform backend transaction to frontend format
export function transformTransaction(backend: BackendTransaction): Transaction {
  const typeMap: Record<BackendTransactionType, TransactionType> = {
    DEPOSIT: 'deposit',
    WITHDRAWAL: 'withdrawal',
    TRANSFER: 'transfer',
    REFUND: 'refund',
    PAYOUT: 'payout',
    PAYMENT: 'payment',
    FEE: 'fee',
  };

  return {
    id: backend.id,
    type: typeMap[backend.type] || 'payment',
    amount: backend.amount_cents / 100,
    currency: backend.currency,
    description: backend.description || getDefaultDescription(backend.type),
    status: (backend.status?.toLowerCase() || 'pending') as TransactionStatus,
    reference_id: backend.reference_id ?? undefined,
    created_at: backend.created_at,
    completed_at: backend.completed_at ?? undefined,
  };
}

function getDefaultDescription(type: BackendTransactionType): string {
  const descriptions: Record<BackendTransactionType, string> = {
    DEPOSIT: 'Wallet top-up',
    WITHDRAWAL: 'Withdrawal to bank',
    TRANSFER: 'Transfer',
    REFUND: 'Session refund',
    PAYOUT: 'Tutor payout',
    PAYMENT: 'Session payment',
    FEE: 'Platform fee',
  };
  return descriptions[type] || 'Transaction';
}

export interface WithdrawalRequest {
  id: number;
  amount: number;
  currency: string;
  status: WithdrawalStatus;
  payment_method_id: number;
  payment_method?: PaymentMethod;
  created_at: string;
  processed_at?: string;
  failure_reason?: string;
}

export interface PaymentMethod {
  id: number;
  type: PaymentMethodType;
  name: string;
  is_default: boolean;
  last_four?: string;
  bank_name?: string;
  email?: string;
  created_at: string;
}

export interface CreateWithdrawalInput {
  amount: number;
  payment_method_id: number;
}

export interface TransactionFilters {
  type?: string;
  status?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}

// Wallet checkout types
export interface WalletCheckoutRequest {
  amount_cents: number;
  currency?: string;
}

export interface WalletCheckoutResponse {
  checkout_url: string;
  session_id: string;
  amount_cents: number;
  currency: string;
}
