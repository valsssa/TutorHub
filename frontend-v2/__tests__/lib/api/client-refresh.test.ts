import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFetch = vi.fn();
const originalFetch = global.fetch;

describe('Token refresh race condition handling', () => {
  beforeEach(() => {
    vi.resetModules();
    global.fetch = mockFetch;
    mockFetch.mockReset();
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('queues concurrent 401 requests on single refresh promise', async () => {
    const { api } = await import('@/lib/api/client');

    // Both initial requests return 401
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Single refresh call
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      // Both retries succeed
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'a' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'b' }),
      });

    const [r1, r2] = await Promise.all([
      api.get('/endpoint-a'),
      api.get('/endpoint-b'),
    ]);

    expect(r1).toEqual({ data: 'a' });
    expect(r2).toEqual({ data: 'b' });

    // Only one refresh call should have been made
    const refreshCalls = mockFetch.mock.calls.filter((call) =>
      call[0].includes('/auth/refresh')
    );
    expect(refreshCalls.length).toBe(1);
  });

  it('clears refresh promise after completion so future refreshes work', async () => {
    const { api } = await import('@/lib/api/client');

    // First 401 -> refresh -> retry success
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'expired' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ round: 1 }),
      });

    const r1 = await api.get('/first');
    expect(r1).toEqual({ round: 1 });

    // Second 401 -> should trigger a NEW refresh (not reuse old promise)
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'expired again' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ round: 2 }),
      });

    const r2 = await api.get('/second');
    expect(r2).toEqual({ round: 2 });

    // Should have 2 refresh calls total
    const refreshCalls = mockFetch.mock.calls.filter((call) =>
      call[0].includes('/auth/refresh')
    );
    expect(refreshCalls.length).toBe(2);
  });

  it('does not retry if already a retry (_isRetry flag)', async () => {
    const { api } = await import('@/lib/api/client');

    // First request -> 401
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'expired' }),
      })
      // Refresh succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      // Retry also returns 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'still unauthorized' }),
      });

    await expect(api.get('/protected')).rejects.toMatchObject({
      status: 401,
      detail: 'still unauthorized',
    });

    // Should NOT trigger another refresh - only 3 total calls
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('refresh uses POST with credentials include', async () => {
    const { api } = await import('@/lib/api/client');

    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'expired' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ok: true }),
      });

    await api.get('/resource');

    const refreshCall = mockFetch.mock.calls.find((call) =>
      call[0].includes('/auth/refresh')
    );
    expect(refreshCall).toBeDefined();
    expect(refreshCall![1]).toMatchObject({
      method: 'POST',
      credentials: 'include',
    });
  });
});
