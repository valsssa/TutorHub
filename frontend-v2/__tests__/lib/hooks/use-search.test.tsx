import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

// Mock the search API
const mockSearch = vi.fn();
vi.mock('@/lib/api/search', () => ({
  searchApi: {
    search: (query: string) => mockSearch(query),
  },
}));

// Import after mocking
import { useSearch, useRecentSearches } from '@/lib/hooks/use-search';

// Create a wrapper with QueryClient for testing hooks
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };
}

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockSearch.mockResolvedValue({
      tutors: [],
      subjects: [],
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('debouncing', () => {
    it('does not call API immediately on query change', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Type first character
      rerender({ query: 'a' });

      // API should not be called yet (debounce delay not elapsed)
      expect(mockSearch).not.toHaveBeenCalled();
    });

    it('calls API after debounce delay', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Type query
      rerender({ query: 'test' });

      // Should not call immediately
      expect(mockSearch).not.toHaveBeenCalled();

      // Advance timers past debounce delay
      await act(async () => {
        vi.advanceTimersByTime(350);
      });

      // Now API should be called
      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledWith('test');
      });
    });

    it('only makes one API call for rapid typing', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Rapid typing simulation
      rerender({ query: 'm' });
      await act(async () => {
        vi.advanceTimersByTime(50);
      });

      rerender({ query: 'ma' });
      await act(async () => {
        vi.advanceTimersByTime(50);
      });

      rerender({ query: 'mat' });
      await act(async () => {
        vi.advanceTimersByTime(50);
      });

      rerender({ query: 'math' });

      // Should not have called API yet
      expect(mockSearch).not.toHaveBeenCalled();

      // Advance past debounce delay from last keystroke
      await act(async () => {
        vi.advanceTimersByTime(350);
      });

      // Should only call API once with final query
      await waitFor(() => {
        expect(mockSearch).toHaveBeenCalledTimes(1);
        expect(mockSearch).toHaveBeenCalledWith('math');
      });
    });

    it('shows loading state while waiting for debounce', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Type query
      rerender({ query: 'test' });

      // Should show loading while debouncing (query differs from debouncedQuery)
      expect(result.current.isLoading).toBe(true);
    });

    it('does not call API for empty query', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Empty query
      rerender({ query: '   ' });

      // Advance past debounce delay
      await act(async () => {
        vi.advanceTimersByTime(350);
      });

      // Should not call API for whitespace-only query
      expect(mockSearch).not.toHaveBeenCalled();
    });

    it('cancels pending debounce when query is cleared', async () => {
      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      // Type query
      rerender({ query: 'test' });

      // Advance partway through debounce
      await act(async () => {
        vi.advanceTimersByTime(150);
      });

      // Clear query
      rerender({ query: '' });

      // Advance past original debounce time
      await act(async () => {
        vi.advanceTimersByTime(200);
      });

      // Should not have called API
      expect(mockSearch).not.toHaveBeenCalled();
    });
  });

  describe('results', () => {
    it('returns results after successful search', async () => {
      const mockResults = {
        tutors: [{ id: 1, first_name: 'John', last_name: 'Doe' }],
        subjects: [{ id: 1, name: 'Math' }],
      };
      mockSearch.mockResolvedValueOnce(mockResults);

      const { result, rerender } = renderHook(
        ({ query }) => useSearch(query),
        {
          wrapper: createWrapper(),
          initialProps: { query: '' },
        }
      );

      rerender({ query: 'test' });

      // Advance past debounce delay
      await act(async () => {
        vi.advanceTimersByTime(350);
      });

      await waitFor(() => {
        expect(result.current.results).toEqual(mockResults);
      });
    });
  });
});

describe('useRecentSearches', () => {
  const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
      getItem: vi.fn((key: string) => store[key] || null),
      setItem: vi.fn((key: string, value: string) => {
        store[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        store = {};
      }),
    };
  })();

  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
  });

  it('returns empty array initially', () => {
    const { result } = renderHook(() => useRecentSearches());
    expect(result.current.recentSearches).toEqual([]);
  });

  it('adds recent search', () => {
    const { result } = renderHook(() => useRecentSearches());

    act(() => {
      result.current.addRecentSearch('math tutor');
    });

    expect(result.current.recentSearches).toHaveLength(1);
    expect(result.current.recentSearches[0].query).toBe('math tutor');
  });

  it('removes duplicate searches (case insensitive)', () => {
    const { result } = renderHook(() => useRecentSearches());

    act(() => {
      result.current.addRecentSearch('Math Tutor');
    });

    act(() => {
      result.current.addRecentSearch('math tutor');
    });

    expect(result.current.recentSearches).toHaveLength(1);
    expect(result.current.recentSearches[0].query).toBe('math tutor');
  });

  it('limits to MAX_RECENT_SEARCHES', () => {
    const { result } = renderHook(() => useRecentSearches());

    for (let i = 0; i < 10; i++) {
      act(() => {
        result.current.addRecentSearch(`search ${i}`);
      });
    }

    expect(result.current.recentSearches).toHaveLength(5);
  });

  it('clears all recent searches', () => {
    const { result } = renderHook(() => useRecentSearches());

    act(() => {
      result.current.addRecentSearch('search 1');
      result.current.addRecentSearch('search 2');
    });

    act(() => {
      result.current.clearRecentSearches();
    });

    expect(result.current.recentSearches).toEqual([]);
  });

  it('removes specific search by id', () => {
    const { result } = renderHook(() => useRecentSearches());

    act(() => {
      result.current.addRecentSearch('search 1');
      result.current.addRecentSearch('search 2');
    });

    const idToRemove = result.current.recentSearches[0].id;

    act(() => {
      result.current.removeRecentSearch(idToRemove);
    });

    expect(result.current.recentSearches).toHaveLength(1);
    expect(result.current.recentSearches[0].query).toBe('search 1');
  });

  it('ignores empty search queries', () => {
    const { result } = renderHook(() => useRecentSearches());

    act(() => {
      result.current.addRecentSearch('');
      result.current.addRecentSearch('   ');
    });

    expect(result.current.recentSearches).toEqual([]);
  });
});
