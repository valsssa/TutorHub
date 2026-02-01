/**
 * Booking type definitions matching backend BookingDTO schema.
 * Based on booking_detail.md specification with four-field status system.
 */

// New four-field status system
export type SessionState =
  | "REQUESTED"  // Waiting for tutor response
  | "SCHEDULED"  // Confirmed, session upcoming
  | "ACTIVE"     // Session happening now
  | "ENDED"      // Session lifecycle complete
  | "EXPIRED"    // Request timed out (24h)
  | "CANCELLED"; // Explicitly cancelled

export type SessionOutcome =
  | "COMPLETED"        // Session happened successfully
  | "NOT_HELD"         // Session didn't happen
  | "NO_SHOW_STUDENT"  // Student didn't attend
  | "NO_SHOW_TUTOR";   // Tutor didn't attend

export type PaymentState =
  | "PENDING"            // Awaiting authorization
  | "AUTHORIZED"         // Funds held
  | "CAPTURED"           // Tutor earned payment
  | "VOIDED"             // Authorization released
  | "REFUNDED"           // Full refund issued
  | "PARTIALLY_REFUNDED"; // Partial refund issued

export type DisputeState =
  | "NONE"              // No dispute
  | "OPEN"              // Under review
  | "RESOLVED_UPHELD"   // Original decision stands
  | "RESOLVED_REFUNDED"; // Refund granted

export type CancelledByRole = "STUDENT" | "TUTOR" | "ADMIN" | "SYSTEM";

// Legacy status (for backward compatibility)
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

export type VideoProvider = "zoom" | "google_meet" | "teams" | "custom" | "manual";

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

  // New four-field status system
  session_state: SessionState;
  session_outcome?: SessionOutcome | null;
  payment_state: PaymentState;
  dispute_state: DisputeState;

  // Legacy status (for backward compatibility)
  status: string;

  // Cancellation info
  cancelled_by_role?: CancelledByRole | null;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;

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

  // Dispute information
  dispute_reason?: string | null;
  disputed_at?: string | null;

  // Attendance tracking
  tutor_joined_at?: string | null;
  student_joined_at?: string | null;

  // Video meeting provider
  video_provider?: "zoom" | "google_meet" | "teams" | "custom" | "manual" | null;
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

// Dispute request schemas
export interface DisputeCreateRequest {
  reason: string;
}

export interface DisputeResolveRequest {
  resolution: "RESOLVED_UPHELD" | "RESOLVED_REFUNDED";
  notes?: string;
  refund_amount_cents?: number;
}
