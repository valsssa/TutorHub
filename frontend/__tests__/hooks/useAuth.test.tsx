/**
 * Tests for useAuth hook
 * Critical: Authentication is the foundation for all protected routes
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useAuth } from '@/hooks/useAuth';

// Increase Jest timeout for all tests in this file
jest.setTimeout(15000);

// Mock next/navigation
const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
}));

// Mock auth module
let mockGetCurrentUserImpl: () => Promise<any>;
const mockLogout = jest.fn();

jest.mock('@/lib/api', () => ({
  auth: {
    getCurrentUser: () => mockGetCurrentUserImpl(),
    logout: () => mockLogout(),
  },
}));

// Helper to flush all pending promises
const flushPromises = () => new Promise(resolve => setTimeout(resolve, 0));

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogout.mockReset();
    // Default to pending promise
    mockGetCurrentUserImpl = () => new Promise(() => {});
  });

  it('returns loading state initially', () => {
    mockGetCurrentUserImpl = () => new Promise(() => {});

    const { result } = renderHook(() => useAuth());

    expect(result.current.loading).toBe(true);
    expect(result.current.user).toBeNull();
  });

  it('fetches and returns user on mount', async () => {
    const mockUser = { id: 1, email: 'test@example.com', role: 'student', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockUser);

    const { result } = renderHook(() => useAuth());

    // Flush promises and wait for state update
    await act(async () => {
      await flushPromises();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isStudent).toBe(true);
  });

  it('redirects to unauthorized when role does not match', async () => {
    const mockUser = { id: 1, email: 'student@example.com', role: 'student', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockUser);

    renderHook(() => useAuth({ requiredRole: 'admin' }));

    await act(async () => {
      await flushPromises();
    });

    expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
  });

  it('sets error and redirects on auth failure', async () => {
    mockGetCurrentUserImpl = () => Promise.reject(new Error('Not authenticated'));

    const { result } = renderHook(() => useAuth({ redirectTo: '/login' }));

    await act(async () => {
      await flushPromises();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe('Authentication failed');
    expect(mockReplace).toHaveBeenCalledWith('/login');
  });

  it('correctly identifies admin role', async () => {
    const mockAdmin = { id: 1, email: 'admin@example.com', role: 'admin', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockAdmin);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await flushPromises();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.isAdmin).toBe(true);
    expect(result.current.isTutor).toBe(false);
    expect(result.current.isStudent).toBe(false);
  });

  it('correctly identifies tutor role', async () => {
    const mockTutor = { id: 2, email: 'tutor@example.com', role: 'tutor', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockTutor);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await flushPromises();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.isTutor).toBe(true);
    expect(result.current.isStudent).toBe(false);
  });

  it('provides logout function that clears user', async () => {
    const mockUser = { id: 1, email: 'test@example.com', role: 'student', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockUser);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await flushPromises();
    });

    expect(result.current.user).not.toBeNull();

    act(() => {
      result.current.logout();
    });

    expect(mockLogout).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
  });

  it('allows matching requiredRole', async () => {
    const mockAdmin = { id: 1, email: 'admin@example.com', role: 'admin', is_active: true };
    mockGetCurrentUserImpl = () => Promise.resolve(mockAdmin);

    const { result } = renderHook(() => useAuth({ requiredRole: 'admin' }));

    await act(async () => {
      await flushPromises();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.user).toEqual(mockAdmin);
    expect(mockReplace).not.toHaveBeenCalledWith('/unauthorized');
  });
});
