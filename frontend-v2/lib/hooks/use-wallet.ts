import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { walletApi } from '@/lib/api/wallet';
import type { WalletCheckoutRequest, TransactionFilters } from '@/types/wallet';

export const walletKeys = {
  all: ['wallet'] as const,
  balance: () => [...walletKeys.all, 'balance'] as const,
  transactions: () => [...walletKeys.all, 'transactions'] as const,
  transactionList: (filters?: TransactionFilters) =>
    [...walletKeys.transactions(), filters ?? {}] as const,
};

export function useWalletBalance() {
  return useQuery({
    queryKey: walletKeys.balance(),
    queryFn: walletApi.getBalance,
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
