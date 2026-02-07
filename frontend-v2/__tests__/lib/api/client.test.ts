import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError } from '@/lib/api/client';

// Mock fetch globally
const mockFetch = vi.fn();
const originalFetch = global.fetch;

describe('ApiError', () => {
  it('creates an error with status, detail, and code', () => {
    const error = new ApiError(400, 'Bad request', 'INVALID_INPUT');

    expect(error.status).toBe(400);
    expect(error.detail).toBe('Bad request');
    expect(error.code).toBe('INVALID_INPUT');
    expect(error.message).toBe('Bad request');
    expect(error.name).toBe('ApiError');
  });

  it('creates an error without code', () => {
    const error = new ApiError(500, 'Server error');

    expect(error.status).toBe(500);
    expect(error.detail).toBe('Server error');
    expect(error.code).toBeUndefined();
  });

  describe('status helpers', () => {
    it('isUnauthorized returns true for 401', () => {
      const error = new ApiError(401, 'Unauthorized');
      expect(error.isUnauthorized).toBe(true);
      expect(error.isForbidden).toBe(false);
    });

    it('isForbidden returns true for 403', () => {
      const error = new ApiError(403, 'Forbidden');
      expect(error.isForbidden).toBe(true);
      expect(error.isUnauthorized).toBe(false);
    });

    it('isNotFound returns true for 404', () => {
      const error = new ApiError(404, 'Not found');
      expect(error.isNotFound).toBe(true);
    });

    it('isValidation returns true for 422', () => {
      const error = new ApiError(422, 'Validation error');
      expect(error.isValidation).toBe(true);
    });

    it('isServerError returns true for 500+', () => {
      expect(new ApiError(500, 'Internal').isServerError).toBe(true);
      expect(new ApiError(502, 'Bad gateway').isServerError).toBe(true);
      expect(new ApiError(503, 'Unavailable').isServerError).toBe(true);
    });

    it('isServerError returns false for client errors', () => {
      expect(new ApiError(400, 'Bad request').isServerError).toBe(false);
      expect(new ApiError(404, 'Not found').isServerError).toBe(false);
      expect(new ApiError(499, 'Client closed').isServerError).toBe(false);
    });
  });
});

describe('ApiClient', () => {
  beforeEach(() => {
    vi.resetModules();
    global.fetch = mockFetch;
    mockFetch.mockReset();
    // Reset document.cookie
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('credentials mode', () => {
    it('includes credentials in all requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      });
      const { api } = await import('@/lib/api/client');
      await api.get('/test');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('includes credentials in POST requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.post('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('includes credentials in PUT requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.put('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('includes credentials in PATCH requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.patch('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });

    it('includes credentials in DELETE requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });
      const { api } = await import('@/lib/api/client');
      await api.delete('/test');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          credentials: 'include',
        })
      );
    });
  });

  describe('CSRF token handling', () => {
    it('reads CSRF token from cookie and adds to header for POST', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=test_csrf_value',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.post('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRF-Token': 'test_csrf_value',
          }),
        })
      );
    });

    it('reads CSRF token from cookie and adds to header for PUT', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=put_csrf_token',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.put('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRF-Token': 'put_csrf_token',
          }),
        })
      );
    });

    it('reads CSRF token from cookie and adds to header for PATCH', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=patch_csrf_token',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.patch('/test', { data: 'value' });
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRF-Token': 'patch_csrf_token',
          }),
        })
      );
    });

    it('reads CSRF token from cookie and adds to header for DELETE', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=delete_csrf_token',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });
      const { api } = await import('@/lib/api/client');
      await api.delete('/test');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRF-Token': 'delete_csrf_token',
          }),
        })
      );
    });

    it('does not include CSRF token for GET requests', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'csrf_token=should_not_appear',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.get('/test');
      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers?.['X-CSRF-Token']).toBeUndefined();
    });

    it('handles CSRF token in cookie with other cookies', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'session=abc123; csrf_token=multi_cookie_csrf; other=value',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.post('/test', {});
      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-CSRF-Token': 'multi_cookie_csrf',
          }),
        })
      );
    });

    it('handles missing CSRF token gracefully', async () => {
      Object.defineProperty(document, 'cookie', {
        writable: true,
        value: 'session=abc123; other=value',
      });
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.post('/test', {});
      // Should not throw, just not include the header
      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers?.['X-CSRF-Token']).toBeUndefined();
    });
  });

  describe('no Authorization header', () => {
    it('does not include Authorization header when using cookies', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.get('/test');
      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers?.Authorization).toBeUndefined();
    });

    it('does not include Authorization header for POST requests', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });
      const { api } = await import('@/lib/api/client');
      await api.post('/test', { data: 'value' });
      const callArgs = mockFetch.mock.calls[0][1];
      expect(callArgs.headers?.Authorization).toBeUndefined();
    });
  });

  describe('request method', () => {
    it('makes request to correct URL', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'test' }),
      });

      const { api } = await import('@/lib/api/client');
      await api.get('/users');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/users',
        expect.any(Object)
      );
    });

    it('sets Content-Type to application/json by default', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      const { api } = await import('@/lib/api/client');
      await api.get('/endpoint');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('returns parsed JSON response', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      });

      const { api } = await import('@/lib/api/client');
      const result = await api.get('/data');

      expect(result).toEqual(mockData);
    });

    it('returns undefined for 204 No Content', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      const { api } = await import('@/lib/api/client');
      const result = await api.delete('/resource/1');

      expect(result).toBeUndefined();
    });

    it('throws ApiError on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Invalid data', code: 'INVALID' }),
      });

      const { api, ApiError: DynamicApiError } = await import('@/lib/api/client');
      await expect(api.get('/bad-request')).rejects.toThrow(DynamicApiError);
    });

    it('throws ApiError with correct properties', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Invalid data', code: 'INVALID' }),
      });

      const { api } = await import('@/lib/api/client');
      await expect(api.get('/bad-request')).rejects.toMatchObject({
        status: 400,
        detail: 'Invalid data',
        code: 'INVALID',
      });
    });

    it('throws ApiError with default message when response is not JSON', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.reject(new Error('Not JSON')),
      });

      const { api } = await import('@/lib/api/client');
      await expect(api.get('/server-error')).rejects.toMatchObject({
        status: 500,
        detail: 'Request failed',
      });
    });

    it('throws ApiError with detail from response when available', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      });

      const { api } = await import('@/lib/api/client');
      await expect(api.get('/expired')).rejects.toMatchObject({
        status: 401,
        detail: 'Token expired',
      });
    });
  });

  describe('HTTP methods', () => {
    beforeEach(() => {
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });
    });

    it('get() makes GET request', async () => {
      const { api } = await import('@/lib/api/client');
      await api.get('/items');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items'),
        expect.objectContaining({ method: 'GET' })
      );
    });

    it('post() makes POST request with JSON body', async () => {
      const data = { name: 'New Item' };
      const { api } = await import('@/lib/api/client');
      await api.post('/items', data);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(data),
        })
      );
    });

    it('post() handles undefined data', async () => {
      const { api } = await import('@/lib/api/client');
      await api.post('/items');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items'),
        expect.objectContaining({
          method: 'POST',
          body: undefined,
        })
      );
    });

    it('postForm() makes POST request with form-urlencoded body', async () => {
      const data = { username: 'test@example.com', password: 'secret' };
      const { api } = await import('@/lib/api/client');
      await api.postForm('/auth/login', data);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: 'username=test%40example.com&password=secret',
          headers: expect.objectContaining({
            'Content-Type': 'application/x-www-form-urlencoded',
          }),
        })
      );
    });

    it('put() makes PUT request with JSON body', async () => {
      const data = { name: 'Updated Item' };
      const { api } = await import('@/lib/api/client');
      await api.put('/items/1', data);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(data),
        })
      );
    });

    it('patch() makes PATCH request with JSON body', async () => {
      const data = { name: 'Patched Item' };
      const { api } = await import('@/lib/api/client');
      await api.patch('/items/1', data);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items/1'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify(data),
        })
      );
    });

    it('delete() makes DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
      });
      const { api } = await import('@/lib/api/client');
      await api.delete('/items/1');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/items/1'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });
});

describe('getCsrfToken', () => {
  beforeEach(() => {
    vi.resetModules();
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  it('returns csrf token from cookie', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=my_csrf_token_123',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('my_csrf_token_123');
  });

  it('returns null when csrf_token cookie is not present', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'other_cookie=value',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBeNull();
  });

  it('returns null when cookies are empty', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBeNull();
  });

  it('handles csrf token with special characters', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=abc%3D%3D123',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('abc==123');
  });

  it('extracts csrf token from multiple cookies', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'session=sess123; csrf_token=csrf_in_middle; user=john',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('csrf_in_middle');
  });
});

describe('Automatic token refresh on 401', () => {
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

  it('retries request after 401 with automatic refresh', async () => {
    const { api } = await import('@/lib/api/client');

    // First call returns 401
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Refresh call succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ access_token: 'new_token' }),
      })
      // Retry original request succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'success' }),
      });

    const result = await api.get('/protected-resource');

    expect(result).toEqual({ data: 'success' });
    expect(mockFetch).toHaveBeenCalledTimes(3);

    // Verify the calls were made correctly
    expect(mockFetch.mock.calls[0][0]).toContain('/protected-resource');
    expect(mockFetch.mock.calls[1][0]).toContain('/auth/refresh');
    expect(mockFetch.mock.calls[2][0]).toContain('/protected-resource');
  });

  it('throws on 401 if refresh also fails', async () => {
    const { api, ApiError } = await import('@/lib/api/client');

    mockFetch
      // First call returns 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Refresh call fails
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Refresh failed' }),
      });

    try {
      await api.get('/protected');
      // Should not reach here
      expect.fail('Expected ApiError to be thrown');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).status).toBe(401);
      expect((error as ApiError).detail).toBe('Token expired');
    }
  });

  it('does not retry more than once after refresh', async () => {
    const { api } = await import('@/lib/api/client');

    mockFetch
      // First call returns 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Refresh call succeeds
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ access_token: 'new_token' }),
      })
      // Retry also returns 401 (token was already revoked for another reason)
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Still unauthorized' }),
      });

    await expect(api.get('/protected')).rejects.toMatchObject({
      status: 401,
      detail: 'Still unauthorized',
    });

    // Should only call fetch 3 times (original, refresh, retry)
    // NOT 4+ times in an infinite loop
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('handles refresh network error gracefully', async () => {
    const { api } = await import('@/lib/api/client');

    mockFetch
      // First call returns 401
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      // Refresh call throws network error
      .mockRejectedValueOnce(new Error('Network error'));

    await expect(api.get('/protected')).rejects.toMatchObject({
      status: 401,
    });
  });

  it('makes refresh request with correct parameters', async () => {
    const { api } = await import('@/lib/api/client');

    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'success' }),
      });

    await api.get('/protected');

    // Verify refresh call has correct options
    const refreshCall = mockFetch.mock.calls[1];
    expect(refreshCall[0]).toContain('/auth/refresh');
    expect(refreshCall[1]).toMatchObject({
      method: 'POST',
      credentials: 'include',
    });
  });

  it('handles concurrent 401 responses with single refresh', async () => {
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
        json: () => Promise.resolve({ data: 'result1' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'result2' }),
      });

    // Make concurrent requests
    const [result1, result2] = await Promise.all([
      api.get('/endpoint1'),
      api.get('/endpoint2'),
    ]);

    expect(result1).toEqual({ data: 'result1' });
    expect(result2).toEqual({ data: 'result2' });

    // Verify refresh was only called once
    const refreshCalls = mockFetch.mock.calls.filter((call) =>
      call[0].includes('/auth/refresh')
    );
    expect(refreshCalls.length).toBe(1);
  });

  it('works correctly for POST requests after refresh', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=test_csrf',
    });

    const { api } = await import('@/lib/api/client');

    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ created: true }),
      });

    const result = await api.post('/resource', { name: 'test' });

    expect(result).toEqual({ created: true });
    expect(mockFetch).toHaveBeenCalledTimes(3);

    // Verify retry has CSRF token
    const retryCall = mockFetch.mock.calls[2];
    expect(retryCall[1].headers).toMatchObject({
      'X-CSRF-Token': 'test_csrf',
    });
  });
});
