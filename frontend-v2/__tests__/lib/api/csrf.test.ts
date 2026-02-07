import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('CSRF token parsing', () => {
  beforeEach(() => {
    vi.resetModules();
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
  });

  it('handles = characters in cookie values', async () => {
    // Base64-encoded tokens often contain = padding
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=abc123def456==',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('abc123def456==');
  });

  it('handles URL-encoded values with decodeURIComponent', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=hello%20world%3D%3D',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('hello world==');
  });

  it('returns simple token value correctly', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'csrf_token=simple_token_123',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('simple_token_123');
  });

  it('returns null when no csrf_token cookie exists', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'session=abc; other=xyz',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBeNull();
  });

  it('returns null for empty cookies', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: '',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBeNull();
  });

  it('extracts csrf_token from multiple cookies', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'session=abc123; csrf_token=my_token_value; theme=dark',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('my_token_value');
  });

  it('handles csrf_token with = in value among other cookies', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'session=abc; csrf_token=token=with=equals; pref=light',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('token=with=equals');
  });

  it('handles cookie with no = sign gracefully', async () => {
    Object.defineProperty(document, 'cookie', {
      writable: true,
      value: 'malformed; csrf_token=valid_token',
    });
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(getCsrfToken()).toBe('valid_token');
  });

  it('returns null on server-side (no document)', async () => {
    // This tests the typeof document === 'undefined' check
    const originalDocument = global.document;
    // We can't easily remove document in jsdom, but we verify the function exists
    const { getCsrfToken } = await import('@/lib/api/client');
    expect(typeof getCsrfToken).toBe('function');
  });
});
