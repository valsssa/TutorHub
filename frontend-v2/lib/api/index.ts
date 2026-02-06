export { api, ApiError } from './client';
export { authApi } from './auth';
export { tutorsApi } from './tutors';
export { bookingsApi } from './bookings';
export { messagesApi } from './messages';
export { reviewsApi } from './reviews';
export { packagesApi } from './packages';
export { favoritesApi } from './favorites';
export { walletApi } from './wallet';
export { searchApi } from './search';
export { notificationsApi } from './notifications';
export { adminApi } from './admin';
export { ownerApi } from './owner';
export { settingsApi, type NotificationPreferences, type AvatarResponse, type AvatarDeleteResponse } from './settings';
export {
  videoSettingsApi,
  type VideoProvider,
  type VideoSettings,
  type VideoSettingsUpdateRequest,
  type VideoProviderOption,
  type VideoProvidersListResponse,
} from './video-settings';
export { studentNotesApi } from './student-notes';
export {
  integrationsApi,
  type ZoomConnectionStatus,
  type CalendarConnectionStatus,
  type CalendarAuthURLResponse,
} from './integrations';
