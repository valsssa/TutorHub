/**
 * Type definitions for owner dashboard
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
  standard_tutors: number;  // 20% fee: < $1,000 earnings
  silver_tutors: number;    // 15% fee: $1,000-$4,999
  gold_tutors: number;      // 10% fee: $5,000+
  total_tutors: number;
}

export interface OwnerDashboard {
  revenue: RevenueMetrics;
  growth: GrowthMetrics;
  health: MarketplaceHealth;
  commission_tiers: CommissionTierBreakdown;
  generated_at: string;
}
