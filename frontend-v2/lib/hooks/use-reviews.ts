import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewsApi } from '@/lib/api/reviews';
import { tutorKeys } from './use-tutors';
import type { CreateReviewInput } from '@/types/review';

export const reviewKeys = {
  all: ['reviews'] as const,
  lists: () => [...reviewKeys.all, 'list'] as const,
  forTutor: (tutorId: number) =>
    [...reviewKeys.lists(), 'tutor', tutorId] as const,
};

export function useTutorReviews(tutorId: number, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: [...reviewKeys.forTutor(tutorId), page, pageSize],
    queryFn: () => reviewsApi.getForTutor(tutorId, page, pageSize),
    enabled: !!tutorId,
  });
}

export function useCreateReview() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateReviewInput) => reviewsApi.create(data),
    onSuccess: (review) => {
      queryClient.invalidateQueries({ queryKey: reviewKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: reviewKeys.forTutor(review.tutor_profile_id),
      });
      queryClient.invalidateQueries({ queryKey: tutorKeys.all });
    },
  });
}
