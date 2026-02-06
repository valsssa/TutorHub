import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  WalletBalance,
  WalletCheckoutRequest,
  WalletCheckoutResponse,
  Transaction,
  TransactionFilters,
  BackendTransaction,
} from '@/types/wallet';
import { transformTransaction } from '@/types/wallet';

interface BackendTransactionListResponse {
  items: BackendTransaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const walletApi = {
  // Get current student's wallet balance
  getBalance: () =>
    api.get<WalletBalance>('/wallet/balance'),

  // Create a checkout session for wallet top-up
  createCheckout: (data: WalletCheckoutRequest) =>
    api.post<WalletCheckoutResponse>('/wallet/checkout', data),

  // Get paginated list of wallet transactions
  getTransactions: async (filters?: TransactionFilters): Promise<TransactionListResponse> => {
    const query = filters ? toQueryString(filters) : '';
    const endpoint = query ? `/wallet/transactions?${query}` : '/wallet/transactions';
    const response = await api.get<BackendTransactionListResponse>(endpoint);

    return {
      ...response,
      items: response.items.map(transformTransaction),
    };
  },
};
