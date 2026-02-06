import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { searchApi } from '@/lib/api/search';
import type { SearchResults, RecentSearch } from '@/types/search';

const RECENT_SEARCHES_KEY = 'edustream_recent_searches';
const MAX_RECENT_SEARCHES = 5;
const DEBOUNCE_DELAY_MS = 300;

export const searchKeys = {
  all: ['search'] as const,
  query: (q: string) => [...searchKeys.all, q] as const,
};

/**
 * Custom hook for debouncing search input
 * Delays updating the debounced value until after the specified delay
 */
function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

export function useSearch(query: string) {
  // Debounce the query to prevent excessive API calls
  const debouncedQuery = useDebouncedValue(query, DEBOUNCE_DELAY_MS);

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: searchKeys.query(debouncedQuery),
    queryFn: () => searchApi.search(debouncedQuery),
    enabled: debouncedQuery.trim().length > 0,
    staleTime: 60000, // Cache results for 1 minute
  });

  // Show loading state when query differs from debounced query (typing)
  // or when actually fetching data
  const isSearching = (query !== debouncedQuery && query.trim().length > 0) ||
                      (isFetching && debouncedQuery.trim().length > 0);

  return {
    results: data as SearchResults | undefined,
    isLoading: isSearching,
    error,
  };
}

function getInitialRecentSearches(): RecentSearch[] {
  if (typeof window === 'undefined') return [];
  try {
    const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

export function useRecentSearches() {
  // Use lazy initialization to avoid useEffect
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>(getInitialRecentSearches);

  const addRecentSearch = useCallback((query: string) => {
    if (!query.trim()) return;

    setRecentSearches((prev) => {
      const filtered = prev.filter((s) => s.query.toLowerCase() !== query.toLowerCase());
      const newSearch: RecentSearch = {
        id: crypto.randomUUID(),
        query: query.trim(),
        timestamp: Date.now(),
      };
      const updated = [newSearch, ...filtered].slice(0, MAX_RECENT_SEARCHES);

      if (typeof window !== 'undefined') {
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
      }

      return updated;
    });
  }, []);

  const clearRecentSearches = useCallback(() => {
    setRecentSearches([]);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(RECENT_SEARCHES_KEY);
    }
  }, []);

  const removeRecentSearch = useCallback((id: string) => {
    setRecentSearches((prev) => {
      const updated = prev.filter((s) => s.id !== id);
      if (typeof window !== 'undefined') {
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated));
      }
      return updated;
    });
  }, []);

  return {
    recentSearches,
    addRecentSearch,
    clearRecentSearches,
    removeRecentSearch,
  };
}
