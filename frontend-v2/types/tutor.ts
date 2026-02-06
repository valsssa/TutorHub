import type { PricingOption } from './package';

/**
 * Valid tutor profile status values matching backend constraint.
 */
export type TutorProfileStatus =
  | 'incomplete'
  | 'pending_approval'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'archived';

export interface Subject {
  id: number;
  name: string;
}

export interface TutorProfile {
  id: number;
  user_id: number;
  // Name fields from backend - first_name/last_name
  first_name?: string;
  last_name?: string;
  // Legacy name fields for backwards compatibility
  name?: string;
  display_name?: string;
  title?: string;
  headline?: string;
  bio?: string;
  description?: string;
  hourly_rate: number;
  currency?: string;
  experience_years?: number;
  education?: string | string[];
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
  // Profile photos - backend uses profile_photo_url
  avatar_url?: string;
  profile_photo_url?: string;
  // Profile state
  is_approved: boolean;
  profile_status?: TutorProfileStatus;
  rejection_reason?: string;
  approved_at?: string;
  timezone?: string;
  version?: number;
  created_at?: string;
  // Extra fields from public profile
  recent_review?: string;
  next_available_slots?: string[];
}

export interface TutorFilters {
  // Subject filtering - can use either subject name (search_query) or subject_id
  subject?: string;
  subject_id?: number;
  // Price filtering - maps to backend min_rate/max_rate
  price_min?: number;
  price_max?: number;
  min_rating?: number;
  min_experience?: number;
  language?: string;
  search_query?: string;
  // Sort options: 'rating' (default), 'rate_asc', 'rate_desc', 'experience'
  sort_by?: 'rating' | 'rate_asc' | 'rate_desc' | 'experience';
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
