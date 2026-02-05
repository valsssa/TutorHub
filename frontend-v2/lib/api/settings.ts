import { api, getCsrfToken } from './client';
import type { User } from '@/types';

export interface NotificationPreferences {
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
}

export interface AvatarResponse {
  avatar_url: string | null;
}

export interface AvatarDeleteResponse {
  message: string;
  avatar_url: string | null;
}

export const settingsApi = {
  // Profile settings
  updateProfile: (data: {
    first_name?: string;
    last_name?: string;
    timezone?: string;
    currency?: string;
  }) => api.put<User>('/auth/me', data),

  // Avatar management
  uploadAvatar: async (file: File): Promise<AvatarResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const csrfToken = getCsrfToken();
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/users/me/avatar`,
      {
        method: 'POST',
        headers: {
          // CSRF token for state-changing request
          ...(csrfToken && { 'X-CSRF-Token': csrfToken }),
        },
        body: formData,
        credentials: 'include', // Include HttpOnly cookies
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  getAvatar: () => api.get<AvatarResponse>('/users/me/avatar'),

  deleteAvatar: () => api.delete<AvatarDeleteResponse>('/users/me/avatar'),

  // Notification preferences
  getNotificationPreferences: () =>
    api.get<NotificationPreferences>('/notifications/preferences'),

  updateNotificationPreferences: (preferences: Partial<NotificationPreferences>) =>
    api.put<NotificationPreferences>('/notifications/preferences', preferences),

  // Password reset request (since no change-password endpoint exists)
  requestPasswordReset: (email: string) =>
    api.post<{ message: string }>('/auth/password/reset-request', { email }),
};
