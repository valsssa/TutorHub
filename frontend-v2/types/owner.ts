/**
 * Owner Dashboard Types
 *
 * Matches backend models from backend/modules/admin/owner/router.py
 */

export interface RevenueMetrics {
  total_gmv_cents: number;
  total_platform_fees_cents: number;
  total_tutor_payouts_cents: number;
  average_booking_value_cents: number;
  period_days: number;
}

export interface GrowthMetrics {
  total_users: number;
  new_users_period: number;
  total_tutors: number;
  approved_tutors: number;
  total_students: number;
  total_bookings: number;
  completed_bookings: number;
  completion_rate: number;
  period_days: number;
}

export interface MarketplaceHealth {
  average_tutor_rating: number;
  tutors_with_bookings_pct: number;
  repeat_booking_rate: number;
  cancellation_rate: number;
  no_show_rate: number;
  average_response_time_hours: number | null;
}

export interface CommissionTierBreakdown {
  standard_tutors: number;
  silver_tutors: number;
  gold_tutors: number;
  total_tutors: number;
}

export interface OwnerDashboard {
  revenue: RevenueMetrics;
  growth: GrowthMetrics;
  health: MarketplaceHealth;
  commission_tiers: CommissionTierBreakdown;
  generated_at: string;
}

export interface SystemHealthService {
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  latency?: string;
  message?: string;
}

export interface SystemHealth {
  services: SystemHealthService[];
  overall_status: 'healthy' | 'warning' | 'critical';
  checked_at: string;
}

export interface AdminUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  last_active?: string;
  created_at: string;
}

export interface RevenueChartDataPoint {
  date: string;
  revenue: number;
  bookings: number;
}
