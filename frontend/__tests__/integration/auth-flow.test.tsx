/**
 * Integration tests for authentication flow
 * Tests the complete auth flow from login to protected route access
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '@/app/(public)/login/page';
import ProtectedRoute from '@/components/ProtectedRoute';
import { auth } from '@/lib/api';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
};

jest.mock('@/components/ToastContainer', () => ({
  useToast: () => toastMocks,
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('Authentication Flow Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue(undefined);
  });

  describe('Login to Protected Route', () => {
    it('completes full login and access protected content flow', async () => {
      const user = userEvent.setup();

      // Step 1: User is on login page
      (auth.login as jest.Mock).mockResolvedValueOnce('valid-token');

      const { rerender } = render(<LoginPage />);

      // Step 2: User enters credentials
      await user.type(screen.getByLabelText(/email address/i), 'student@example.com');
      await user.type(screen.getByLabelText(/password/i), 'password123');

      // Step 3: User submits form
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      // Step 4: Verify login was called
      await waitFor(() => {
        expect(auth.login).toHaveBeenCalledWith('student@example.com', 'password123');
      });

      // Step 5: Verify success toast and redirect
      await waitFor(() => {
        expect(toastMocks.showSuccess).toHaveBeenCalled();
        expect(mockPush).toHaveBeenCalledWith('/dashboard');
      });

      // Step 6: Now simulate protected route access
      (Cookies.get as jest.Mock).mockReturnValue('valid-token');
      (auth.getCurrentUser as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'student@example.com',
        role: 'student',
        is_active: true,
        is_verified: true,
      });

      rerender(
        <ProtectedRoute>
          <div>Dashboard Content</div>
        </ProtectedRoute>
      );

      // Step 7: Verify protected content is accessible
      await waitFor(() => {
        expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
      });
    });

    it('blocks access when login fails', async () => {
      const user = userEvent.setup();

      (auth.login as jest.Mock).mockRejectedValueOnce({
        response: { data: { detail: 'Invalid credentials' } },
      });

      render(<LoginPage />);

      await user.type(screen.getByLabelText(/email address/i), 'wrong@example.com');
      await user.type(screen.getByLabelText(/password/i), 'wrongpassword');
      await user.click(screen.getByRole('button', { name: /sign in/i }));

      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalledWith('Invalid credentials');
      });

      expect(mockPush).not.toHaveBeenCalledWith('/dashboard');
    });

    it('redirects unauthenticated users from protected routes', async () => {
      (Cookies.get as jest.Mock).mockReturnValue(undefined);

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/');
      });

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });

    it('redirects to unauthorized for wrong role', async () => {
      (Cookies.get as jest.Mock).mockReturnValue('valid-token');
      (auth.getCurrentUser as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'student@example.com',
        role: 'student',
        is_active: true,
      });

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Only Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
      });
    });

    it('allows access when role matches', async () => {
      (Cookies.get as jest.Mock).mockReturnValue('valid-token');
      (auth.getCurrentUser as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'admin@example.com',
        role: 'admin',
        is_active: true,
      });

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Only Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(screen.getByText('Admin Only Content')).toBeInTheDocument();
      });
    });
  });

  describe('Session expiration handling', () => {
    it('handles expired token gracefully', async () => {
      (Cookies.get as jest.Mock).mockReturnValue('expired-token');
      (auth.getCurrentUser as jest.Mock).mockRejectedValue(
        new Error('Token expired')
      );

      render(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(Cookies.remove).toHaveBeenCalledWith('token');
        expect(mockReplace).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Role-based access control', () => {
    const roles = ['student', 'tutor', 'admin', 'owner'] as const;

    roles.forEach((role) => {
      it(`grants access for ${role} when no role required`, async () => {
        (Cookies.get as jest.Mock).mockReturnValue('valid-token');
        (auth.getCurrentUser as jest.Mock).mockResolvedValue({
          id: 1,
          email: `${role}@example.com`,
          role: role,
          is_active: true,
        });

        render(
          <ProtectedRoute>
            <div>Generic Protected Content</div>
          </ProtectedRoute>
        );

        await waitFor(() => {
          expect(screen.getByText('Generic Protected Content')).toBeInTheDocument();
        });
      });
    });

    it('tutor cannot access admin-only route', async () => {
      (Cookies.get as jest.Mock).mockReturnValue('valid-token');
      (auth.getCurrentUser as jest.Mock).mockResolvedValue({
        id: 1,
        email: 'tutor@example.com',
        role: 'tutor',
        is_active: true,
      });

      render(
        <ProtectedRoute requiredRole="admin">
          <div>Admin Panel</div>
        </ProtectedRoute>
      );

      await waitFor(() => {
        expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
      });
    });
  });
});
