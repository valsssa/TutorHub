/**
 * Type definitions for the application
 */

export interface User {
  id: number;
  email: string;
  role: "student" | "tutor" | "admin";
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  avatar_url?: string | null;
  avatarUrl?: string | null;
  currency: string;
  timezone: string;
  first_name?: string | null;
  last_name?: string | null;
  country?: string | null;
  bio?: string | null;
  learning_goal?: string | null;
}

export interface AvatarApiResponse {
  avatar_url: string;
  expires_at: string;
}

export interface AvatarSignedUrl {
  avatarUrl: string;
  expiresAt: string;
}

export interface AvatarDeleteResponse {
  detail: string;
}

export interface TutorCertification {
  id: number;
  name: string;
  issuing_organization?: string;
  issue_date?: string;
  expiration_date?: string;
  credential_id?: string;
  credential_url?: string;
  document_url?: string;
}

export interface TutorEducation {
  id: number;
  institution: string;
  degree?: string;
  field_of_study?: string;
  start_year?: number;
  end_year?: number;
  description?: string;
  document_url?: string;
}

export interface TutorPricingOption {
  id: number;
  title: string;
  description?: string;
  duration_minutes: number;
  price: number;
}

export interface TutorProfile {
  id: number;
  user_id: number;
  name: string;
  title: string;
  headline?: string;
  bio?: string;
  description?: string;
  teaching_philosophy?: string;
  hourly_rate: number;
  experience_years: number;
  education?: string;
  languages: string[];
  video_url?: string;
  profile_photo_url?: string | null;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  is_approved: boolean;
  profile_status: "incomplete" | "pending_approval" | "under_review" | "approved" | "rejected";
  rejection_reason?: string;
  subjects?: TutorSubject[];
  certifications?: TutorCertification[];
  educations?: TutorEducation[];
  pricing_options?: TutorPricingOption[];
  availabilities?: TutorAvailability[];
  timezone?: string;
  version: number;
  created_at?: string;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TutorPublicSummary {
  id: number;
  user_id: number;
  first_name?: string | null;
  last_name?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  name?: string | null;
  title: string;
  headline?: string;
  bio?: string;
  hourly_rate: number;
  experience_years: number;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
  subjects: string[];
  profile_photo_url?: string | null;
  education?: string[];
  teaching_philosophy?: string;
  recent_review?: string;
  next_available_slots?: string[];
}

export interface TutorSubject {
  id: number;
  subject_id: number;
  subject_name: string;
  proficiency_level: string;
  years_experience: number;
}

export interface TutorAvailability {
  id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_recurring: boolean;
  timezone?: string;
}

export interface Subject {
  id: number;
  name: string;
  description?: string;
  category?: string;
  is_active: boolean;
}

export interface StudentProfile {
  id: number;
  user_id: number;
  phone?: string | null;
  bio?: string | null;
  grade_level?: string | null;
  school_name?: string | null;
  learning_goals?: string | null;
  interests?: string | null;
  total_sessions: number;
  credit_balance_cents?: number;
   preferred_language?: string | null;
   timezone: string;
  created_at?: string;
  updated_at?: string;
}

export interface Booking {
  id: number;
  tutor_profile_id: number;
  student_id: number;
  subject_id: number;
  start_time: string;
  end_time: string;
  topic?: string;
  notes?: string;
  hourly_rate: number;
  total_amount: number;
  status: "pending" | "confirmed" | "cancelled" | "completed";
  meeting_url?: string;
  pricing_option_id?: number;
  pricing_type?: string;
  // Immutable snapshot fields (populated by backend on booking creation)
  tutor_name?: string;
  tutor_title?: string;
  student_name?: string;
  subject_name?: string;
  pricing_snapshot?: string;
  agreement_terms?: string;
  // Decision tracking fields
  is_instant_booking?: boolean;
  confirmed_at?: string;
  confirmed_by?: number;
  cancellation_reason?: string;
  cancelled_at?: string;
  is_rebooked?: boolean;
  original_booking_id?: number;
  // Enhanced tutor view fields
  student_avatar_url?: string;
  student_language_level?: string;
  tutor_earnings?: number;
  lesson_type?: "trial" | "regular" | "package";
  student_timezone?: string;
  // Enhanced student view fields
  tutor_photo_url?: string;
  tutor_rating?: number;
  tutor_language?: string;
  tutor_total_lessons?: number;
  created_at: string;
  updated_at?: string;
}

export interface StudentPackage {
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
  status: "active" | "expired" | "exhausted" | "refunded";
  payment_intent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: number;
  booking_id: number;
  tutor_profile_id: number;
  student_id: number;
  rating: number;
  comment?: string;
  is_public: boolean;
  created_at: string;
}

export interface Message {
  id: number;
  sender_id: number;
  recipient_id: number;
  booking_id?: number;
  message: string;
  is_read: boolean;
  created_at: string;
  delivery_state?: "sent" | "delivered" | "read";
}

export interface MessageThread {
  other_user_id: number;
  other_user_email: string;
  other_user_first_name?: string | null;
  other_user_last_name?: string | null;
  other_user_avatar_url?: string | null;
  other_user_role?: string;
  booking_id?: number;
  last_message: string;
  last_message_time: string;
  last_sender_id?: number;
  unread_count: number;
  total_messages?: number;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  is_read: boolean;
  link?: string;
  created_at: string;
}

export interface FavoriteTutor {
  id: number;
  student_id: number;
  tutor_profile_id: number;
  created_at: string;
}

export interface ApiError {
  detail: string;
}
