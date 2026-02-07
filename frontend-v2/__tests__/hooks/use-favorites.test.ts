import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import {
  useFavorites,
  useIsFavorite,
  useAddFavorite,
  useRemoveFavorite,
  useToggleFavorite,
  favoriteKeys,
} from '@/lib/hooks/use-favorites';
import type { Favorite, PaginatedResponse } from '@/types';

// Mock the favoritesApi module
const mockList = vi.fn();
const mockAdd = vi.fn();
const mockRemove = vi.fn();
const mockCheck = vi.fn();

vi.mock('@/lib/api', () => ({
  favoritesApi: {
    list: (params?: { page?: number; page_size?: number }) => mockList(params),
    add: (tutorId: number) => mockAdd(tutorId),
    remove: (tutorId: number) => mockRemove(tutorId),
    check: (tutorId: number) => mockCheck(tutorId),
  },
}));

// Helper to create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: Infinity, // Keep cache for testing
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

// Wrapper component for React Query
function createWrapper() {
  const queryClient = createTestQueryClient();
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children
    );
  };
}

// Sample test data
const mockFavoriteItems: Favorite[] = [
  {
    id: 1,
    student_id: 10,
    tutor_profile_id: 100,
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 2,
    student_id: 10,
    tutor_profile_id: 101,
    created_at: '2024-01-16T12:00:00Z',
  },
];

// Paginated response format matching backend
const mockPaginatedFavorites: PaginatedResponse<Favorite> = {
  items: mockFavoriteItems,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
  has_next: false,
  has_prev: false,
};

const mockEmptyPaginatedFavorites: PaginatedResponse<Favorite> = {
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0,
  has_next: false,
  has_prev: false,
};

const mockNewFavorite: Favorite = {
  id: 3,
  student_id: 10,
  tutor_profile_id: 102,
  created_at: '2024-01-17T14:00:00Z',
};

describe('use-favorites hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('favoriteKeys', () => {
    it('generates correct query keys', () => {
      expect(favoriteKeys.all).toEqual(['favorites']);
      expect(favoriteKeys.list()).toEqual(['favorites', 'list', undefined]);
      expect(favoriteKeys.list({ page: 2, page_size: 10 })).toEqual([
        'favorites', 'list', { page: 2, page_size: 10 },
      ]);
      expect(favoriteKeys.check(42)).toEqual(['favorites', 'check', 42]);
    });
  });

  describe('useFavorites', () => {
    it('returns favorites list on success', async () => {
      mockList.mockResolvedValueOnce(mockPaginatedFavorites);

      const { result } = renderHook(() => useFavorites(), {
        wrapper: createWrapper(),
      });

      // Initially loading
      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // data should be the items array for backward compatibility
      expect(result.current.data).toEqual(mockFavoriteItems);
      expect(mockList).toHaveBeenCalledTimes(1);
    });

    it('returns pagination metadata', async () => {
      mockList.mockResolvedValueOnce(mockPaginatedFavorites);

      const { result } = renderHook(() => useFavorites(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.pagination).toEqual({
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
        has_next: false,
        has_prev: false,
      });
    });

    it('returns empty array when no favorites', async () => {
      mockList.mockResolvedValueOnce(mockEmptyPaginatedFavorites);

      const { result } = renderHook(() => useFavorites(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual([]);
    });

    it('handles loading state', () => {
      mockList.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useFavorites(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    it('handles error state', async () => {
      const errorMessage = 'Failed to fetch favorites';
      mockList.mockRejectedValueOnce(new Error(errorMessage));

      const { result } = renderHook(() => useFavorites(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeInstanceOf(Error);
      expect((result.current.error as Error).message).toBe(errorMessage);
    });
  });

  describe('useIsFavorite', () => {
    it('returns true when tutor is favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: true });

      const { result } = renderHook(() => useIsFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual({ is_favorite: true });
      expect(mockCheck).toHaveBeenCalledWith(100);
    });

    it('returns false when not favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: false });

      const { result } = renderHook(() => useIsFavorite(200), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual({ is_favorite: false });
    });

    it('returns false during loading (data is undefined)', () => {
      mockCheck.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useIsFavorite(100), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
      expect(result.current.data).toBeUndefined();
    });

    it('does not fetch when tutorId is falsy', () => {
      const { result } = renderHook(() => useIsFavorite(0), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.isFetching).toBe(false);
      expect(mockCheck).not.toHaveBeenCalled();
    });
  });

  describe('useAddFavorite', () => {
    it('calls API with correct tutorId', async () => {
      mockAdd.mockResolvedValueOnce(mockNewFavorite);

      const queryClient = createTestQueryClient();
      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useAddFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(102);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockAdd).toHaveBeenCalledWith(102);
    });

    it('invalidates favorites queries on success', async () => {
      mockAdd.mockResolvedValueOnce(mockNewFavorite);

      const queryClient = createTestQueryClient();
      // Pre-populate the cache with existing favorites (paginated format)
      queryClient.setQueryData(favoriteKeys.list(), mockPaginatedFavorites);

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useAddFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(102);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Check that queries were invalidated
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: favoriteKeys.all });
      invalidateSpy.mockRestore();
    });

    it('sets check cache to is_favorite: true on success', async () => {
      mockAdd.mockResolvedValueOnce(mockNewFavorite);

      const queryClient = createTestQueryClient();
      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useAddFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(102);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // Check that the check cache was updated
      const checkCache = queryClient.getQueryData(
        favoriteKeys.check(mockNewFavorite.tutor_profile_id)
      );
      expect(checkCache).toEqual({ is_favorite: true });
    });

    it('handles error gracefully', async () => {
      const errorMessage = 'Failed to add favorite';
      mockAdd.mockRejectedValueOnce(new Error(errorMessage));

      const { result } = renderHook(() => useAddFavorite(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate(102);
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBeInstanceOf(Error);
      expect((result.current.error as Error).message).toBe(errorMessage);
    });

    it('invalidates queries even if cache is empty', async () => {
      mockAdd.mockResolvedValueOnce(mockNewFavorite);

      const queryClient = createTestQueryClient();
      // Do NOT pre-populate the cache

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useAddFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(102);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: favoriteKeys.all });
      invalidateSpy.mockRestore();
    });
  });

  describe('useRemoveFavorite', () => {
    it('calls API with correct tutorId', async () => {
      mockRemove.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useRemoveFavorite(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        result.current.mutate(100);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(mockRemove).toHaveBeenCalledWith(100);
    });

    it('performs optimistic update on list cache', async () => {
      // Create a promise that we control
      let resolveRemove: () => void;
      const removePromise = new Promise<void>((resolve) => {
        resolveRemove = resolve;
      });
      mockRemove.mockReturnValueOnce(removePromise);

      const queryClient = createTestQueryClient();
      const listKey = favoriteKeys.list();
      queryClient.setQueryData(listKey, mockPaginatedFavorites);

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useRemoveFavorite(), { wrapper });

      // Start the mutation
      act(() => {
        result.current.mutate(100);
      });

      // Check optimistic update happened immediately (paginated format)
      await waitFor(() => {
        const cachedFavorites = queryClient.getQueryData<PaginatedResponse<Favorite>>(listKey);
        expect(cachedFavorites?.items).toHaveLength(1);
        expect(cachedFavorites?.items[0].tutor_profile_id).toBe(101);
        expect(cachedFavorites?.total).toBe(1);
      });

      // Resolve the mutation
      await act(async () => {
        resolveRemove!();
      });
    });

    it('performs optimistic update on check cache', async () => {
      let resolveRemove!: () => void;
      const removePromise = new Promise<void>((resolve) => {
        resolveRemove = resolve;
      });
      mockRemove.mockReturnValueOnce(removePromise);

      const queryClient = createTestQueryClient();
      queryClient.setQueryData(favoriteKeys.check(100), { is_favorite: true });

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useRemoveFavorite(), { wrapper });

      act(() => {
        result.current.mutate(100);
      });

      // Check optimistic update
      await waitFor(() => {
        const checkCache = queryClient.getQueryData(favoriteKeys.check(100));
        expect(checkCache).toEqual({ is_favorite: false });
      });

      await act(async () => {
        resolveRemove();
      });
    });

    it('rolls back on error', async () => {
      mockRemove.mockRejectedValueOnce(new Error('Remove failed'));

      const queryClient = createTestQueryClient();
      const listKey = favoriteKeys.list();
      queryClient.setQueryData(listKey, mockPaginatedFavorites);
      queryClient.setQueryData(favoriteKeys.check(100), { is_favorite: true });

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useRemoveFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(100);
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // Check that the cache was rolled back (paginated format)
      const cachedFavorites = queryClient.getQueryData<PaginatedResponse<Favorite>>(listKey);
      expect(cachedFavorites).toEqual(mockPaginatedFavorites);

      const checkCache = queryClient.getQueryData(favoriteKeys.check(100));
      expect(checkCache).toEqual({ is_favorite: true });
    });

    it('handles empty cache on optimistic update', async () => {
      mockRemove.mockResolvedValueOnce(undefined);

      const queryClient = createTestQueryClient();
      // Do NOT pre-populate the cache

      const wrapper = ({ children }: { children: React.ReactNode }) =>
        React.createElement(
          QueryClientProvider,
          { client: queryClient },
          children
        );

      const { result } = renderHook(() => useRemoveFavorite(), { wrapper });

      await act(async () => {
        result.current.mutate(100);
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // With no pre-populated cache, setQueriesData has nothing to update
      // The cache should remain undefined since there was no matching query
      const cachedFavorites = queryClient.getQueryData<PaginatedResponse<Favorite>>(
        favoriteKeys.list()
      );
      expect(cachedFavorites).toBeUndefined();
    });
  });

  describe('useToggleFavorite', () => {
    it('returns correct isFavorite state when favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: true });

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isFavorite).toBe(true);
      });
    });

    it('returns correct isFavorite state when not favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: false });

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isFavorite).toBe(false);
    });

    it('calls add when not favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: false });
      mockAdd.mockResolvedValueOnce(mockNewFavorite);

      const { result } = renderHook(() => useToggleFavorite(102), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isFavorite).toBe(false);

      await act(async () => {
        result.current.toggle();
      });

      expect(mockAdd).toHaveBeenCalledWith(102);
      expect(mockRemove).not.toHaveBeenCalled();
    });

    it('calls remove when favorited', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: true });
      mockRemove.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isFavorite).toBe(true);
      });

      await act(async () => {
        result.current.toggle();
      });

      expect(mockRemove).toHaveBeenCalledWith(100);
      expect(mockAdd).not.toHaveBeenCalled();
    });

    it('returns isLoading true while checking status', () => {
      mockCheck.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);
    });

    it('returns isLoading true while add is pending', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: false });
      mockAdd.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.toggle();
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });
    });

    it('returns isLoading true while remove is pending', async () => {
      mockCheck.mockResolvedValueOnce({ is_favorite: true });
      mockRemove.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isFavorite).toBe(true);
      });

      act(() => {
        result.current.toggle();
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true);
      });
    });

    it('returns false for isFavorite while loading', () => {
      mockCheck.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      const { result } = renderHook(() => useToggleFavorite(100), {
        wrapper: createWrapper(),
      });

      // The status?.is_favorite ?? false means it returns false when undefined
      expect(result.current.isFavorite).toBe(false);
    });
  });
});
