import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { packagesApi } from '@/lib/api';
import type { MyPackageFilters, PurchasePackageInput } from '@/types';

export const packageKeys = {
  all: ['packages'] as const,
  lists: () => [...packageKeys.all, 'list'] as const,
  myPackages: () => [...packageKeys.all, 'my-packages'] as const,
  myPackagesList: (filters: MyPackageFilters) =>
    [...packageKeys.myPackages(), filters] as const,
};

export function useMyPackages(filters: MyPackageFilters = {}) {
  return useQuery({
    queryKey: packageKeys.myPackagesList(filters),
    queryFn: () => packagesApi.getMyPackages(filters),
  });
}

export function usePurchasePackage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PurchasePackageInput) => packagesApi.purchase(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: packageKeys.myPackages() });
    },
  });
}

export function useUsePackageCredit() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (packageId: number) => packagesApi.useCredit(packageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: packageKeys.myPackages() });
    },
  });
}
