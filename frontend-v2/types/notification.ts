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
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  action_url?: string;
}

export interface NotificationFilters {
  type?: NotificationType;
  read?: boolean;
  page?: number;
  page_size?: number;
}

export interface NotificationStats {
  unread_count: number;
}
