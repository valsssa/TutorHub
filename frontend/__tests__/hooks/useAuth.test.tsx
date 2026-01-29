/**
 * Tests for useAuth hook
 * Critical: Authentication is the foundation for all protected routes
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useAuth } from '@/hooks/useAuth';
import { auth } from '@/lib/api';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
}));

const mockReplace = jest.fn();

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns loading state initially', () => {
    (auth.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useAuth());

    expect(result.current.loading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it('fetches and returns user on mount', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isStudent).toBe(true);
    expect(result.current.isTutor).toBe(false);
    expect(result.current.isAdmin).toBe(false);
  });

  it('redirects to unauthorized when role does not match', async () => {
    const mockUser = {
      id: 1,
      email: 'student@example.com',
      role: 'student',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    renderHook(() => useAuth({ requiredRole: 'admin' }));

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });
  });

  it('sets error and redirects on auth failure', async () => {
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(
      new Error('Not authenticated')
    );

    const { result } = renderHook(() => useAuth({ redirectTo: '/login' }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Authentication failed');
    expect(result.current.user).toBeNull();
    expect(mockReplace).toHaveBeenCalledWith('/login');
  });

  it('correctly identifies admin role', async () => {
    const mockAdmin = {
      id: 1,
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockAdmin);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isAdmin).toBe(true);
    expect(result.current.isTutor).toBe(false);
    expect(result.current.isStudent).toBe(false);
    expect(result.current.isOwner).toBe(false);
  });

  it('correctly identifies tutor role', async () => {
    const mockTutor = {
      id: 2,
      email: 'tutor@example.com',
      role: 'tutor',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutor);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.isTutor).toBe(true);
    expect(result.current.isStudent).toBe(false);
  });

  it('provides logout function that clears user', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
    (auth.logout as jest.Mock).mockImplementation(() => {});

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.user).not.toBeNull();
    });

    act(() => {
      result.current.logout();
    });

    expect(auth.logout).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
  });

  it('allows role when requiredRole matches', async () => {
    const mockAdmin = {
      id: 1,
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockAdmin);

    const { result } = renderHook(() => useAuth({ requiredRole: 'admin' }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual(mockAdmin);
    expect(mockReplace).not.toHaveBeenCalledWith('/unauthorized');
  });
});
