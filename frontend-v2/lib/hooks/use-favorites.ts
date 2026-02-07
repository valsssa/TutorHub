import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { favoritesApi } from '@/lib/api';
import type { FavoritesListParams } from '@/lib/api/favorites';
import type { Favorite, PaginatedResponse } from '@/types';

export const favoriteKeys = {
  all: ['favorites'] as const,
  list: (params?: FavoritesListParams) => [...favoriteKeys.all, 'list', params] as const,
  check: (tutorId: number) => [...favoriteKeys.all, 'check', tutorId] as const,
};

export function useFavorites(params?: FavoritesListParams) {
  const query = useQuery({
    queryKey: favoriteKeys.list(params),
    queryFn: () => favoritesApi.list(params),
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
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all });
      queryClient.setQueryData(
        favoriteKeys.check(newFavorite.tutor_profile_id),
        { is_favorite: true }
      );
    },
  });
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient();

  // Partial key to match all list queries regardless of pagination params
  const listKeyPrefix = ['favorites', 'list'] as const;

  return useMutation({
    mutationFn: favoritesApi.remove,
    onMutate: async (tutorProfileId) => {
      await queryClient.cancelQueries({ queryKey: listKeyPrefix });
      await queryClient.cancelQueries({ queryKey: favoriteKeys.check(tutorProfileId) });

      // Snapshot all list query caches for rollback
      const previousListCaches = queryClient.getQueriesData<PaginatedResponse<Favorite>>({
        queryKey: listKeyPrefix,
      });

      // Optimistically update all list caches (regardless of pagination params)
      queryClient.setQueriesData<PaginatedResponse<Favorite>>(
        { queryKey: listKeyPrefix },
        (old) => {
          if (!old) return old;
          const newItems = old.items.filter((f) => f.tutor_profile_id !== tutorProfileId);
          return {
            ...old,
            items: newItems,
            total: Math.max(0, old.total - 1),
          };
        }
      );

      queryClient.setQueryData(
        favoriteKeys.check(tutorProfileId),
        { is_favorite: false }
      );

      return { previousListCaches };
    },
    onError: (_err, tutorProfileId, context) => {
      // Rollback all list caches
      if (context?.previousListCaches) {
        for (const [key, data] of context.previousListCaches) {
          queryClient.setQueryData(key, data);
        }
      }
      queryClient.setQueryData(
        favoriteKeys.check(tutorProfileId),
        { is_favorite: true }
      );
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
