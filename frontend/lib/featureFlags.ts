/**
 * Feature Flags Client
 *
 * Client-side feature flag checking with local caching.
 *
 * Usage:
 *   import { featureFlags } from '@/lib/featureFlags';
 *
 *   // Check if feature is enabled
 *   const isEnabled = await featureFlags.isEnabled('new_booking_flow');
 *
 *   // With React hook
 *   const { isEnabled, isLoading } = useFeatureFlag('new_booking_flow');
 */

import { useState, useEffect, useCallback } from 'react';

// Types

export interface FeatureFlag {
  name: string;
  state: 'disabled' | 'enabled' | 'percentage' | 'allowlist' | 'denylist';
  percentage: number;
  description: string;
}

interface CacheEntry {
  enabled: boolean;
  timestamp: number;
}

// Configuration

const CACHE_TTL_MS = 60 * 1000; // 60 seconds
const API_BASE = '/api/v1';

// Feature Flags Client

class FeatureFlagsClient {
  private cache: Map<string, CacheEntry> = new Map();
  private userId: string | null = null;
  private pendingRequests: Map<string, Promise<boolean>> = new Map();

  /**
   * Set the current user ID for percentage rollouts
   */
  setUserId(userId: string | null): void {
    if (this.userId !== userId) {
      this.userId = userId;
      // Clear cache when user changes
      this.cache.clear();
    }
  }

  /**
   * Check if a feature is enabled
   */
  async isEnabled(name: string): Promise<boolean> {
    // Check cache first
    const cached = this.cache.get(name);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      return cached.enabled;
    }

    // Check if request is already in flight
    const pending = this.pendingRequests.get(name);
    if (pending) {
      return pending;
    }

    // Make request
    const request = this.fetchFeatureStatus(name);
    this.pendingRequests.set(name, request);

    try {
      const enabled = await request;
      this.cache.set(name, { enabled, timestamp: Date.now() });
      return enabled;
    } finally {
      this.pendingRequests.delete(name);
    }
  }

  /**
   * Check multiple features at once
   */
  async areEnabled(names: string[]): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};
    await Promise.all(
      names.map(async (name) => {
        results[name] = await this.isEnabled(name);
      })
    );
    return results;
  }

  /**
   * Clear the cache
   */
  clearCache(): void {
    this.cache.clear();
  }

  /**
   * Invalidate a specific feature
   */
  invalidate(name: string): void {
    this.cache.delete(name);
  }

  /**
   * Fetch feature status from backend
   *
   * Uses the public endpoint /api/v1/features/{name}/check
   * which doesn't require authentication.
   */
  private async fetchFeatureStatus(name: string): Promise<boolean> {
    try {
      // Use the public check endpoint with optional user ID
      const params = new URLSearchParams();
      if (this.userId) {
        params.set('user_id', this.userId);
      }

      const response = await fetch(
        `${API_BASE}/features/${name}/check?${params.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        // Feature doesn't exist or error - treat as disabled
        if (process.env.NODE_ENV !== 'production') {
          console.warn(`Feature flag '${name}' check failed:`, response.status);
        }
        return false;
      }

      const data = await response.json();
      return data.enabled ?? false;
    } catch (error) {
      // On error, default to disabled for safety
      if (process.env.NODE_ENV !== 'production') {
        console.error(`Error checking feature flag '${name}':`, error);
      }
      return false;
    }
  }
}

// Singleton instance
export const featureFlags = new FeatureFlagsClient();

// React Hook

interface UseFeatureFlagResult {
  isEnabled: boolean;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

/**
 * React hook for feature flag checking
 *
 * @param name Feature flag name
 * @param defaultValue Value to use while loading (default: false)
 */
export function useFeatureFlag(
  name: string,
  defaultValue: boolean = false
): UseFeatureFlagResult {
  const [isEnabled, setIsEnabled] = useState<boolean>(defaultValue);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchFlag = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const enabled = await featureFlags.isEnabled(name);
      setIsEnabled(enabled);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
      setIsEnabled(defaultValue);
    } finally {
      setIsLoading(false);
    }
  }, [name, defaultValue]);

  useEffect(() => {
    fetchFlag();
  }, [fetchFlag]);

  const refetch = useCallback(() => {
    featureFlags.invalidate(name);
    fetchFlag();
  }, [name, fetchFlag]);

  return { isEnabled, isLoading, error, refetch };
}

/**
 * React hook for multiple feature flags
 */
export function useFeatureFlags(
  names: string[]
): {
  flags: Record<string, boolean>;
  isLoading: boolean;
  error: Error | null;
} {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchFlags = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const results = await featureFlags.areEnabled(names);
        setFlags(results);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchFlags();
  }, [names.join(',')]); // Re-fetch when names change

  return { flags, isLoading, error };
}

// Feature Flag Guard Component

interface FeatureFlagGuardProps {
  name: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loading?: React.ReactNode;
}

/**
 * Component that conditionally renders based on feature flag
 *
 * @example
 * <FeatureFlagGuard name="new_feature" fallback={<OldFeature />}>
 *   <NewFeature />
 * </FeatureFlagGuard>
 */
export function FeatureFlagGuard({
  name,
  children,
  fallback = null,
  loading = null,
}: FeatureFlagGuardProps): React.ReactNode {
  const { isEnabled, isLoading } = useFeatureFlag(name);

  if (isLoading) {
    return loading;
  }

  return isEnabled ? children : fallback;
}

// Predefined feature flag names for type safety

export const FEATURE_FLAGS = {
  NEW_BOOKING_FLOW: 'new_booking_flow',
  AI_TUTOR_MATCHING: 'ai_tutor_matching',
  INSTANT_BOOKING: 'instant_booking',
  VIDEO_SESSIONS: 'video_sessions',
  GROUP_SESSIONS: 'group_sessions',
} as const;

export type FeatureFlagName = (typeof FEATURE_FLAGS)[keyof typeof FEATURE_FLAGS];
