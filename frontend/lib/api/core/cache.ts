/**
 * In-memory cache with LRU eviction
 */
import { createLogger } from "../../logger";

const logger = createLogger('APICache');

// Cache Entry Interface
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  accessCount: number;
  lastAccessed: number;
}

const cache = new Map<string, CacheEntry<unknown>>();
const DEFAULT_CACHE_TTL = 2 * 60 * 1000; // 2 minutes (reduced for fresher data)
const MAX_CACHE_SIZE = 100; // Reduced to prevent memory bloat

/**
 * Generate cache key from URL and params
 */
export function getCacheKey(url: string, params?: unknown): string {
  return `${url}:${JSON.stringify(params || {})}`;
}

/**
 * Get value from cache
 */
export function getFromCache<T>(key: string, ttl: number = DEFAULT_CACHE_TTL): T | null {
  const cached = cache.get(key);
  if (!cached) return null;

  const age = Date.now() - cached.timestamp;
  if (age > ttl) {
    cache.delete(key);
    return null;
  }

  // Update access stats for LRU
  cached.accessCount++;
  cached.lastAccessed = Date.now();
  return cached.data as T;
}

/**
 * Set value in cache with LRU eviction
 */
export function setCache(key: string, data: unknown): void {
  // LRU eviction before adding new entry
  if (cache.size >= MAX_CACHE_SIZE) {
    const now = Date.now();
    const entries = Array.from(cache.entries());

    // Remove stale entries first (older than 10 minutes)
    const staleEntries = entries.filter(([, v]) => now - v.timestamp > 10 * 60 * 1000);
    staleEntries.forEach(([k]) => cache.delete(k));

    // If still at limit, remove least recently used
    if (cache.size >= MAX_CACHE_SIZE) {
      const sortedByLRU = entries.sort((a, b) => a[1].lastAccessed - b[1].lastAccessed);
      // Remove oldest 30%
      const toRemove = Math.ceil(MAX_CACHE_SIZE * 0.3);
      sortedByLRU.slice(0, toRemove).forEach(([k]) => cache.delete(k));
    }
  }

  cache.set(key, {
    data,
    timestamp: Date.now(),
    accessCount: 1,
    lastAccessed: Date.now(),
  });
}

/**
 * Clear cache by pattern or all
 */
export function clearCache(pattern?: string): void {
  if (pattern) {
    // Clear specific pattern
    const keys = Array.from(cache.keys());
    keys.forEach(key => {
      if (key.includes(pattern)) {
        cache.delete(key);
      }
    });
    logger.info(`Cache cleared for pattern: ${pattern}`);
  } else {
    cache.clear();
    logger.info("Cache cleared");
  }
}
