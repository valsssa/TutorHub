import type { Subject } from './tutor';

/**
 * Valid session states matching backend BookingStateMachine.
 * State flow: REQUESTED -> SCHEDULED -> ACTIVE -> ENDED
 * Terminal states: ENDED, CANCELLED, EXPIRED
 */
export type SessionState =
  | 'REQUESTED'
  | 'SCHEDULED'
  | 'ACTIVE'
  | 'ENDED'
  | 'EXPIRED'
  | 'CANCELLED';

export type SessionOutcome =
  | 'COMPLETED'
  | 'NOT_HELD'
  | 'NO_SHOW_STUDENT'
  | 'NO_SHOW_TUTOR';

/**
 * Valid payment states matching backend PaymentState enum.
 */
export type PaymentState =
  | 'PENDING'
  | 'AUTHORIZED'
  | 'CAPTURED'
  | 'VOIDED'
  | 'REFUNDED'
  | 'PARTIALLY_REFUNDED';

export type DisputeState =
  | 'NONE'
  | 'OPEN'
  | 'RESOLVED_UPHELD'
  | 'RESOLVED_REFUNDED';

export type LessonType = 'TRIAL' | 'REGULAR' | 'PACKAGE';

export interface TutorInfo {
  id: number;
  name: string;
  display_name?: string;
  avatar_url?: string;
  rating_avg: number;
  title?: string;
  headline?: string;
}

export interface StudentInfo {
  id: number;
  name: string;
  avatar_url?: string;
  level?: string;
}

export interface Booking {
  id: number;
  version: number;
  lesson_type: LessonType;
  session_state: SessionState;
  session_outcome?: SessionOutcome;
  payment_state: PaymentState;
  dispute_state: DisputeState;
  status: string; // Computed from session_state + session_outcome for display
  cancelled_by_role?: string;
  cancelled_at?: string;
  cancellation_reason?: string;
  // Time fields (ISO UTC strings)
  start_at: string;
  end_at: string;
  // Legacy time field aliases
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  student_tz: string;
  tutor_tz: string;
  // Pricing
  rate_cents: number;
  rate_locked_at?: string;
  currency: string;
  platform_fee_pct: number;
  platform_fee_cents: number;
  tutor_earnings_cents: number;
  total_amount?: number; // Computed total in dollars
  // Session details
  join_url?: string;
  notes_student?: string;
  notes_tutor?: string;
  student_message?: string; // Alias for notes_student
  tutor: TutorInfo;
  student: StudentInfo;
  student_id?: number; // Direct reference for display
  subject?: Subject; // Full subject object
  subject_name?: string;
  topic?: string;
  created_at: string;
  updated_at: string;
  // Dispute info
  dispute_reason?: string;
  disputed_at?: string;
  // Attendance tracking
  tutor_joined_at?: string;
  student_joined_at?: string;
  video_provider?: string;
}

export interface CreateBookingInput {
  tutor_profile_id?: number;
  tutor_id?: number; // Alternative field name
  subject_id?: number;
  start_at?: string; // ISO datetime string (UTC)
  start_time?: string; // Alternative field name
  duration_minutes: number; // 25, 30, 45, 50, 60, 90, 120
  lesson_type?: LessonType;
  notes_student?: string;
  use_package_id?: number;
}

export interface BookingFilters {
  status?: string; // 'upcoming', 'pending', 'completed', 'cancelled', 'active', 'scheduled'
  role?: 'student' | 'tutor';
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}

// Response structure from backend
export interface BookingListResponse {
  bookings: Booking[];
  items?: Booking[]; // Alternative field name used in some responses
  total: number;
  page: number;
  page_size: number;
}
