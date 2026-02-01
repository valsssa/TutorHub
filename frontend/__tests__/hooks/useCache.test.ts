/**
 * useCache Hooks Tests
 *
 * Tests for React cache hooks including:
 * - useCachedData with SWR pattern
 * - useMutation with automatic cache invalidation
 * - useInvalidateCache
 * - useOptimisticUpdate
 */

import { renderHook, act, waitFor } from '@testing-library/react';

// Mock the logger before importing
jest.mock('@/lib/logger', () => ({
  createLogger: () => ({
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn(),
  }),
}));

// Mock the cache module - use jest.fn() directly in factory
jest.mock('@/lib/cache', () => ({
  cacheStore: {
    get: jest.fn(),
    getData: jest.fn(),
    set: jest.fn(),
    invalidate: jest.fn(),
    invalidatePattern: jest.fn(),
    invalidateResource: jest.fn(),
    clear: jest.fn(),
    subscribe: jest.fn(() => jest.fn()),
    markRevalidating: jest.fn(),
    isRevalidating: jest.fn(),
    getRevalidationPromise: jest.fn(),
    setRevalidationPromise: jest.fn(),
    optimisticUpdate: jest.fn(),
    getStats: jest.fn(),
  },
  ResourceType: {},
  CacheConfig: {},
  CacheEvent: {},
}));

// Get reference to mocked cacheStore for tests
import { cacheStore } from '@/lib/cache';
const mockCacheStore = cacheStore as jest.Mocked<typeof cacheStore>;

import {
  useCachedData,
  useMutation,
  useInvalidateCache,
  useOptimisticUpdate,
  useCacheSubscription,
  useCacheStats,
  prefetch,
} from '@/hooks/useCache';

describe('useCachedData', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCacheStore.get.mockReturnValue({ data: null, isStale: false, isExpired: true });
    mockCacheStore.getData.mockReturnValue(null);
    mockCacheStore.isRevalidating.mockReturnValue(false);
    mockCacheStore.getRevalidationPromise.mockReturnValue(null);
  });

  it('fetches data when cache is empty', async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1, name: 'Test' });

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher, { resourceType: 'users' })
    );

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetcher).toHaveBeenCalled();
    expect(result.current.data).toEqual({ id: 1, name: 'Test' });
    expect(mockCacheStore.set).toHaveBeenCalled();
  });

  it('returns cached data immediately when available', async () => {
    const cachedData = { id: 1, name: 'Cached' };
    mockCacheStore.get.mockReturnValue({ data: cachedData, isStale: false, isExpired: false });
    mockCacheStore.getData.mockReturnValue(cachedData);

    const fetcher = jest.fn().mockResolvedValue({ id: 2, name: 'Fresh' });

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher, { resourceType: 'users' })
    );

    // Should have cached data immediately
    expect(result.current.data).toEqual(cachedData);
    expect(result.current.loading).toBe(false);
    expect(fetcher).not.toHaveBeenCalled();
  });

  it('triggers background revalidation for stale data', async () => {
    const cachedData = { id: 1, name: 'Stale' };
    mockCacheStore.get.mockReturnValue({ data: cachedData, isStale: true, isExpired: false });
    mockCacheStore.getData.mockReturnValue(cachedData);
    mockCacheStore.isRevalidating.mockReturnValue(false);

    const fetcher = jest.fn().mockResolvedValue({ id: 2, name: 'Fresh' });

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher, { resourceType: 'users' })
    );

    // Should return stale data immediately
    expect(result.current.data).toEqual(cachedData);
    expect(result.current.isStale).toBe(true);

    // Background revalidation should be triggered
    await waitFor(() => {
      expect(fetcher).toHaveBeenCalled();
    });
  });

  it('skips fetch when skip option is true', () => {
    const fetcher = jest.fn();

    renderHook(() =>
      useCachedData('/api/test', fetcher, { skip: true })
    );

    expect(fetcher).not.toHaveBeenCalled();
  });

  it('handles fetch errors', async () => {
    const error = new Error('Fetch failed');
    const fetcher = jest.fn().mockRejectedValue(error);

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher)
    );

    await waitFor(() => {
      expect(result.current.error).toBe(error);
    });

    expect(result.current.loading).toBe(false);
  });

  it('calls onSuccess callback on successful fetch', async () => {
    const data = { id: 1 };
    const fetcher = jest.fn().mockResolvedValue(data);
    const onSuccess = jest.fn();

    renderHook(() =>
      useCachedData('/api/test', fetcher, { onSuccess })
    );

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(data);
    });
  });

  it('calls onError callback on fetch error', async () => {
    const error = new Error('Failed');
    const fetcher = jest.fn().mockRejectedValue(error);
    const onError = jest.fn();

    renderHook(() =>
      useCachedData('/api/test', fetcher, { onError })
    );

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(error);
    });
  });

  it('provides refetch function', async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Clear mock to verify refetch
    fetcher.mockClear();

    await act(async () => {
      await result.current.refetch();
    });

    expect(fetcher).toHaveBeenCalled();
  });

  it('provides setData function for manual updates', async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1, count: 0 });

    const { result } = renderHook(() =>
      useCachedData<{ id: number; count: number }>('/api/test', fetcher)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.setData({ id: 1, count: 5 });
    });

    expect(result.current.data).toEqual({ id: 1, count: 5 });
  });

  it('provides invalidate function', async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(() =>
      useCachedData('/api/test', fetcher)
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.invalidate();
    });

    expect(mockCacheStore.invalidate).toHaveBeenCalledWith('/api/test');
  });
});

describe('useMutation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('executes mutation function', async () => {
    const mutationFn = jest.fn().mockResolvedValue({ success: true });

    const { result } = renderHook(() =>
      useMutation(mutationFn)
    );

    let mutationResult: unknown;
    await act(async () => {
      mutationResult = await result.current.mutate({ id: 1 });
    });

    expect(mutationFn).toHaveBeenCalledWith({ id: 1 });
    expect(mutationResult).toEqual({ success: true });
    expect(result.current.data).toEqual({ success: true });
  });

  it('sets loading state during mutation', async () => {
    const mutationFn = jest.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 50))
    );

    const { result } = renderHook(() =>
      useMutation(mutationFn)
    );

    expect(result.current.loading).toBe(false);

    let mutationPromise: Promise<unknown>;
    act(() => {
      mutationPromise = result.current.mutate({});
    });

    expect(result.current.loading).toBe(true);

    await act(async () => {
      await mutationPromise;
    });

    expect(result.current.loading).toBe(false);
  });

  it('handles mutation errors', async () => {
    const error = new Error('Mutation failed');
    const mutationFn = jest.fn().mockRejectedValue(error);

    const { result } = renderHook(() =>
      useMutation(mutationFn)
    );

    await act(async () => {
      await result.current.mutate({});
    });

    expect(result.current.error).toBe(error);
    expect(result.current.data).toBeNull();
  });

  it('calls onSuccess callback on success', async () => {
    const data = { success: true };
    const mutationFn = jest.fn().mockResolvedValue(data);
    const onSuccess = jest.fn();

    const { result } = renderHook(() =>
      useMutation(mutationFn, { onSuccess })
    );

    await act(async () => {
      await result.current.mutate({ id: 1 });
    });

    expect(onSuccess).toHaveBeenCalledWith(data, { id: 1 });
  });

  it('calls onError callback on error', async () => {
    const error = new Error('Failed');
    const mutationFn = jest.fn().mockRejectedValue(error);
    const onError = jest.fn();

    const { result } = renderHook(() =>
      useMutation(mutationFn, { onError })
    );

    await act(async () => {
      await result.current.mutate({ id: 1 });
    });

    expect(onError).toHaveBeenCalledWith(error, { id: 1 });
  });

  it('calls onSettled callback after mutation', async () => {
    const data = { success: true };
    const mutationFn = jest.fn().mockResolvedValue(data);
    const onSettled = jest.fn();

    const { result } = renderHook(() =>
      useMutation(mutationFn, { onSettled })
    );

    await act(async () => {
      await result.current.mutate({ id: 1 });
    });

    expect(onSettled).toHaveBeenCalledWith(data, null, { id: 1 });
  });

  it('invalidates specified cache keys on success', async () => {
    const mutationFn = jest.fn().mockResolvedValue({ success: true });

    const { result } = renderHook(() =>
      useMutation(mutationFn, { invalidateKeys: ['key1', 'key2'] })
    );

    await act(async () => {
      await result.current.mutate({});
    });

    expect(mockCacheStore.invalidate).toHaveBeenCalledWith('key1');
    expect(mockCacheStore.invalidate).toHaveBeenCalledWith('key2');
  });

  it('invalidates specified resource types on success', async () => {
    const mutationFn = jest.fn().mockResolvedValue({ success: true });

    const { result } = renderHook(() =>
      useMutation(mutationFn, { invalidateResources: ['bookings', 'messages'] })
    );

    await act(async () => {
      await result.current.mutate({});
    });

    expect(mockCacheStore.invalidateResource).toHaveBeenCalledWith('bookings', true);
    expect(mockCacheStore.invalidateResource).toHaveBeenCalledWith('messages', true);
  });

  it('provides reset function', async () => {
    const mutationFn = jest.fn().mockResolvedValue({ success: true });

    const { result } = renderHook(() =>
      useMutation(mutationFn)
    );

    await act(async () => {
      await result.current.mutate({});
    });

    expect(result.current.data).not.toBeNull();

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('mutateAsync throws on error', async () => {
    const error = new Error('Failed');
    const mutationFn = jest.fn().mockRejectedValue(error);

    const { result } = renderHook(() =>
      useMutation(mutationFn)
    );

    await expect(
      act(async () => {
        await result.current.mutateAsync({});
      })
    ).rejects.toThrow('Failed');
  });
});

describe('useInvalidateCache', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('provides invalidate function', () => {
    const { result } = renderHook(() => useInvalidateCache());

    act(() => {
      result.current.invalidate('test-key');
    });

    expect(mockCacheStore.invalidate).toHaveBeenCalledWith('test-key');
  });

  it('provides invalidatePattern function', () => {
    const { result } = renderHook(() => useInvalidateCache());

    act(() => {
      result.current.invalidatePattern('users');
    });

    expect(mockCacheStore.invalidatePattern).toHaveBeenCalledWith('users');
  });

  it('provides invalidateResource function', () => {
    const { result } = renderHook(() => useInvalidateCache());

    act(() => {
      result.current.invalidateResource('bookings', true);
    });

    expect(mockCacheStore.invalidateResource).toHaveBeenCalledWith('bookings', true);
  });

  it('provides clearAll function', () => {
    const { result } = renderHook(() => useInvalidateCache());

    act(() => {
      result.current.clearAll();
    });

    expect(mockCacheStore.clear).toHaveBeenCalled();
  });
});

describe('useOptimisticUpdate', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCacheStore.optimisticUpdate.mockReturnValue(jest.fn());
  });

  it('applies optimistic update', async () => {
    const rollback = jest.fn();
    mockCacheStore.optimisticUpdate.mockReturnValue(rollback);

    const { result } = renderHook(() =>
      useOptimisticUpdate<{ count: number }>('test-key', 'users')
    );

    const mutation = jest.fn().mockResolvedValue(undefined);

    await act(async () => {
      await result.current.update(
        (current) => ({ count: (current?.count ?? 0) + 1 }),
        mutation
      );
    });

    expect(mockCacheStore.optimisticUpdate).toHaveBeenCalled();
    expect(mutation).toHaveBeenCalled();
    expect(rollback).not.toHaveBeenCalled();
  });

  it('rolls back on mutation error', async () => {
    const rollback = jest.fn();
    mockCacheStore.optimisticUpdate.mockReturnValue(rollback);

    const { result } = renderHook(() =>
      useOptimisticUpdate<{ count: number }>('test-key', 'users')
    );

    const mutation = jest.fn().mockRejectedValue(new Error('Failed'));

    await act(async () => {
      const success = await result.current.update(
        (current) => ({ count: (current?.count ?? 0) + 1 }),
        mutation
      );

      expect(success).toBe(false);
    });

    expect(rollback).toHaveBeenCalled();
  });

  it('tracks updating state', async () => {
    const { result } = renderHook(() =>
      useOptimisticUpdate<{ count: number }>('test-key', 'users')
    );

    expect(result.current.isUpdating).toBe(false);

    const mutation = jest.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 50))
    );

    let updatePromise: Promise<boolean>;
    act(() => {
      updatePromise = result.current.update(() => ({ count: 1 }), mutation);
    });

    expect(result.current.isUpdating).toBe(true);

    await act(async () => {
      await updatePromise;
    });

    expect(result.current.isUpdating).toBe(false);
  });
});

describe('useCacheSubscription', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('subscribes to cache events', () => {
    const callback = jest.fn();
    const unsubscribe = jest.fn();
    mockCacheStore.subscribe.mockReturnValue(unsubscribe);

    const { unmount } = renderHook(() => useCacheSubscription(callback));

    expect(mockCacheStore.subscribe).toHaveBeenCalled();

    unmount();

    expect(unsubscribe).toHaveBeenCalled();
  });
});

describe('useCacheStats', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCacheStore.getStats.mockReturnValue({
      size: 5,
      maxSize: 200,
      hitRate: 0.8,
      entries: [],
    });
  });

  it('returns cache statistics', () => {
    const { result } = renderHook(() => useCacheStats());

    expect(result.current.size).toBe(5);
    expect(result.current.maxSize).toBe(200);
    expect(result.current.hitRate).toBe(0.8);
  });
});

describe('prefetch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockCacheStore.get.mockReturnValue({ data: null, isStale: true, isExpired: true });
  });

  it('fetches and caches data', async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1 });

    await prefetch('test-key', fetcher, 'users');

    expect(fetcher).toHaveBeenCalled();
    expect(mockCacheStore.set).toHaveBeenCalledWith('test-key', { id: 1 }, 'users');
  });

  it('skips fetch when data is fresh', async () => {
    mockCacheStore.get.mockReturnValue({ data: { id: 1 }, isStale: false, isExpired: false });
    const fetcher = jest.fn();

    await prefetch('test-key', fetcher, 'users');

    expect(fetcher).not.toHaveBeenCalled();
  });

  it('handles fetch errors gracefully', async () => {
    const fetcher = jest.fn().mockRejectedValue(new Error('Failed'));

    // Should not throw
    await prefetch('test-key', fetcher, 'users');

    expect(mockCacheStore.set).not.toHaveBeenCalled();
  });
});
