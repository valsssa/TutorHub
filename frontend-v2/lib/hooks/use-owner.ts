import { useQuery } from '@tanstack/react-query';
import { ownerApi, type OwnerDashboardParams } from '@/lib/api/owner';

export const ownerKeys = {
  all: ['owner'] as const,
  dashboard: (params?: OwnerDashboardParams) =>
    [...ownerKeys.all, 'dashboard', params] as const,
  revenue: (params?: OwnerDashboardParams) =>
    [...ownerKeys.all, 'revenue', params] as const,
  growth: (params?: OwnerDashboardParams) =>
    [...ownerKeys.all, 'growth', params] as const,
  health: () => [...ownerKeys.all, 'health'] as const,
  commissionTiers: () => [...ownerKeys.all, 'commission-tiers'] as const,
};

/**
 * Fetch complete owner dashboard data
 */
export function useOwnerDashboard(params: OwnerDashboardParams = {}) {
  return useQuery({
    queryKey: ownerKeys.dashboard(params),
    queryFn: () => ownerApi.getDashboard(params),
    staleTime: 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
  });
}

/**
 * Fetch revenue metrics only
 */
export function useOwnerRevenue(params: OwnerDashboardParams = {}) {
  return useQuery({
    queryKey: ownerKeys.revenue(params),
    queryFn: () => ownerApi.getRevenue(params),
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch growth metrics only
 */
export function useOwnerGrowth(params: OwnerDashboardParams = {}) {
  return useQuery({
    queryKey: ownerKeys.growth(params),
    queryFn: () => ownerApi.getGrowth(params),
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch marketplace health indicators
 */
export function useOwnerHealth() {
  return useQuery({
    queryKey: ownerKeys.health(),
    queryFn: ownerApi.getHealth,
    staleTime: 60 * 1000,
  });
}

/**
 * Fetch commission tier breakdown
 */
export function useCommissionTiers() {
  return useQuery({
    queryKey: ownerKeys.commissionTiers(),
    queryFn: ownerApi.getCommissionTiers,
    staleTime: 5 * 60 * 1000, // 5 minutes - less volatile data
  });
}
