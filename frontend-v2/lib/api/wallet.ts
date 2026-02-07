import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  WalletBalance,
  WalletCheckoutRequest,
  WalletCheckoutResponse,
  Transaction,
  TransactionFilters,
  BackendTransaction,
  ConnectStatus,
  PayoutBalance,
  PayoutHistory,
  EarningsSummary,
  ConnectOnboardingLink,
  ConnectDashboardLink,
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

  // Tutor Connect endpoints
  getConnectStatus: () =>
    api.get<ConnectStatus>('/tutor/connect/status'),

  getPayoutBalance: () =>
    api.get<PayoutBalance>('/tutor/connect/balance'),

  getPayoutHistory: (limit = 10) =>
    api.get<PayoutHistory>(`/tutor/connect/payouts?limit=${limit}`),

  getEarningsSummary: () =>
    api.get<EarningsSummary>('/tutor/connect/earnings-summary'),

  createConnectAccount: (country = 'US') =>
    api.post<ConnectOnboardingLink>(`/tutor/connect/create?country=${country}`),

  getOnboardingLink: () =>
    api.get<ConnectOnboardingLink>('/tutor/connect/onboarding-link'),

  getDashboardLink: () =>
    api.get<ConnectDashboardLink>('/tutor/connect/dashboard-link'),
};
