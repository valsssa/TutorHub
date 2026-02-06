import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi, type NotificationPreferences } from '@/lib/api/settings';
import { authKeys } from './use-auth';

export const settingsKeys = {
  all: ['settings'] as const,
  notificationPreferences: () => [...settingsKeys.all, 'notification-preferences'] as const,
  avatar: () => [...settingsKeys.all, 'avatar'] as const,
};

export function useNotificationPreferences() {
  return useQuery({
    queryKey: settingsKeys.notificationPreferences(),
    queryFn: settingsApi.getNotificationPreferences,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preferences: Partial<NotificationPreferences>) =>
      settingsApi.updateNotificationPreferences(preferences),
    onSuccess: (data) => {
      queryClient.setQueryData(settingsKeys.notificationPreferences(), data);
    },
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => settingsApi.uploadAvatar(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.avatar() });
    },
  });
}

export function useDeleteAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => settingsApi.deleteAvatar(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.me() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.avatar() });
    },
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: (email: string) => settingsApi.requestPasswordReset(email),
  });
}
