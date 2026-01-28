/**
 * Booking type definitions matching backend BookingDTO schema.
 * Based on booking_detail.md specification.
 */

export type BookingStatus =
  | "PENDING"
  | "CONFIRMED"
  | "CANCELLED_BY_STUDENT"
  | "CANCELLED_BY_TUTOR"
  | "NO_SHOW_STUDENT"
  | "NO_SHOW_TUTOR"
  | "COMPLETED"
  | "REFUNDED"
  // Legacy statuses for backward compatibility
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show";

export type LessonType = "TRIAL" | "REGULAR" | "PACKAGE";

export interface TutorInfo {
  id: number;
  name: string;
  avatar_url?: string | null;
  rating_avg: number;
  title?: string | null;
}

export interface StudentInfo {
  id: number;
  name: string;
  avatar_url?: string | null;
  level?: string | null;
}

export interface BookingDTO {
  id: number;
  lesson_type: LessonType;
  status: string;
  start_at: string; // ISO datetime
  end_at: string; // ISO datetime
  student_tz: string;
  tutor_tz: string;
  rate_cents: number;
  currency: string;
  platform_fee_pct: number;
  platform_fee_cents: number;
  tutor_earnings_cents: number;
  join_url?: string | null;
  notes_student?: string | null;
  notes_tutor?: string | null;
  tutor: TutorInfo;
  student: StudentInfo;
  subject_name?: string | null;
  topic?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingListResponse {
  bookings: BookingDTO[];
  total: number;
  page: number;
  page_size: number;
}

export interface BookingCreateRequest {
  tutor_profile_id: number;
  start_at: string;
  duration_minutes: number;
  lesson_type?: LessonType;
  subject_id?: number;
  notes_student?: string;
  use_package_id?: number;
}

export interface BookingCancelRequest {
  reason?: string;
}

export interface BookingRescheduleRequest {
  new_start_at: string;
}
