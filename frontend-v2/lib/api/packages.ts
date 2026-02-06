import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  PurchasedPackage,
  PurchasePackageInput,
  MyPackageFilters,
} from '@/types';

export const packagesApi = {
  // Get current student's purchased packages
  getMyPackages: (filters: MyPackageFilters = {}) =>
    api.get<PurchasedPackage[]>(`/packages?${toQueryString(filters)}`),

  // Purchase a package (create StudentPackage)
  purchase: (data: PurchasePackageInput) =>
    api.post<{
      package: PurchasedPackage;
      warning?: string;
      active_booking_id?: number;
    }>('/packages', data),

  // Use a credit from a package
  useCredit: (packageId: number) =>
    api.patch<PurchasedPackage>(`/packages/${packageId}/use-credit`, {}),
};
