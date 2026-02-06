import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { favoritesApi } from '@/lib/api';
import type { Favorite } from '@/types';

export const favoriteKeys = {
  all: ['favorites'] as const,
  list: () => [...favoriteKeys.all, 'list'] as const,
  check: (tutorId: number) => [...favoriteKeys.all, 'check', tutorId] as const,
};

export function useFavorites() {
  return useQuery({
    queryKey: favoriteKeys.list(),
    queryFn: favoritesApi.list,
  });
}

export function useIsFavorite(tutorId: number) {
  return useQuery({
    queryKey: favoriteKeys.check(tutorId),
    queryFn: () => favoritesApi.check(tutorId),
    enabled: !!tutorId,
  });
}

export function useAddFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: favoritesApi.add,
    onSuccess: (newFavorite) => {
      queryClient.setQueryData<Favorite[]>(favoriteKeys.list(), (old) => {
        if (!old) return [newFavorite];
        return [...old, newFavorite];
      });
      queryClient.setQueryData(
        favoriteKeys.check(newFavorite.tutor_profile_id),
        { is_favorite: true }
      );
    },
  });
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: favoritesApi.remove,
    onMutate: async (tutorProfileId) => {
      await queryClient.cancelQueries({ queryKey: favoriteKeys.list() });
      await queryClient.cancelQueries({ queryKey: favoriteKeys.check(tutorProfileId) });

      const previousFavorites = queryClient.getQueryData<Favorite[]>(favoriteKeys.list());

      queryClient.setQueryData<Favorite[]>(favoriteKeys.list(), (old) => {
        if (!old) return [];
        return old.filter((f) => f.tutor_profile_id !== tutorProfileId);
      });

      queryClient.setQueryData(
        favoriteKeys.check(tutorProfileId),
        { is_favorite: false }
      );

      return { previousFavorites };
    },
    onError: (_err, tutorProfileId, context) => {
      if (context?.previousFavorites) {
        queryClient.setQueryData(favoriteKeys.list(), context.previousFavorites);
        queryClient.setQueryData(
          favoriteKeys.check(tutorProfileId),
          { is_favorite: true }
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all });
    },
  });
}

export function useToggleFavorite(tutorId: number) {
  const { data: status, isLoading: isCheckingStatus } = useIsFavorite(tutorId);
  const addFavorite = useAddFavorite();
  const removeFavorite = useRemoveFavorite();

  const isFavorite = status?.is_favorite ?? false;
  const isLoading = isCheckingStatus || addFavorite.isPending || removeFavorite.isPending;

  const toggle = () => {
    if (isFavorite) {
      removeFavorite.mutate(tutorId);
    } else {
      addFavorite.mutate(tutorId);
    }
  };

  return {
    isFavorite,
    isLoading,
    toggle,
  };
}
