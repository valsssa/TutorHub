export type TransactionType = 'earning' | 'withdrawal' | 'refund' | 'bonus' | 'fee';

export type TransactionStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

export type WithdrawalStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export type PaymentMethodType = 'bank_account' | 'paypal' | 'stripe';

export interface WalletBalance {
  available: number;
  pending: number;
  total: number;
  currency: string;
  last_updated: string;
}

export interface Transaction {
  id: number;
  type: TransactionType;
  amount: number;
  currency: string;
  description: string;
  status: TransactionStatus;
  booking_id?: number;
  withdrawal_id?: number;
  created_at: string;
  completed_at?: string;
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
  type?: TransactionType;
  status?: TransactionStatus;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}
