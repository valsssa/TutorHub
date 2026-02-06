import { api } from './client';
import type { Review, CreateReviewInput } from '@/types/review';

export const reviewsApi = {
  // Get reviews for a tutor (via /reviews/tutors/:id endpoint)
  getForTutor: (tutorId: number, page = 1, pageSize = 20) =>
    api.get<Review[]>(`/reviews/tutors/${tutorId}?page=${page}&page_size=${pageSize}`),

  // Create a review for a completed booking
  create: (data: CreateReviewInput) =>
    api.post<Review>('/reviews', data),

  // Also available via tutor profile endpoint
  getForTutorViaProfile: (tutorId: number) =>
    api.get<Review[]>(`/tutors/${tutorId}/reviews`),
};
