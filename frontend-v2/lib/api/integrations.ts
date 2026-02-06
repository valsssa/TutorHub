import { api } from './client';

// ============================================================================
// Zoom Types
// ============================================================================

export interface ZoomConnectionStatus {
  is_connected: boolean;
  zoom_email: string | null;
  connected_at: string | null;
}

// ============================================================================
// Google Calendar Types
// ============================================================================

export interface CalendarConnectionStatus {
  is_connected: boolean;
  calendar_email: string | null;
  connected_at: string | null;
  can_create_events: boolean;
}

export interface CalendarAuthURLResponse {
  authorization_url: string;
  state: string;
}

// ============================================================================
// API Methods
// ============================================================================

export const integrationsApi = {
  // Zoom
  /**
   * Get Zoom connection status
   */
  getZoomStatus: () =>
    api.get<ZoomConnectionStatus>('/integrations/zoom/status'),

  /**
   * Note: Zoom uses Server-to-Server OAuth, so there's no user connection flow.
   * The status endpoint indicates if Zoom is configured at the platform level.
   */

  // Google Calendar
  /**
   * Get Google Calendar connection status
   */
  getCalendarStatus: () =>
    api.get<CalendarConnectionStatus>('/integrations/calendar/status'),

  /**
   * Get Google Calendar authorization URL to start OAuth flow
   */
  connectCalendar: () =>
    api.get<CalendarAuthURLResponse>('/integrations/calendar/connect'),

  /**
   * Disconnect Google Calendar
   */
  disconnectCalendar: () =>
    api.delete<{ message: string }>('/integrations/calendar/disconnect'),
};
