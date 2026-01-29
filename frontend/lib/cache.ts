/**
 * Centralized Cache Management Module
 *
 * Features:
 * - LRU cache with configurable TTL per resource type
 * - Stale-while-revalidate (SWR) pattern support
 * - Automatic invalidation on mutations
 * - Related cache invalidation (e.g., updating a tutor invalidates tutor lists)
 * - Cache event system for reactive updates
 * - Optimistic update support
 * - Cache warming utilities
 */

import { createLogger } from "./logger";

const logger = createLogger("Cache");

// ============================================================================
// Types
// ============================================================================

export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  staleAt: number;
  expiresAt: number;
  accessCount: number;
  lastAccessed: number;
  isRevalidating?: boolean;
}

export interface CacheConfig {
  /** Time until data is considered stale (ms) - triggers background revalidation */
  staleTime: number;
  /** Time until data is completely expired (ms) - returns null */
  cacheTime: number;
  /** Enable stale-while-revalidate pattern */
  swr?: boolean;
}

export type ResourceType =
  | "users"
  | "profile"
  | "tutors"
  | "tutor-profile"
  | "bookings"
  | "reviews"
  | "messages"
  | "notifications"
  | "packages"
  | "favorites"
  | "subjects"
  | "admin"
  | "owner"
  | "availability";

export type CacheEventType = "set" | "invalidate" | "clear" | "revalidate";

export interface CacheEvent {
  type: CacheEventType;
  key?: string;
  pattern?: string;
  resourceType?: ResourceType;
  timestamp: number;
}

type CacheEventListener = (event: CacheEvent) => void;

// ============================================================================
// Default Cache Configurations per Resource Type
// ============================================================================

const RESOURCE_CACHE_CONFIGS: Record<ResourceType, CacheConfig> = {
  users: { staleTime: 30 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  profile: { staleTime: 30 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  tutors: { staleTime: 60 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  "tutor-profile": { staleTime: 60 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  bookings: { staleTime: 30 * 1000, cacheTime: 2 * 60 * 1000, swr: true },
  reviews: { staleTime: 2 * 60 * 1000, cacheTime: 10 * 60 * 1000, swr: true },
  messages: { staleTime: 10 * 1000, cacheTime: 60 * 1000, swr: true },
  notifications: { staleTime: 15 * 1000, cacheTime: 60 * 1000, swr: true },
  packages: { staleTime: 60 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  favorites: { staleTime: 30 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  subjects: { staleTime: 10 * 60 * 1000, cacheTime: 30 * 60 * 1000, swr: true },
  admin: { staleTime: 30 * 1000, cacheTime: 2 * 60 * 1000, swr: true },
  owner: { staleTime: 60 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
  availability: { staleTime: 60 * 1000, cacheTime: 5 * 60 * 1000, swr: true },
};

// Related resource invalidation mapping
// When a resource is mutated, these related resources should also be invalidated
const RELATED_RESOURCES: Partial<Record<ResourceType, ResourceType[]>> = {
  users: ["profile"],
  profile: ["users"],
  tutors: ["tutor-profile", "favorites"],
  "tutor-profile": ["tutors"],
  bookings: ["messages", "notifications"],
  favorites: ["tutors"],
  packages: ["bookings"],
};

// ============================================================================
// Cache Store
// ============================================================================

class CacheStore {
  private cache = new Map<string, CacheEntry<unknown>>();
  private listeners = new Set<CacheEventListener>();
  private maxSize = 200;
  private revalidationPromises = new Map<string, Promise<unknown>>();

  // -------------------------------------------------------------------------
  // Cache Key Generation
  // -------------------------------------------------------------------------

  /**
   * Generate a cache key from URL and optional params
   */
  generateKey(url: string, params?: unknown): string {
    const paramStr = params ? JSON.stringify(params) : "{}";
    return `${url}:${paramStr}`;
  }

  /**
   * Generate a cache key for a specific resource
   */
  generateResourceKey(
    resourceType: ResourceType,
    id?: string | number,
    params?: Record<string, unknown>
  ): string {
    const base = `/api/${resourceType}`;
    const path = id ? `${base}/${id}` : base;
    return this.generateKey(path, params);
  }

  /**
   * Extract resource type from URL
   */
  getResourceTypeFromUrl(url: string): ResourceType | null {
    const patterns: [RegExp, ResourceType][] = [
      [/\/users|\/auth\/me|\/profile/i, "users"],
      [/\/profile\/student|\/profile\/tutor/i, "profile"],
      [/\/tutors\/me/i, "tutor-profile"],
      [/\/tutors/i, "tutors"],
      [/\/bookings/i, "bookings"],
      [/\/reviews/i, "reviews"],
      [/\/messages/i, "messages"],
      [/\/notifications/i, "notifications"],
      [/\/packages/i, "packages"],
      [/\/favorites/i, "favorites"],
      [/\/subjects/i, "subjects"],
      [/\/admin/i, "admin"],
      [/\/owner/i, "owner"],
      [/\/availability/i, "availability"],
    ];

    for (const [pattern, type] of patterns) {
      if (pattern.test(url)) {
        return type;
      }
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Core Cache Operations
  // -------------------------------------------------------------------------

  /**
   * Get value from cache with stale-while-revalidate support
   */
  get<T>(
    key: string,
    config?: Partial<CacheConfig>
  ): { data: T | null; isStale: boolean; isExpired: boolean } {
    const cached = this.cache.get(key) as CacheEntry<T> | undefined;

    if (!cached) {
      return { data: null, isStale: false, isExpired: true };
    }

    const now = Date.now();
    const isExpired = now > cached.expiresAt;
    const isStale = now > cached.staleAt;

    if (isExpired) {
      this.cache.delete(key);
      return { data: null, isStale: true, isExpired: true };
    }

    // Update access stats for LRU
    cached.accessCount++;
    cached.lastAccessed = now;

    return { data: cached.data, isStale, isExpired: false };
  }

  /**
   * Get cached data only (simple interface)
   */
  getData<T>(key: string): T | null {
    const { data } = this.get<T>(key);
    return data;
  }

  /**
   * Set value in cache with automatic config based on resource type
   */
  set<T>(
    key: string,
    data: T,
    resourceType?: ResourceType,
    customConfig?: Partial<CacheConfig>
  ): void {
    // LRU eviction before adding new entry
    this.evictIfNeeded();

    const config: CacheConfig = {
      ...RESOURCE_CACHE_CONFIGS[resourceType || "users"],
      ...customConfig,
    };

    const now = Date.now();
    const entry: CacheEntry<T> = {
      data,
      timestamp: now,
      staleAt: now + config.staleTime,
      expiresAt: now + config.cacheTime,
      accessCount: 1,
      lastAccessed: now,
    };

    this.cache.set(key, entry);
    this.emit({ type: "set", key, resourceType, timestamp: now });

    logger.debug(`Cache set: ${key} (stale in ${config.staleTime}ms, expires in ${config.cacheTime}ms)`);
  }

  /**
   * Mark an entry as currently revalidating (for SWR)
   */
  markRevalidating(key: string): void {
    const cached = this.cache.get(key);
    if (cached) {
      cached.isRevalidating = true;
    }
  }

  /**
   * Check if a key is currently being revalidated
   */
  isRevalidating(key: string): boolean {
    const cached = this.cache.get(key);
    return cached?.isRevalidating || false;
  }

  /**
   * Store a revalidation promise to prevent duplicate requests
   */
  setRevalidationPromise<T>(key: string, promise: Promise<T>): void {
    this.revalidationPromises.set(key, promise as Promise<unknown>);
    promise.finally(() => {
      this.revalidationPromises.delete(key);
      const cached = this.cache.get(key);
      if (cached) {
        cached.isRevalidating = false;
      }
    });
  }

  /**
   * Get existing revalidation promise if any
   */
  getRevalidationPromise<T>(key: string): Promise<T> | null {
    return (this.revalidationPromises.get(key) as Promise<T>) || null;
  }

  // -------------------------------------------------------------------------
  // Cache Invalidation
  // -------------------------------------------------------------------------

  /**
   * Invalidate a specific cache key
   */
  invalidate(key: string): void {
    if (this.cache.has(key)) {
      this.cache.delete(key);
      this.emit({ type: "invalidate", key, timestamp: Date.now() });
      logger.debug(`Cache invalidated: ${key}`);
    }
  }

  /**
   * Invalidate all cache entries matching a pattern
   */
  invalidatePattern(pattern: string): void {
    const keys = Array.from(this.cache.keys());
    let count = 0;

    for (const key of keys) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
        count++;
      }
    }

    if (count > 0) {
      this.emit({ type: "invalidate", pattern, timestamp: Date.now() });
      logger.debug(`Cache invalidated ${count} entries matching: ${pattern}`);
    }
  }

  /**
   * Invalidate all cache entries for a resource type and its related resources
   */
  invalidateResource(resourceType: ResourceType, includeRelated = true): void {
    this.invalidatePattern(resourceType);
    this.emit({ type: "invalidate", resourceType, timestamp: Date.now() });

    if (includeRelated) {
      const related = RELATED_RESOURCES[resourceType];
      if (related) {
        for (const relatedType of related) {
          this.invalidatePattern(relatedType);
        }
      }
    }
  }

  /**
   * Invalidate cache based on mutation URL
   * This is called automatically after POST/PUT/PATCH/DELETE requests
   */
  invalidateOnMutation(url: string, method: string): void {
    const resourceType = this.getResourceTypeFromUrl(url);
    if (resourceType) {
      logger.debug(`Auto-invalidating cache for ${method} ${url} (resource: ${resourceType})`);
      this.invalidateResource(resourceType, true);
    }
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.revalidationPromises.clear();
    this.emit({ type: "clear", timestamp: Date.now() });
    logger.info("Cache cleared");
  }

  // -------------------------------------------------------------------------
  // Optimistic Updates
  // -------------------------------------------------------------------------

  /**
   * Apply an optimistic update and return a rollback function
   */
  optimisticUpdate<T>(
    key: string,
    updater: (current: T | null) => T,
    resourceType?: ResourceType
  ): () => void {
    const { data: currentData } = this.get<T>(key);
    const snapshot = currentData ? structuredClone(currentData) : null;

    const newData = updater(currentData);
    this.set(key, newData, resourceType);

    // Return rollback function
    return () => {
      if (snapshot !== null) {
        this.set(key, snapshot, resourceType);
      } else {
        this.invalidate(key);
      }
      logger.debug(`Optimistic update rolled back: ${key}`);
    };
  }

  // -------------------------------------------------------------------------
  // Cache Warming
  // -------------------------------------------------------------------------

  /**
   * Pre-populate cache with data (useful for SSR or initial data)
   */
  warm<T>(entries: Array<{ key: string; data: T; resourceType?: ResourceType }>): void {
    for (const { key, data, resourceType } of entries) {
      this.set(key, data, resourceType);
    }
    logger.debug(`Cache warmed with ${entries.length} entries`);
  }

  /**
   * Get cache statistics
   */
  getStats(): {
    size: number;
    maxSize: number;
    hitRate: number;
    entries: Array<{ key: string; age: number; accessCount: number }>;
  } {
    const now = Date.now();
    const entries = Array.from(this.cache.entries()).map(([key, entry]) => ({
      key,
      age: now - entry.timestamp,
      accessCount: entry.accessCount,
    }));

    const totalAccess = entries.reduce((sum, e) => sum + e.accessCount, 0);

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hitRate: this.cache.size > 0 ? totalAccess / this.cache.size : 0,
      entries,
    };
  }

  // -------------------------------------------------------------------------
  // Event System
  // -------------------------------------------------------------------------

  /**
   * Subscribe to cache events
   */
  subscribe(listener: CacheEventListener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit(event: CacheEvent): void {
    for (const listener of this.listeners) {
      try {
        listener(event);
      } catch (error) {
        logger.error("Cache event listener error", error);
      }
    }
  }

  // -------------------------------------------------------------------------
  // Internal Methods
  // -------------------------------------------------------------------------

  private evictIfNeeded(): void {
    if (this.cache.size < this.maxSize) {
      return;
    }

    const now = Date.now();
    const entries = Array.from(this.cache.entries());

    // First, remove expired entries
    const expiredKeys = entries
      .filter(([, v]) => now > v.expiresAt)
      .map(([k]) => k);

    for (const key of expiredKeys) {
      this.cache.delete(key);
    }

    // If still at limit, remove LRU entries
    if (this.cache.size >= this.maxSize) {
      const sortedByLRU = entries
        .filter(([k]) => !expiredKeys.includes(k))
        .sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);

      const toRemove = Math.ceil(this.maxSize * 0.3);
      for (let i = 0; i < toRemove && i < sortedByLRU.length; i++) {
        this.cache.delete(sortedByLRU[i][0]);
      }
    }
  }
}

// ============================================================================
// Singleton Export
// ============================================================================

export const cacheStore = new CacheStore();

// ============================================================================
// Helper Functions (for backward compatibility)
// ============================================================================

/**
 * Generate cache key from URL and params
 * @deprecated Use cacheStore.generateKey instead
 */
export function getCacheKey(url: string, params?: unknown): string {
  return cacheStore.generateKey(url, params);
}

/**
 * Get value from cache
 * @deprecated Use cacheStore.get or cacheStore.getData instead
 */
export function getFromCache<T>(key: string, ttl?: number): T | null {
  const { data, isExpired } = cacheStore.get<T>(key);
  if (isExpired) return null;
  return data;
}

/**
 * Set value in cache
 * @deprecated Use cacheStore.set instead
 */
export function setCache(key: string, data: unknown): void {
  const resourceType = cacheStore.getResourceTypeFromUrl(key);
  cacheStore.set(key, data, resourceType || undefined);
}

/**
 * Clear cache by pattern or all
 * @deprecated Use cacheStore.invalidatePattern or cacheStore.clear instead
 */
export function clearCache(pattern?: string): void {
  if (pattern) {
    cacheStore.invalidatePattern(pattern);
  } else {
    cacheStore.clear();
  }
}

// ============================================================================
// Mutation Cache Invalidation Helper
// ============================================================================

/**
 * Call this after any mutation (POST/PUT/PATCH/DELETE) to automatically
 * invalidate the appropriate cache entries
 */
export function invalidateOnMutation(url: string, method: string): void {
  cacheStore.invalidateOnMutation(url, method);
}

// ============================================================================
// SWR Fetch Helper
// ============================================================================

interface SWRFetchOptions<T> {
  /** Resource type for cache configuration */
  resourceType: ResourceType;
  /** Fetcher function to get fresh data */
  fetcher: () => Promise<T>;
  /** Custom logger for debugging */
  logger?: { debug: (msg: string, ...args: unknown[]) => void };
  /** Label for logging (e.g., "Dashboard stats") */
  label?: string;
}

/**
 * SWR-style fetch helper for API functions
 *
 * Implements stale-while-revalidate:
 * 1. Return cached data immediately if available and not expired
 * 2. If data is stale, trigger background revalidation
 * 3. If no valid cache, fetch fresh data
 *
 * @example
 * ```ts
 * async getDashboardStats(): Promise<DashboardStats> {
 *   return swrFetch(getCacheKey("/api/v1/admin/dashboard/stats"), {
 *     resourceType: "admin",
 *     fetcher: async () => (await api.get("/api/v1/admin/dashboard/stats")).data,
 *     label: "Dashboard stats",
 *   });
 * }
 * ```
 */
export async function swrFetch<T>(
  cacheKey: string,
  options: SWRFetchOptions<T>
): Promise<T> {
  const { resourceType, fetcher, logger: customLogger, label } = options;
  const logLabel = label || cacheKey;

  const { data: cached, isStale, isExpired } = cacheStore.get<T>(cacheKey);

  // Return cached data if available and not expired
  if (cached && !isExpired) {
    if (customLogger) {
      customLogger.debug(`${logLabel} loaded from cache (stale: ${isStale})`);
    }

    // Trigger background revalidation if stale
    if (isStale && !cacheStore.isRevalidating(cacheKey)) {
      cacheStore.markRevalidating(cacheKey);
      fetcher()
        .then((data) => {
          cacheStore.set(cacheKey, data, resourceType);
        })
        .catch(() => {
          // Silently fail background revalidation
        });
    }

    return cached;
  }

  // Fetch fresh data
  if (customLogger) {
    customLogger.debug(`Fetching ${logLabel} from API`);
  }

  const data = await fetcher();
  cacheStore.set(cacheKey, data, resourceType);
  return data;
}

// ============================================================================
// Export Types
// ============================================================================

export type { CacheEventListener };
