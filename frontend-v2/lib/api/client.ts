const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Unsafe HTTP methods that require CSRF protection
const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

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

  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token' && value) {
      return value;
    }
  }
  return null;
}

class ApiClient {
  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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
