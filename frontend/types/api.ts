/**
 * API response type definitions
 */

export interface DashboardStats {
  total_users: number;
  total_tutors: number;
  total_students: number;
  active_sessions: number;
  total_revenue: number;
  pending_approvals: number;
  recent_signups: number;
  conversion_rate: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
  errors?: Record<string, string[]>;
}

export interface PaginatedApiResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SuccessResponse {
  message: string;
  detail?: string;
}

export interface TutorListParams {
  search?: string;
  subject?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  languages?: string[];
  availability?: string;
  page?: number;
  limit?: number;
  sort_by?: 'price' | 'rating' | 'experience' | 'name';
  order?: 'asc' | 'desc';
}

export interface MessageSendResponse {
  id: number;
  content: string;
  sender_id: number;
  recipient_id: number;
  created_at: string;
  read_at: string | null;
  booking_id?: number | null;
}

export interface UnreadCountResponse {
  total: number;
  by_thread?: Record<number, number>;
}
