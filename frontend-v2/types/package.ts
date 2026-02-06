import type { TutorProfile } from './tutor';

export type PurchasedPackageStatus = 'active' | 'expired' | 'exhausted' | 'refunded';

// TutorPricingOption from backend (matches TutorPricingOptionResponse schema)
export interface PricingOption {
  id: number;
  title: string;
  description?: string;
  duration_minutes: number;
  price: number;
  validity_days?: number;
  extend_on_use?: boolean;
}

// Legacy Package type for compatibility
// Can be constructed from PricingOption + tutor context
export interface Package {
  id: number;
  tutor_profile_id: number;
  name?: string;
  description?: string;
  price: number;
  currency: string;
  duration_minutes?: number;
  sessions_count?: number;
  validity_days?: number;
  extend_on_use?: boolean;
  is_active: boolean;
  tutor?: TutorProfile;
  created_at: string;
  updated_at?: string;
}

// StudentPackage from backend
export interface PurchasedPackage {
  id: number;
  student_id: number;
  tutor_profile_id: number;
  pricing_option_id: number;
  sessions_purchased: number;
  sessions_remaining: number;
  sessions_used: number;
  purchase_price: number;
  purchased_at: string;
  expires_at?: string;
  status: PurchasedPackageStatus;
  payment_intent_id?: string;
}

export interface PurchasePackageInput {
  tutor_profile_id: number;
  pricing_option_id: number;
  payment_intent_id?: string;
  agreed_terms?: string;
}

export interface PackageFilters {
  tutor_profile_id?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface MyPackageFilters {
  status?: PurchasedPackageStatus;
}
