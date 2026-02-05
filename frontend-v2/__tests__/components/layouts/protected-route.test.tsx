import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    back: vi.fn(),
  }),
  redirect: vi.fn(),
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
};

Object.defineProperty(global, 'localStorage', {
  value: mockLocalStorage,
});

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

describe('Protected Route Behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe('Authentication Check', () => {
    it('should redirect to login when user is not authenticated', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      });

      const { useAuth } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { user, isLoading, isAuthenticated } = useAuth();

        if (isLoading) return <div>Loading...</div>;
        if (!isAuthenticated) {
          mockPush('/login');
          return null;
        }
        return <div>Protected Content</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });

    it('should render protected content when user is authenticated', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        role: 'student',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUser),
      });

      const { useAuth } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { user, isLoading, isAuthenticated } = useAuth();

        if (isLoading) return <div>Loading...</div>;
        if (!isAuthenticated) {
          mockPush('/login');
          return null;
        }
        return <div>Protected Content for {user?.email}</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText(/Protected Content/)).toBeInTheDocument();
      });

      expect(mockPush).not.toHaveBeenCalledWith('/login');
    });

    it('should show loading state while checking authentication', async () => {
      mockFetch.mockImplementation(() => new Promise(() => {}));

      const { useAuth } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { isLoading } = useAuth();

        if (isLoading) return <div>Loading...</div>;
        return <div>Protected Content</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('Role-Based Access', () => {
    it('should allow access for matching role', async () => {
      const mockUser = {
        id: 1,
        email: 'student@example.com',
        role: 'student',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUser),
      });

      const { useAuth, useIsRole } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { isLoading } = useAuth();
        const isStudent = useIsRole('student');

        if (isLoading) return <div>Loading...</div>;
        if (!isStudent) {
          mockPush('/unauthorized');
          return null;
        }
        return <div>Student Dashboard</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Student Dashboard')).toBeInTheDocument();
      });

      expect(mockPush).not.toHaveBeenCalledWith('/unauthorized');
    });

    it('should deny access for non-matching role', async () => {
      const mockUser = {
        id: 1,
        email: 'student@example.com',
        role: 'student',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUser),
      });

      const { useAuth, useIsRole } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { isLoading } = useAuth();
        const isAdmin = useIsRole('admin');

        if (isLoading) return <div>Loading...</div>;
        if (!isAdmin) {
          mockPush('/unauthorized');
          return null;
        }
        return <div>Admin Dashboard</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/unauthorized');
      });

      expect(screen.queryByText('Admin Dashboard')).not.toBeInTheDocument();
    });

    it('should allow access for any of multiple roles', async () => {
      const mockUser = {
        id: 1,
        email: 'tutor@example.com',
        role: 'tutor',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockUser),
      });

      const { useAuth, useIsRole } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { isLoading } = useAuth();
        const hasAccess = useIsRole(['student', 'tutor']);

        if (isLoading) return <div>Loading...</div>;
        if (!hasAccess) {
          mockPush('/unauthorized');
          return null;
        }
        return <div>Learning Area</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(screen.getByText('Learning Area')).toBeInTheDocument();
      });

      expect(mockPush).not.toHaveBeenCalledWith('/unauthorized');
    });
  });

  describe('Token Handling', () => {
    it('should redirect to login when token is expired', async () => {
      mockLocalStorage.getItem.mockReturnValue('expired-token');

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Token expired' }),
      });

      const { useAuth } = await import('@/lib/hooks/use-auth');

      const TestComponent = () => {
        const { isLoading, isAuthenticated } = useAuth();

        if (isLoading) return <div>Loading...</div>;
        if (!isAuthenticated) {
          mockPush('/login');
          return null;
        }
        return <div>Protected Content</div>;
      };

      render(<TestComponent />, { wrapper: createWrapper() });

      await waitFor(() => {
        expect(mockPush).toHaveBeenCalledWith('/login');
      });
    });
  });
});
