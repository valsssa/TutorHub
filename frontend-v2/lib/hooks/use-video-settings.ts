import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  videoSettingsApi,
  type VideoSettings,
  type VideoSettingsUpdateRequest,
} from '@/lib/api/video-settings';

export const videoSettingsKeys = {
  all: ['video-settings'] as const,
  settings: () => [...videoSettingsKeys.all, 'settings'] as const,
  providers: () => [...videoSettingsKeys.all, 'providers'] as const,
};

/**
 * Hook to fetch tutor's video settings
 */
export function useVideoSettings() {
  return useQuery({
    queryKey: videoSettingsKeys.settings(),
    queryFn: videoSettingsApi.getVideoSettings,
  });
}

/**
 * Hook to update tutor's video settings
 */
export function useUpdateVideoSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VideoSettingsUpdateRequest) =>
      videoSettingsApi.updateVideoSettings(data),
    onSuccess: (data: VideoSettings) => {
      queryClient.setQueryData(videoSettingsKeys.settings(), data);
      // Also invalidate providers list in case availability changed
      queryClient.invalidateQueries({ queryKey: videoSettingsKeys.providers() });
    },
  });
}

/**
 * Hook to fetch available video providers
 */
export function useVideoProviders() {
  return useQuery({
    queryKey: videoSettingsKeys.providers(),
    queryFn: videoSettingsApi.listProviders,
  });
}
