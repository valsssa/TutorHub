import { api } from './client';
import type { Favorite } from '@/types';

export const favoritesApi = {
  // Get all favorite tutors for current student
  list: () =>
    api.get<Favorite[]>('/favorites'),

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
