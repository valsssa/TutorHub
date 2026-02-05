export interface Review {
  id: number;
  booking_id: number;
  student_id: number;
  tutor_profile_id: number;
  rating: number;
  comment?: string | null;
  booking_snapshot?: string; // JSON string with session details at time of review
  is_public: boolean;
  created_at: string;
}

export interface CreateReviewInput {
  booking_id: number;
  rating: number;
  comment?: string;
}

export interface ReviewFilters {
  tutor_id?: number;
  min_rating?: number;
  page?: number;
  page_size?: number;
}

export interface ReviewStats {
  average_rating: number;
  total_reviews: number;
  rating_distribution: {
    1: number;
    2: number;
    3: number;
    4: number;
    5: number;
  };
}
