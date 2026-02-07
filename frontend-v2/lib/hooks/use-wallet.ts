import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { walletApi } from '@/lib/api/wallet';
import type { WalletCheckoutRequest, TransactionFilters } from '@/types/wallet';

export const walletKeys = {
  all: ['wallet'] as const,
  balance: () => [...walletKeys.all, 'balance'] as const,
  transactions: () => [...walletKeys.all, 'transactions'] as const,
  transactionList: (filters?: TransactionFilters) =>
    [...walletKeys.transactions(), filters ?? {}] as const,
  connect: () => [...walletKeys.all, 'connect'] as const,
  connectStatus: () => [...walletKeys.connect(), 'status'] as const,
  payoutBalance: () => [...walletKeys.connect(), 'payout-balance'] as const,
  payoutHistory: () => [...walletKeys.connect(), 'payout-history'] as const,
  earnings: () => [...walletKeys.connect(), 'earnings'] as const,
};

export function useWalletBalance(enabled = true) {
  return useQuery({
    queryKey: walletKeys.balance(),
    queryFn: walletApi.getBalance,
    enabled,
    refetchOnWindowFocus: true,
  });
}

export function useTransactions(filters?: TransactionFilters) {
  return useQuery({
    queryKey: walletKeys.transactionList(filters),
    queryFn: () => walletApi.getTransactions(filters),
  });
}

export function useCreateWalletCheckout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: WalletCheckoutRequest) => walletApi.createCheckout(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: walletKeys.balance() });
      queryClient.invalidateQueries({ queryKey: walletKeys.transactions() });
    },
  });
}

// Tutor Connect hooks
export function useConnectStatus(enabled = true) {
  return useQuery({
    queryKey: walletKeys.connectStatus(),
    queryFn: walletApi.getConnectStatus,
    enabled,
  });
}

export function usePayoutBalance(enabled = true) {
  return useQuery({
    queryKey: walletKeys.payoutBalance(),
    queryFn: walletApi.getPayoutBalance,
    enabled,
  });
}

export function usePayoutHistory(enabled = true) {
  return useQuery({
    queryKey: walletKeys.payoutHistory(),
    queryFn: () => walletApi.getPayoutHistory(10),
    enabled,
  });
}

export function useEarningsSummary(enabled = true) {
  return useQuery({
    queryKey: walletKeys.earnings(),
    queryFn: walletApi.getEarningsSummary,
    enabled,
  });
}

export function useCreateConnectAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (country: string | undefined) => walletApi.createConnectAccount(country),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: walletKeys.connectStatus() });
    },
  });
}

export function useGetDashboardLink() {
  return useMutation({
    mutationFn: () => walletApi.getDashboardLink(),
  });
}
