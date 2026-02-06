import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { favoritesApi } from '@/lib/api';
import type { Favorite, PaginatedResponse } from '@/types';

export const favoriteKeys = {
  all: ['favorites'] as const,
  list: () => [...favoriteKeys.all, 'list'] as const,
  check: (tutorId: number) => [...favoriteKeys.all, 'check', tutorId] as const,
};

export function useFavorites() {
  const query = useQuery({
    queryKey: favoriteKeys.list(),
    queryFn: favoritesApi.list,
  });

  // Return the items array for backward compatibility, plus pagination metadata
  return {
    ...query,
    data: query.data?.items,
    pagination: query.data ? {
      total: query.data.total,
      page: query.data.page,
      page_size: query.data.page_size,
      total_pages: query.data.total_pages,
      has_next: query.data.has_next,
      has_prev: query.data.has_prev,
    } : undefined,
  };
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
      queryClient.setQueryData<PaginatedResponse<Favorite>>(favoriteKeys.list(), (old) => {
        if (!old) {
          return {
            items: [newFavorite],
            total: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
            has_next: false,
            has_prev: false,
          };
        }
        return {
          ...old,
          items: [...old.items, newFavorite],
          total: old.total + 1,
        };
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

      const previousFavorites = queryClient.getQueryData<PaginatedResponse<Favorite>>(favoriteKeys.list());

      queryClient.setQueryData<PaginatedResponse<Favorite>>(favoriteKeys.list(), (old) => {
        if (!old) {
          return {
            items: [],
            total: 0,
            page: 1,
            page_size: 20,
            total_pages: 0,
            has_next: false,
            has_prev: false,
          };
        }
        const newItems = old.items.filter((f) => f.tutor_profile_id !== tutorProfileId);
        return {
          ...old,
          items: newItems,
          total: Math.max(0, old.total - 1),
        };
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
