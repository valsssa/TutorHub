import { api } from './client';
import type { Favorite, PaginatedResponse } from '@/types';

export interface FavoritesListParams {
  page?: number;
  page_size?: number;
}

export const favoritesApi = {
  // Get favorite tutors for current student (paginated)
  list: (params?: FavoritesListParams) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    const qs = searchParams.toString();
    return api.get<PaginatedResponse<Favorite>>(`/favorites${qs ? `?${qs}` : ''}`);
  },

  // Add a tutor to favorites
  add: (tutorProfileId: number) =>
    api.post<Favorite>('/favorites', { tutor_profile_id: tutorProfileId }),

  // Remove a tutor from favorites
  remove: (tutorProfileId: number) =>
    api.delete<void>(`/favorites/${tutorProfileId}`),

  // Check if a tutor is in favorites
  check: (tutorProfileId: number) =>
    api.get<Favorite>(`/favorites/${tutorProfileId}`).then(
      () => ({ is_favorite: true }),
      (error) => {
        if (error.status === 404) {
          return { is_favorite: false };
        }
        throw error;
      }
    ),
};
