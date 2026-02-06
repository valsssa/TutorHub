import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tutorsApi } from '@/lib/api';
import type { TutorFilters } from '@/types';

export const tutorKeys = {
  all: ['tutors'] as const,
  lists: () => [...tutorKeys.all, 'list'] as const,
  list: (filters: TutorFilters) => [...tutorKeys.lists(), filters] as const,
  details: () => [...tutorKeys.all, 'detail'] as const,
  detail: (id: number) => [...tutorKeys.details(), id] as const,
  availability: (id: number, weekStart?: string) =>
    [...tutorKeys.all, 'availability', id, weekStart] as const,
  featured: () => [...tutorKeys.all, 'featured'] as const,
  myProfile: () => [...tutorKeys.all, 'my-profile'] as const,
  subjects: () => ['subjects'] as const,
};

export function useTutors(filters: TutorFilters = {}) {
  return useQuery({
    queryKey: tutorKeys.list(filters),
    queryFn: () => tutorsApi.list(filters),
  });
}

export function useTutor(id: number) {
  return useQuery({
    queryKey: tutorKeys.detail(id),
    queryFn: () => tutorsApi.get(id),
    enabled: !!id,
  });
}

export function useTutorAvailability(tutorId: number, weekStart?: string) {
  return useQuery({
    queryKey: tutorKeys.availability(tutorId, weekStart),
    queryFn: () => tutorsApi.getAvailability(tutorId, weekStart),
    enabled: !!tutorId,
  });
}

export function useFeaturedTutors(limit = 6) {
  return useQuery({
    queryKey: tutorKeys.featured(),
    queryFn: () => tutorsApi.getFeatured(limit),
  });
}

export function useSubjects() {
  return useQuery({
    queryKey: tutorKeys.subjects(),
    queryFn: tutorsApi.getSubjects,
    staleTime: 10 * 60 * 1000,
  });
}

export function useMyTutorProfile() {
  return useQuery({
    queryKey: tutorKeys.myProfile(),
    queryFn: tutorsApi.getMyProfile,
  });
}

export function useUpdateTutorAbout() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: tutorsApi.updateAbout,
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(tutorKeys.myProfile(), updatedProfile);
      queryClient.invalidateQueries({ queryKey: tutorKeys.details() });
    },
  });
}

export function useUpdateTutorPricing() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: tutorsApi.updatePricing,
    onSuccess: (updatedProfile) => {
      queryClient.setQueryData(tutorKeys.myProfile(), updatedProfile);
      queryClient.invalidateQueries({ queryKey: tutorKeys.details() });
    },
  });
}

export function useUpdateAvailability() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: tutorsApi.updateAvailability,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tutorKeys.all });
    },
  });
}
