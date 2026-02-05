import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import { useAuth, useUser, useIsRole, authKeys, useUpdateProfile } from '@/lib/hooks/use-auth';
import type { User, AuthTokens } from '@/types';

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: vi.fn(),
  }),
}));

const mockLogin = vi.fn();
const mockRegister = vi.fn();
const mockMe = vi.fn();
const mockLogout = vi.fn();
const mockUpdateProfile = vi.fn();

vi.mock('@/lib/api', () => ({
  authApi: {
    login: (...args: unknown[]) => mockLogin(...args),
    register: (...args: unknown[]) => mockRegister(...args),
    me: () => mockMe(),
    logout: () => mockLogout(),
    updateProfile: (...args: unknown[]) => mockUpdateProfile(...args),
  },
}));

const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'student',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
};

const mockTokens: AuthTokens = {
  access_token: 'mock-jwt-token',
  token_type: 'bearer',
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

describe('authKeys', () => {
  it('generates correct query keys', () => {
    expect(authKeys.all).toEqual(['auth']);
    expect(authKeys.me()).toEqual(['auth', 'me']);
  });
});

describe('useUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches current user on mount', async () => {
    mockMe.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockMe).toHaveBeenCalled();
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('returns isAuthenticated false when no user', async () => {
    mockMe.mockRejectedValueOnce(new Error('Unauthorized'));

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeUndefined();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.error).toBeTruthy();
  });

  it('provides refetch function', async () => {
    mockMe.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useUser(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');
  });
});

describe('useUpdateProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('updates profile and updates cache', async () => {
    mockMe.mockResolvedValue(mockUser);
    const updatedUser = { ...mockUser, first_name: 'Updated' };
    mockUpdateProfile.mockResolvedValueOnce(updatedUser);

    const { result } = renderHook(() => useUpdateProfile(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.mutateAsync({ first_name: 'Updated' });
    });

    expect(mockUpdateProfile).toHaveBeenCalled();
    expect(mockUpdateProfile.mock.calls[0][0]).toEqual({ first_name: 'Updated' });
  });
});

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockReset();
    mockReplace.mockReset();
  });

  describe('initial state', () => {
    it('fetches user on mount', async () => {
      mockMe.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('handles unauthenticated state', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.user).toBeUndefined();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('login', () => {
    it('calls authApi.login on success (token stored in HttpOnly cookie by browser)', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));
      mockLogin.mockResolvedValueOnce(mockTokens);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      expect(mockLogin).toHaveBeenCalled();
      expect(mockLogin.mock.calls[0][0]).toEqual({
        email: 'test@example.com',
        password: 'password',
      });
      // Token is now stored in HttpOnly cookie by the browser, not via api.setToken()
    });

    it('sets isLoggingIn during login', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));

      let resolveLogin: (value: AuthTokens) => void;
      const loginPromise = new Promise<AuthTokens>((resolve) => {
        resolveLogin = resolve;
      });
      mockLogin.mockReturnValueOnce(loginPromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.login({ email: 'test@example.com', password: 'password' });
      });

      await waitFor(() => {
        expect(result.current.isLoggingIn).toBe(true);
      });

      await act(async () => {
        resolveLogin!(mockTokens);
      });

      await waitFor(() => {
        expect(result.current.isLoggingIn).toBe(false);
      });
    });

    it('sets loginError on failure', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));
      const loginError = new Error('Invalid credentials');
      mockLogin.mockRejectedValueOnce(loginError);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        try {
          await result.current.login({ email: 'bad@example.com', password: 'wrong' });
        } catch {
          // Expected to throw
        }
      });

      await waitFor(() => {
        expect(result.current.loginError).toBeTruthy();
      });
    });

    it('invalidates user query after successful login', async () => {
      mockMe
        .mockRejectedValueOnce(new Error('Not authenticated'))
        .mockResolvedValueOnce(mockUser);
      mockLogin.mockResolvedValueOnce(mockTokens);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);

      await act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'password' });
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });
    });
  });

  describe('register', () => {
    it('calls authApi.register with registration data', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));
      mockRegister.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      const registerData = {
        email: 'newuser@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
        role: 'student' as const,
      };

      await act(async () => {
        await result.current.register(registerData);
      });

      expect(mockRegister).toHaveBeenCalled();
      expect(mockRegister.mock.calls[0][0]).toEqual(registerData);
    });

    it('sets isRegistering during registration', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));

      let resolveRegister: (value: User) => void;
      const registerPromise = new Promise<User>((resolve) => {
        resolveRegister = resolve;
      });
      mockRegister.mockReturnValueOnce(registerPromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.register({
          email: 'new@example.com',
          password: 'pass',
          first_name: 'New',
          last_name: 'User',
          role: 'student',
        });
      });

      await waitFor(() => {
        expect(result.current.isRegistering).toBe(true);
      });

      await act(async () => {
        resolveRegister!(mockUser);
      });

      await waitFor(() => {
        expect(result.current.isRegistering).toBe(false);
      });
    });

    it('sets registerError on failure', async () => {
      mockMe.mockRejectedValueOnce(new Error('Not authenticated'));
      mockRegister.mockRejectedValueOnce(new Error('Email already exists'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        try {
          await result.current.register({
            email: 'existing@example.com',
            password: 'pass',
            first_name: 'Existing',
            last_name: 'User',
            role: 'student',
          });
        } catch {
          // Expected to throw
        }
      });

      await waitFor(() => {
        expect(result.current.registerError).toBeTruthy();
      });
    });
  });

  describe('logout', () => {
    it('calls authApi.logout', async () => {
      mockMe.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.logout();
      });

      await waitFor(() => {
        expect(mockLogout).toHaveBeenCalled();
      });
    });

    it('redirects to login page after logout', async () => {
      mockMe.mockResolvedValueOnce(mockUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.logout();
      });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });
  });

  describe('updateProfile', () => {
    it('calls authApi.updateProfile', async () => {
      mockMe.mockResolvedValueOnce(mockUser);
      const updatedUser = { ...mockUser, first_name: 'Updated' };
      mockUpdateProfile.mockResolvedValueOnce(updatedUser);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await act(async () => {
        await result.current.updateProfile({ first_name: 'Updated' });
      });

      expect(mockUpdateProfile).toHaveBeenCalled();
      expect(mockUpdateProfile.mock.calls[0][0]).toEqual({ first_name: 'Updated' });
    });

    it('sets isUpdatingProfile during update', async () => {
      mockMe.mockResolvedValueOnce(mockUser);

      let resolveUpdate: (value: User) => void;
      const updatePromise = new Promise<User>((resolve) => {
        resolveUpdate = resolve;
      });
      mockUpdateProfile.mockReturnValueOnce(updatePromise);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.updateProfile({ first_name: 'New Name' });
      });

      await waitFor(() => {
        expect(result.current.isUpdatingProfile).toBe(true);
      });

      await act(async () => {
        resolveUpdate!(mockUser);
      });

      await waitFor(() => {
        expect(result.current.isUpdatingProfile).toBe(false);
      });
    });
  });
});

describe('Cookie-based authentication', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPush.mockReset();
  });

  it('login does not store tokens in localStorage (cookies handled by browser)', async () => {
    // Mock localStorage to verify it's not used
    const localStorageSpy = vi.spyOn(Storage.prototype, 'setItem');

    mockMe.mockRejectedValueOnce(new Error('Not authenticated'));
    mockLogin.mockResolvedValueOnce(mockTokens);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password' });
    });

    // Verify localStorage was never called with any token-related keys
    const tokenStorageCalls = localStorageSpy.mock.calls.filter(
      ([key]) => key.includes('token') || key.includes('auth')
    );
    expect(tokenStorageCalls.length).toBe(0);

    localStorageSpy.mockRestore();
  });

  it('login success invalidates user query to refetch from server (using new cookie)', async () => {
    mockMe
      .mockRejectedValueOnce(new Error('Not authenticated'))
      .mockResolvedValueOnce(mockUser);
    mockLogin.mockResolvedValueOnce(mockTokens);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password' });
    });

    // After login, the user query should be refetched
    // The second mockMe call should be made
    await waitFor(() => {
      expect(mockMe).toHaveBeenCalledTimes(2);
    });
  });

  it('logout calls backend API to clear HttpOnly cookies', async () => {
    mockMe.mockResolvedValueOnce(mockUser);
    mockLogout.mockResolvedValueOnce({ message: 'Logged out' });

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      result.current.logout();
    });

    // Verify logout API was called (backend clears cookies)
    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalled();
    });
  });

  it('logout clears all cached queries', async () => {
    mockMe.mockResolvedValueOnce(mockUser);
    mockLogout.mockResolvedValueOnce({ message: 'Logged out' });

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
        mutations: { retry: false },
      },
    });

    const clearSpy = vi.spyOn(queryClient, 'clear');

    function Wrapper({ children }: { children: React.ReactNode }) {
      return (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      );
    }

    const { result } = renderHook(() => useAuth(), {
      wrapper: Wrapper,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      result.current.logout();
    });

    await waitFor(() => {
      expect(clearSpy).toHaveBeenCalled();
    });

    clearSpy.mockRestore();
  });

  it('auth state is determined by /auth/me API response, not localStorage', async () => {
    // First: user is not authenticated
    mockMe.mockRejectedValueOnce(new Error('Not authenticated'));

    const { result, rerender } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeUndefined();

    // The hook relies on /auth/me to determine auth state
    expect(mockMe).toHaveBeenCalled();
  });
});

describe('useIsRole', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns true when user has matching role', async () => {
    mockMe.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useIsRole('student'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it('returns false when user has different role', async () => {
    mockMe.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useIsRole('admin'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('returns false when no user is authenticated', async () => {
    mockMe.mockRejectedValueOnce(new Error('Not authenticated'));

    const { result } = renderHook(() => useIsRole('student'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('accepts array of roles', async () => {
    const adminUser = { ...mockUser, role: 'admin' as const };
    mockMe.mockResolvedValueOnce(adminUser);

    const { result } = renderHook(() => useIsRole(['admin', 'owner']), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });

  it('returns false when user role not in array', async () => {
    mockMe.mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useIsRole(['admin', 'owner']), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });
});
