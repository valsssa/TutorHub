import type { TutorProfile } from './tutor';

export type PurchasedPackageStatus = 'active' | 'expired' | 'exhausted' | 'cancelled';

export interface Package {
  id: number;
  tutor_id: number;
  name: string;
  description?: string;
  sessions_count: number;
  price: number;
  currency: string;
  discount_percent: number;
  validity_days: number;
  is_active: boolean;
  tutor?: TutorProfile;
  created_at: string;
  updated_at?: string;
}

export interface PurchasedPackage {
  id: number;
  package_id: number;
  student_id: number;
  sessions_remaining: number;
  sessions_used: number;
  expires_at: string;
  status: PurchasedPackageStatus;
  purchased_at: string;
  package?: Package;
}

export interface PurchasePackageInput {
  package_id: number;
}

export interface PackageFilters {
  tutor_id?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface MyPackageFilters {
  status?: PurchasedPackageStatus;
  page?: number;
  page_size?: number;
}
