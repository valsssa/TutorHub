import { api } from './client';

export type VideoProvider = 'zoom' | 'google_meet' | 'teams' | 'custom' | 'manual';

export interface VideoSettings {
  preferred_video_provider: VideoProvider;
  custom_meeting_url_template: string | null;
  video_provider_configured: boolean;
  zoom_available: boolean;
  google_calendar_connected: boolean;
}

export interface VideoSettingsUpdateRequest {
  preferred_video_provider: VideoProvider;
  custom_meeting_url_template?: string | null;
}

export interface VideoProviderOption {
  value: VideoProvider;
  label: string;
  description: string;
  requires_setup: boolean;
  is_available: boolean;
}

export interface VideoProvidersListResponse {
  providers: VideoProviderOption[];
  current_provider: VideoProvider;
}

export const videoSettingsApi = {
  /**
   * Get tutor's video meeting settings
   */
  getVideoSettings: () =>
    api.get<VideoSettings>('/tutor/settings/video'),

  /**
   * Update tutor's video meeting settings
   */
  updateVideoSettings: (data: VideoSettingsUpdateRequest) =>
    api.put<VideoSettings>('/tutor/settings/video', data),

  /**
   * List available video providers with their status
   */
  listProviders: () =>
    api.get<VideoProvidersListResponse>('/tutor/settings/video/providers'),
};
