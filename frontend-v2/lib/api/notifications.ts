import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type {
  NotificationFilters,
  NotificationListResponse,
  NotificationStats,
} from '@/types/notification';

export const notificationsApi = {
  // Get notifications with pagination and filtering
  getNotifications: (filters?: NotificationFilters) => {
    const params: Record<string, string | number | boolean> = {};
    if (filters?.category) params.category = filters.category;
    if (filters?.unread_only) params.unread_only = filters.unread_only;
    if (filters?.skip !== undefined) params.skip = filters.skip;
    if (filters?.limit !== undefined) params.limit = filters.limit;
    const query = Object.keys(params).length ? `?${toQueryString(params)}` : '';
    return api.get<NotificationListResponse>(`/notifications${query}`);
  },

  // Mark a single notification as read (PATCH, not POST)
  markAsRead: (id: number) =>
    api.patch<{ message: string }>(`/notifications/${id}/read`, {}),

  // Mark all notifications as read
  markAllAsRead: () =>
    api.patch<{ message: string }>('/notifications/mark-all-read', {}),

  // Dismiss a notification
  dismiss: (id: number) =>
    api.patch<{ message: string }>(`/notifications/${id}/dismiss`, {}),

  // Delete a notification
  delete: (id: number) =>
    api.delete<{ message: string }>(`/notifications/${id}`),

  // Get unread notification count
  getUnreadCount: () =>
    api.get<NotificationStats>('/notifications/unread-count'),

  // Get notification preferences
  getPreferences: () =>
    api.get<{
      email_enabled: boolean;
      push_enabled: boolean;
      sms_enabled: boolean;
      session_reminders_enabled: boolean;
      booking_requests_enabled: boolean;
      learning_nudges_enabled: boolean;
      review_prompts_enabled: boolean;
      achievements_enabled: boolean;
      marketing_enabled: boolean;
      quiet_hours_start?: string;
      quiet_hours_end?: string;
      preferred_notification_time?: string;
      max_daily_notifications: number;
      max_weekly_nudges: number;
    }>('/notifications/preferences'),

  // Update notification preferences
  updatePreferences: (preferences: Partial<{
    email_enabled: boolean;
    push_enabled: boolean;
    sms_enabled: boolean;
    session_reminders_enabled: boolean;
    booking_requests_enabled: boolean;
    learning_nudges_enabled: boolean;
    review_prompts_enabled: boolean;
    achievements_enabled: boolean;
    marketing_enabled: boolean;
    quiet_hours_start: string;
    quiet_hours_end: string;
    preferred_notification_time: string;
    max_daily_notifications: number;
    max_weekly_nudges: number;
  }>) =>
    api.put('/notifications/preferences', preferences),
};
