import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  integrationsApi,
  type CalendarConnectionStatus,
} from '@/lib/api/integrations';
import { videoSettingsKeys } from './use-video-settings';

export const integrationKeys = {
  all: ['integrations'] as const,
  zoom: () => [...integrationKeys.all, 'zoom'] as const,
  zoomStatus: () => [...integrationKeys.zoom(), 'status'] as const,
  calendar: () => [...integrationKeys.all, 'calendar'] as const,
  calendarStatus: () => [...integrationKeys.calendar(), 'status'] as const,
};

// ============================================================================
// Zoom Hooks
// ============================================================================

/**
 * Hook to fetch Zoom connection status
 */
export function useZoomStatus() {
  return useQuery({
    queryKey: integrationKeys.zoomStatus(),
    queryFn: integrationsApi.getZoomStatus,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================================
// Google Calendar Hooks
// ============================================================================

/**
 * Hook to fetch Google Calendar connection status
 */
export function useCalendarStatus() {
  return useQuery({
    queryKey: integrationKeys.calendarStatus(),
    queryFn: integrationsApi.getCalendarStatus,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to connect Google Calendar (returns auth URL)
 */
export function useConnectCalendar() {
  return useMutation({
    mutationFn: integrationsApi.connectCalendar,
    onSuccess: (data) => {
      // Redirect to Google OAuth
      window.location.href = data.authorization_url;
    },
  });
}

/**
 * Hook to disconnect Google Calendar
 */
export function useDisconnectCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: integrationsApi.disconnectCalendar,
    onSuccess: () => {
      // Update cache to reflect disconnected state
      queryClient.setQueryData<CalendarConnectionStatus>(
        integrationKeys.calendarStatus(),
        {
          is_connected: false,
          calendar_email: null,
          connected_at: null,
          can_create_events: false,
        }
      );
      // Also invalidate video settings since they depend on calendar status
      queryClient.invalidateQueries({ queryKey: videoSettingsKeys.all });
    },
  });
}

// ============================================================================
// Combined Hooks
// ============================================================================

/**
 * Hook to fetch all integration statuses
 */
export function useIntegrations() {
  const zoom = useZoomStatus();
  const calendar = useCalendarStatus();

  return {
    zoom: zoom.data,
    calendar: calendar.data,
    isLoading: zoom.isLoading || calendar.isLoading,
    isError: zoom.isError || calendar.isError,
    refetch: () => {
      zoom.refetch();
      calendar.refetch();
    },
  };
}
