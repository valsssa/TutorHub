import type { PricingOption } from './package';

export interface Subject {
  id: number;
  name: string;
}

export interface TutorProfile {
  id: number;
  user_id: number;
  // Name fields - backend uses various naming conventions
  name?: string;
  display_name?: string;
  title?: string;
  headline?: string;
  bio?: string;
  description?: string;
  hourly_rate: number;
  currency?: string;
  experience_years?: number;
  education?: string;
  languages?: string[];
  video_url?: string;
  subjects: Subject[];
  // Pricing options (session packages offered by tutor)
  pricing_options?: PricingOption[];
  // Rating and stats
  average_rating: number;
  total_reviews?: number;
  review_count?: number; // Alias for total_reviews
  total_sessions?: number;
  // Profile state
  avatar_url?: string;
  profile_photo_url?: string; // Alternative field name
  is_approved: boolean;
  profile_status?: string;
  rejection_reason?: string;
  approved_at?: string;
  timezone?: string;
  version?: number;
  created_at?: string;
}

export interface TutorFilters {
  subject?: string;
  price_min?: number;
  price_max?: number;
  sort_by?: 'rating' | 'price' | 'experience';
  page?: number;
  page_size?: number;
}

export interface AvailabilitySlot {
  id: number;
  tutor_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
}
