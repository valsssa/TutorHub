const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Unsafe HTTP methods that require CSRF protection
const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

// Extended RequestInit to track retry attempts
interface ExtendedRequestInit extends RequestInit {
  _isRetry?: boolean;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public code?: string
  ) {
    super(detail);
    this.name = 'ApiError';
  }

  get isUnauthorized() { return this.status === 401; }
  get isForbidden() { return this.status === 403; }
  get isNotFound() { return this.status === 404; }
  get isValidation() { return this.status === 422; }
  get isServerError() { return this.status >= 500; }
}

/**
 * Reads the CSRF token from document.cookie
 * Returns null if the csrf_token cookie is not present
 */
export function getCsrfToken(): string | null {
  if (typeof document === 'undefined') {
    return null;
  }

  try {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      const eqIndex = trimmed.indexOf('=');
      if (eqIndex === -1) continue;
      const name = trimmed.slice(0, eqIndex);
      const rawValue = trimmed.slice(eqIndex + 1);
      if (name === 'csrf_token' && rawValue) {
        return decodeURIComponent(rawValue);
      }
    }
  } catch {
    // Malformed cookie - return null gracefully
  }
  return null;
}

class ApiClient {
  private refreshPromise: Promise<boolean> | null = null;

  /**
   * Try to refresh the access token using the refresh token cookie.
   * Returns true if refresh was successful, false otherwise.
   */
  private async tryRefresh(): Promise<boolean> {
    try {
      const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  async request<T>(endpoint: string, options: ExtendedRequestInit = {}): Promise<T> {
    const method = options.method || 'GET';
    const isUnsafeMethod = UNSAFE_METHODS.includes(method.toUpperCase());

    // Build headers - include CSRF token for unsafe methods
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add CSRF token for unsafe methods (POST, PUT, PATCH, DELETE)
    if (isUnsafeMethod) {
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        (headers as Record<string, string>)['X-CSRF-Token'] = csrfToken;
      }
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Always include cookies for cross-origin requests
    });

    // On 401, try to refresh tokens (unless this is already a retry)
    if (response.status === 401 && !options._isRetry) {
      // Ensure only one refresh happens at a time; concurrent requests queue on the same promise
      if (!this.refreshPromise) {
        this.refreshPromise = this.tryRefresh().finally(() => {
          this.refreshPromise = null;
        });
      }

      const refreshed = await this.refreshPromise;
      if (refreshed) {
        // Retry original request with _isRetry flag to prevent infinite loops
        return this.request<T>(endpoint, { ...options, _isRetry: true });
      }
    }

    if (!response.ok) {
      let errorDetail = 'Request failed';
      let errorCode: string | undefined;

      try {
        const errorBody = await response.json();
        errorDetail = errorBody.detail || errorDetail;
        errorCode = errorBody.code;
      } catch {
        // Response wasn't JSON
      }

      throw new ApiError(response.status, errorDetail, errorCode);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  get<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data?: unknown) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  postForm<T>(endpoint: string, data: Record<string, string>) {
    const formData = new URLSearchParams(data);

    // Get CSRF token for form submission
    const csrfToken = getCsrfToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/x-www-form-urlencoded',
    };
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    return this.request<T>(endpoint, {
      method: 'POST',
      body: formData.toString(),
      headers,
    });
  }

  put<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  patch<T>(endpoint: string, data: unknown) {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient();
