export type NotificationType =
  | 'booking_request'
  | 'booking_confirmed'
  | 'booking_cancelled'
  | 'message'
  | 'review'
  | 'payment'
  | 'system';

export interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  link?: string;
  is_read: boolean;
  read?: boolean; // Alias for is_read, backward compat
  category?: string;
  priority?: number;
  action_url?: string;
  action_label?: string;
  read_at?: string;
  created_at: string;
}

export interface NotificationFilters {
  category?: string;
  type?: NotificationType;
  unread_only?: boolean;
  read?: boolean; // Legacy filter
  skip?: number;
  limit?: number;
  page?: number;
  page_size?: number;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationStats {
  count: number;
  unread_count?: number; // Alias for count
}
