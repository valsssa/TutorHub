export interface Subject {
  id: number;
  name: string;
}

export interface TutorProfile {
  id: number;
  user_id: number;
  display_name: string;
  headline?: string;
  bio?: string;
  hourly_rate: number;
  currency: string;
  subjects: Subject[];
  average_rating: number;
  review_count: number;
  avatar_url?: string;
  is_approved: boolean;
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
