import { api } from './client';
import { toQueryString } from '@/lib/utils';
import type { PaginatedResponse } from '@/types';
import type { TutorProfile, TutorFilters, AvailabilitySlot, Subject } from '@/types';

/**
 * Map frontend filter parameters to backend API parameters.
 * Frontend uses: subject, price_min, price_max
 * Backend expects: subject_id, min_rate, max_rate, search_query
 */
function mapFiltersToBackend(filters: TutorFilters): Record<string, string | number | undefined> {
  const mapped: Record<string, string | number | undefined> = {};

  // Map subject name to search_query for text search
  if (filters.subject) {
    mapped.search_query = filters.subject;
  }

  // Map subject_id if provided directly
  if (filters.subject_id) {
    mapped.subject_id = filters.subject_id;
  }

  // Map price filters to rate filters
  if (filters.price_min !== undefined) {
    mapped.min_rate = filters.price_min;
  }
  if (filters.price_max !== undefined) {
    mapped.max_rate = filters.price_max;
  }

  // Map other filters directly
  if (filters.min_rating !== undefined) {
    mapped.min_rating = filters.min_rating;
  }
  if (filters.min_experience !== undefined) {
    mapped.min_experience = filters.min_experience;
  }
  if (filters.language) {
    mapped.language = filters.language;
  }
  if (filters.search_query) {
    mapped.search_query = filters.search_query;
  }

  // Map sort_by - keep as-is since backend supports rating, rate_asc, rate_desc, experience
  if (filters.sort_by) {
    mapped.sort_by = filters.sort_by;
  }

  // Pagination
  if (filters.page) {
    mapped.page = filters.page;
  }
  if (filters.page_size) {
    mapped.page_size = filters.page_size;
  }

  return mapped;
}

/**
 * Transform backend tutor response to ensure frontend-expected fields exist.
 * Backend returns: first_name, last_name, profile_photo_url, and Decimal fields as strings
 * Frontend expects: display_name, avatar_url, and numeric fields as numbers
 */
function transformTutor(tutor: TutorProfile): TutorProfile {
  // Normalize subjects: backend TutorSubjectResponse uses subject_name,
  // frontend Subject type expects name. Also handle TutorPublicProfile's
  // PublicSubjectItem which already has name.
  const rawSubjects = (tutor.subjects ?? []) as Array<Record<string, unknown>>;
  const normalizedSubjects = rawSubjects.map((s) => ({
    id: Number(s.subject_id ?? s.id),
    name: String(s.name ?? s.subject_name ?? ''),
  }));

  return {
    ...tutor,
    // Create display_name: prefer first+last, then name field, then title
    display_name: tutor.display_name ||
      [tutor.first_name, tutor.last_name].filter(Boolean).join(' ') ||
      tutor.name ||
      tutor.title ||
      'Tutor',
    // Map profile_photo_url to avatar_url
    avatar_url: tutor.avatar_url || tutor.profile_photo_url,
    // Convert numeric string fields to numbers (backend sends Decimal as string)
    average_rating: Number(tutor.average_rating) || 0,
    hourly_rate: Number(tutor.hourly_rate) || 0,
    total_reviews: Number(tutor.total_reviews) || 0,
    total_sessions: Number(tutor.total_sessions) || 0,
    experience_years: Number(tutor.experience_years) || 0,
    // Ensure subjects are in frontend-expected format
    subjects: normalizedSubjects,
    // Default currency if not provided by backend
    currency: tutor.currency || 'USD',
  };
}

export const tutorsApi = {
  // List approved tutors with filtering and pagination
  list: async (filters: TutorFilters = {}) => {
    const backendFilters = mapFiltersToBackend(filters);
    const response = await api.get<PaginatedResponse<TutorProfile>>(`/tutors?${toQueryString(backendFilters)}`);
    // Transform each tutor to ensure frontend-expected fields
    return {
      ...response,
      items: response.items.map(transformTutor),
    };
  },

  // Get a single tutor's public profile by ID
  get: async (id: number) => {
    const tutor = await api.get<TutorProfile>(`/tutors/${id}`);
    return transformTutor(tutor);
  },

  // Get a tutor's public profile (explicit public endpoint)
  getPublic: async (id: number) => {
    const tutor = await api.get<TutorProfile>(`/tutors/${id}/public`);
    return transformTutor(tutor);
  },

  // Get tutor's availability
  getAvailability: (tutorId: number, weekStart?: string) => {
    const params = weekStart ? `?week_start=${weekStart}` : '';
    return api.get<AvailabilitySlot[]>(`/tutors/${tutorId}/availability${params}`);
  },

  // Get all active subjects
  getSubjects: () =>
    api.get<Subject[]>('/subjects'),

  // Get current tutor's own profile (requires tutor role)
  getMyProfile: async () => {
    const tutor = await api.get<TutorProfile>('/tutors/me/profile');
    return transformTutor(tutor);
  },

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
  getFeatured: async (limit = 6) => {
    const response = await api.get<PaginatedResponse<TutorProfile>>(`/tutors?sort_by=rating&page_size=${limit}`);
    return (response.items ?? []).map(transformTutor);
  },
};
