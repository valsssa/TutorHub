import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type { PaginatedResponse } from '@/types';
import type { TutorProfile, TutorFilters, AvailabilitySlot, Subject } from '@/types';

export const tutorsApi = {
  // List approved tutors with filtering and pagination
  list: (filters: TutorFilters = {}) =>
    api.get<PaginatedResponse<TutorProfile>>(`/tutors?${toQueryString(filters)}`),

  // Get a single tutor's public profile by ID
  get: (id: number) =>
    api.get<TutorProfile>(`/tutors/${id}`),

  // Get a tutor's public profile (explicit public endpoint)
  getPublic: (id: number) =>
    api.get<TutorProfile>(`/tutors/${id}/public`),

  // Get tutor's availability
  getAvailability: (tutorId: number, weekStart?: string) => {
    const params = weekStart ? `?week_start=${weekStart}` : '';
    return api.get<AvailabilitySlot[]>(`/tutors/${tutorId}/availability${params}`);
  },

  // Get all active subjects
  getSubjects: () =>
    api.get<Subject[]>('/subjects'),

  // Get current tutor's own profile (requires tutor role)
  getMyProfile: () =>
    api.get<TutorProfile>('/tutors/me/profile'),

  // Update current tutor's about section
  updateAbout: (data: {
    title?: string;
    headline?: string;
    bio?: string;
    languages?: string[];
    experience_years?: number;
  }) =>
    api.patch<TutorProfile>('/tutors/me/about', data),

  // Update current tutor's description
  updateDescription: (description: string) =>
    api.patch<TutorProfile>('/tutors/me/description', { description }),

  // Update current tutor's video URL
  updateVideo: (video_url: string) =>
    api.patch<TutorProfile>('/tutors/me/video', { video_url }),

  // Update current tutor's pricing
  updatePricing: (data: {
    hourly_rate?: number;
    trial_session_rate?: number;
    currency?: string;
  }) =>
    api.patch<TutorProfile>('/tutors/me/pricing', data),

  // Replace tutor subjects
  replaceSubjects: (subjects: Array<{ subject_id: number; proficiency_level?: string }>) =>
    api.put<TutorProfile>('/tutors/me/subjects', subjects),

  // Replace tutor availability
  updateAvailability: (slots: Omit<AvailabilitySlot, 'id' | 'tutor_id'>[]) =>
    api.put<TutorProfile>('/tutors/me/availability', { slots }),

  // Submit profile for admin review
  submitForReview: () =>
    api.post<TutorProfile>('/tutors/me/submit', {}),

  // Get tutor reviews
  getReviews: (tutorId: number, page = 1, pageSize = 20) =>
    api.get(`/tutors/${tutorId}/reviews?page=${page}&page_size=${pageSize}`),

  // Get featured tutors (for homepage)
  getFeatured: (limit = 6) =>
    api.get<PaginatedResponse<TutorProfile>>(`/tutors?sort_by=rating&page_size=${limit}`).then(
      (response) => response.items ?? []
    ),
};
