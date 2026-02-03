import type { TutorProfile, Subject } from './tutor';

export type SessionState =
  | 'pending_tutor'
  | 'pending_student'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'expired'
  | 'no_show';

export type PaymentState =
  | 'pending'
  | 'authorized'
  | 'captured'
  | 'refunded'
  | 'released_to_tutor'
  | 'failed';

export interface Booking {
  id: number;
  student_id: number;
  tutor_id: number;
  subject_id: number;
  start_time: string;
  end_time: string;
  duration_minutes: number;
  session_state: SessionState;
  payment_state: PaymentState;
  total_amount: number;
  currency: string;
  student_message?: string;
  tutor?: TutorProfile;
  subject?: Subject;
  created_at: string;
}

export interface CreateBookingInput {
  tutor_id: number;
  subject_id: number;
  start_time: string;
  duration: '30' | '60' | '90' | '120';
  message?: string;
  package_id?: number;
}

export interface BookingFilters {
  status?: SessionState;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}
