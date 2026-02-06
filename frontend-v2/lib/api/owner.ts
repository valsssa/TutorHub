import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  OwnerDashboard,
  RevenueMetrics,
  GrowthMetrics,
  MarketplaceHealth,
  CommissionTierBreakdown,
} from '@/types/owner';

export interface OwnerDashboardParams {
  period_days?: number;
}

export const ownerApi = {
  /**
   * Get complete owner dashboard with all metrics
   */
  getDashboard: (params: OwnerDashboardParams = {}) =>
    api.get<OwnerDashboard>(`/owner/dashboard?${toQueryString(params)}`),

  /**
   * Get revenue metrics only
   */
  getRevenue: (params: OwnerDashboardParams = {}) =>
    api.get<RevenueMetrics>(`/owner/revenue?${toQueryString(params)}`),

  /**
   * Get growth metrics only
   */
  getGrowth: (params: OwnerDashboardParams = {}) =>
    api.get<GrowthMetrics>(`/owner/growth?${toQueryString(params)}`),

  /**
   * Get marketplace health indicators
   */
  getHealth: () =>
    api.get<MarketplaceHealth>('/owner/health'),

  /**
   * Get commission tier breakdown
   */
  getCommissionTiers: () =>
    api.get<CommissionTierBreakdown>('/owner/commission-tiers'),
};
