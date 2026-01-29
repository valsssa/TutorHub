/**
 * React Cache Hooks
 *
 * Provides React hooks for cache management with:
 * - useCachedData: SWR-like data fetching with caching
 * - useMutation: Mutations with automatic cache invalidation
 * - useInvalidateCache: Manual cache invalidation
 * - useOptimisticUpdate: Optimistic updates with rollback
 */

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import {
  cacheStore,
  ResourceType,
  CacheConfig,
  CacheEvent,
} from "@/lib/cache";
import { createLogger } from "@/lib/logger";

const logger = createLogger("CacheHooks");

// ============================================================================
// Types
// ============================================================================

export interface UseCachedDataOptions<T> {
  /** Resource type for cache configuration */
  resourceType?: ResourceType;
  /** Custom cache key (auto-generated if not provided) */
  cacheKey?: string;
  /** Skip initial fetch */
  skip?: boolean;
  /** Custom stale time override */
  staleTime?: number;
  /** Custom cache time override */
  cacheTime?: number;
  /** Called when data is successfully fetched */
  onSuccess?: (data: T) => void;
  /** Called when fetch fails */
  onError?: (error: Error) => void;
  /** Dependencies that trigger refetch when changed */
  deps?: unknown[];
  /** Refetch interval in milliseconds (0 = disabled) */
  refetchInterval?: number;
  /** Refetch when window regains focus */
  refetchOnFocus?: boolean;
  /** Refetch when network reconnects */
  refetchOnReconnect?: boolean;
}

export interface UseCachedDataReturn<T> {
  /** The cached/fetched data */
  data: T | null;
  /** Whether the initial fetch is in progress */
  loading: boolean;
  /** Whether data is being revalidated in background */
  isRevalidating: boolean;
  /** Whether the data is stale */
  isStale: boolean;
  /** Any error that occurred */
  error: Error | null;
  /** Manually trigger a refetch */
  refetch: () => Promise<void>;
  /** Manually set the data (for optimistic updates) */
  setData: (data: T | ((prev: T | null) => T)) => void;
  /** Invalidate this cache entry */
  invalidate: () => void;
}

export interface UseMutationOptions<TData, TVariables> {
  /** Called on successful mutation */
  onSuccess?: (data: TData, variables: TVariables) => void;
  /** Called on mutation error */
  onError?: (error: Error, variables: TVariables) => void;
  /** Called after mutation completes (success or error) */
  onSettled?: (data: TData | null, error: Error | null, variables: TVariables) => void;
  /** Cache keys to invalidate on success */
  invalidateKeys?: string[];
  /** Resource types to invalidate on success */
  invalidateResources?: ResourceType[];
  /** Enable optimistic updates */
  optimistic?: boolean;
}

export interface UseMutationReturn<TData, TVariables> {
  /** Execute the mutation */
  mutate: (variables: TVariables) => Promise<TData | null>;
  /** Execute mutation with async/await */
  mutateAsync: (variables: TVariables) => Promise<TData>;
  /** Whether mutation is in progress */
  loading: boolean;
  /** Mutation error */
  error: Error | null;
  /** Last mutation result */
  data: TData | null;
  /** Reset mutation state */
  reset: () => void;
}

// ============================================================================
// useCachedData Hook
// ============================================================================

/**
 * Fetch and cache data with SWR-like behavior
 *
 * @example
 * ```tsx
 * const { data, loading, refetch } = useCachedData(
 *   "/api/v1/tutors",
 *   () => tutors.list(),
 *   { resourceType: "tutors" }
 * );
 * ```
 */
export function useCachedData<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: UseCachedDataOptions<T> = {}
): UseCachedDataReturn<T> {
  const {
    resourceType,
    cacheKey,
    skip = false,
    staleTime,
    cacheTime,
    onSuccess,
    onError,
    deps = [],
    refetchInterval = 0,
    refetchOnFocus = false,
    refetchOnReconnect = false,
  } = options;

  const actualKey = cacheKey || key;

  // State
  const [data, setDataState] = useState<T | null>(() => {
    const cached = cacheStore.getData<T>(actualKey);
    return cached;
  });
  const [loading, setLoading] = useState(!skip && !data);
  const [isRevalidating, setIsRevalidating] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs for latest values
  const fetcherRef = useRef(fetcher);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  // Update refs on each render
  useEffect(() => {
    fetcherRef.current = fetcher;
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
  });

  // Core fetch function
  const fetchData = useCallback(
    async (isBackground = false) => {
      if (skip) return;

      // Check for existing revalidation
      const existingPromise = cacheStore.getRevalidationPromise<T>(actualKey);
      if (existingPromise) {
        try {
          const result = await existingPromise;
          setDataState(result);
          setError(null);
        } catch (err) {
          setError(err as Error);
        }
        return;
      }

      if (isBackground) {
        setIsRevalidating(true);
        cacheStore.markRevalidating(actualKey);
      } else {
        setLoading(true);
      }

      try {
        const promise = fetcherRef.current();
        cacheStore.setRevalidationPromise(actualKey, promise);

        const result = await promise;

        setDataState(result);
        setError(null);
        setIsStale(false);

        // Update cache
        const config: Partial<CacheConfig> = {};
        if (staleTime !== undefined) config.staleTime = staleTime;
        if (cacheTime !== undefined) config.cacheTime = cacheTime;

        cacheStore.set(actualKey, result, resourceType, config);

        onSuccessRef.current?.(result);
      } catch (err) {
        const error = err as Error;
        setError(error);
        onErrorRef.current?.(error);
        logger.error(`Fetch error for ${actualKey}`, error);
      } finally {
        setLoading(false);
        setIsRevalidating(false);
      }
    },
    [actualKey, skip, staleTime, cacheTime, resourceType]
  );

  // Initial fetch with SWR pattern
  useEffect(() => {
    if (skip) return;

    const { data: cachedData, isStale: stale, isExpired } = cacheStore.get<T>(actualKey);

    if (cachedData && !isExpired) {
      setDataState(cachedData);
      setIsStale(stale);
      setLoading(false);

      // Background revalidate if stale
      if (stale && !cacheStore.isRevalidating(actualKey)) {
        fetchData(true);
      }
    } else {
      // No valid cache, fetch fresh data
      fetchData(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actualKey, skip, ...deps]);

  // Refetch interval
  useEffect(() => {
    if (refetchInterval <= 0 || skip) return;

    const interval = setInterval(() => {
      fetchData(true);
    }, refetchInterval);

    return () => clearInterval(interval);
  }, [refetchInterval, skip, fetchData]);

  // Refetch on focus
  useEffect(() => {
    if (!refetchOnFocus || skip) return;

    const handleFocus = () => {
      const { isStale } = cacheStore.get<T>(actualKey);
      if (isStale) {
        fetchData(true);
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [refetchOnFocus, skip, actualKey, fetchData]);

  // Refetch on reconnect
  useEffect(() => {
    if (!refetchOnReconnect || skip) return;

    const handleOnline = () => {
      fetchData(true);
    };

    window.addEventListener("online", handleOnline);
    return () => window.removeEventListener("online", handleOnline);
  }, [refetchOnReconnect, skip, fetchData]);

  // Subscribe to cache invalidation events
  useEffect(() => {
    const unsubscribe = cacheStore.subscribe((event: CacheEvent) => {
      if (event.type === "invalidate") {
        const shouldRefetch =
          event.key === actualKey ||
          (event.pattern && actualKey.includes(event.pattern)) ||
          (event.resourceType && resourceType === event.resourceType);

        if (shouldRefetch && !skip) {
          fetchData(false);
        }
      }
    });

    return unsubscribe;
  }, [actualKey, resourceType, skip, fetchData]);

  // Manual setData
  const setData = useCallback(
    (updater: T | ((prev: T | null) => T)) => {
      const newData = typeof updater === "function"
        ? (updater as (prev: T | null) => T)(data)
        : updater;

      setDataState(newData);
      cacheStore.set(actualKey, newData, resourceType);
    },
    [actualKey, data, resourceType]
  );

  // Manual invalidate
  const invalidate = useCallback(() => {
    cacheStore.invalidate(actualKey);
  }, [actualKey]);

  // Manual refetch
  const refetch = useCallback(async () => {
    await fetchData(false);
  }, [fetchData]);

  return {
    data,
    loading,
    isRevalidating,
    isStale,
    error,
    refetch,
    setData,
    invalidate,
  };
}

// ============================================================================
// useMutation Hook
// ============================================================================

/**
 * Execute mutations with automatic cache invalidation
 *
 * @example
 * ```tsx
 * const { mutate, loading } = useMutation(
 *   (data) => bookings.create(data),
 *   { invalidateResources: ["bookings"] }
 * );
 *
 * await mutate({ tutor_id: 1, start_at: "..." });
 * ```
 */
export function useMutation<TData, TVariables = void>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: UseMutationOptions<TData, TVariables> = {}
): UseMutationReturn<TData, TVariables> {
  const {
    onSuccess,
    onError,
    onSettled,
    invalidateKeys = [],
    invalidateResources = [],
  } = options;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<TData | null>(null);

  // Refs for latest callbacks
  const mutationFnRef = useRef(mutationFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  const onSettledRef = useRef(onSettled);

  useEffect(() => {
    mutationFnRef.current = mutationFn;
    onSuccessRef.current = onSuccess;
    onErrorRef.current = onError;
    onSettledRef.current = onSettled;
  });

  const mutateAsync = useCallback(
    async (variables: TVariables): Promise<TData> => {
      setLoading(true);
      setError(null);

      try {
        const result = await mutationFnRef.current(variables);
        setData(result);

        // Invalidate specified cache keys
        for (const key of invalidateKeys) {
          cacheStore.invalidate(key);
        }

        // Invalidate specified resource types
        for (const resource of invalidateResources) {
          cacheStore.invalidateResource(resource, true);
        }

        onSuccessRef.current?.(result, variables);
        onSettledRef.current?.(result, null, variables);

        return result;
      } catch (err) {
        const error = err as Error;
        setError(error);
        onErrorRef.current?.(error, variables);
        onSettledRef.current?.(null, error, variables);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [invalidateKeys, invalidateResources]
  );

  const mutate = useCallback(
    async (variables: TVariables): Promise<TData | null> => {
      try {
        return await mutateAsync(variables);
      } catch {
        return null;
      }
    },
    [mutateAsync]
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setData(null);
  }, []);

  return {
    mutate,
    mutateAsync,
    loading,
    error,
    data,
    reset,
  };
}

// ============================================================================
// useInvalidateCache Hook
// ============================================================================

/**
 * Get functions to manually invalidate cache
 *
 * @example
 * ```tsx
 * const { invalidate, invalidatePattern, invalidateResource } = useInvalidateCache();
 *
 * // After manual data change
 * invalidateResource("bookings");
 * ```
 */
export function useInvalidateCache() {
  const invalidate = useCallback((key: string) => {
    cacheStore.invalidate(key);
  }, []);

  const invalidatePattern = useCallback((pattern: string) => {
    cacheStore.invalidatePattern(pattern);
  }, []);

  const invalidateResource = useCallback(
    (resourceType: ResourceType, includeRelated = true) => {
      cacheStore.invalidateResource(resourceType, includeRelated);
    },
    []
  );

  const clearAll = useCallback(() => {
    cacheStore.clear();
  }, []);

  return {
    invalidate,
    invalidatePattern,
    invalidateResource,
    clearAll,
  };
}

// ============================================================================
// useOptimisticUpdate Hook
// ============================================================================

/**
 * Perform optimistic updates with automatic rollback on error
 *
 * @example
 * ```tsx
 * const { update, isUpdating } = useOptimisticUpdate<Booking[]>(
 *   cacheKey,
 *   "bookings"
 * );
 *
 * await update(
 *   (bookings) => bookings.filter(b => b.id !== deletedId),
 *   () => bookings.delete(deletedId)
 * );
 * ```
 */
export function useOptimisticUpdate<T>(
  cacheKey: string,
  resourceType?: ResourceType
) {
  const [isUpdating, setIsUpdating] = useState(false);

  const update = useCallback(
    async (
      optimisticUpdater: (current: T | null) => T,
      mutation: () => Promise<unknown>
    ): Promise<boolean> => {
      setIsUpdating(true);

      // Apply optimistic update
      const rollback = cacheStore.optimisticUpdate<T>(
        cacheKey,
        optimisticUpdater,
        resourceType
      );

      try {
        await mutation();
        return true;
      } catch (error) {
        // Rollback on error
        rollback();
        logger.error("Optimistic update failed, rolling back", error);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    [cacheKey, resourceType]
  );

  return { update, isUpdating };
}

// ============================================================================
// useCacheSubscription Hook
// ============================================================================

/**
 * Subscribe to cache events
 *
 * @example
 * ```tsx
 * useCacheSubscription((event) => {
 *   if (event.type === "invalidate" && event.resourceType === "bookings") {
 *     refetchBookings();
 *   }
 * });
 * ```
 */
export function useCacheSubscription(callback: (event: CacheEvent) => void) {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  });

  useEffect(() => {
    return cacheStore.subscribe((event) => {
      callbackRef.current(event);
    });
  }, []);
}

// ============================================================================
// useCacheStats Hook (for debugging)
// ============================================================================

/**
 * Get cache statistics for debugging
 */
export function useCacheStats() {
  const [stats, setStats] = useState(() => cacheStore.getStats());

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(cacheStore.getStats());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return stats;
}

// ============================================================================
// Prefetch Utility
// ============================================================================

/**
 * Prefetch data into cache
 *
 * @example
 * ```tsx
 * // Prefetch on hover
 * onMouseEnter={() => prefetch("/api/tutors/123", () => tutors.get(123), "tutors")}
 * ```
 */
export async function prefetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  resourceType?: ResourceType
): Promise<void> {
  // Don't prefetch if already cached and fresh
  const { isExpired, isStale } = cacheStore.get<T>(key);
  if (!isExpired && !isStale) return;

  try {
    const data = await fetcher();
    cacheStore.set(key, data, resourceType);
    logger.debug(`Prefetched: ${key}`);
  } catch (error) {
    logger.error(`Prefetch failed: ${key}`, error);
  }
}
