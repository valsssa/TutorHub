import { render, screen, waitFor } from '../test-utils';
import ProtectedRoute from '@/components/ProtectedRoute';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { auth } from '@/lib/api';

// Mock next/navigation with a configurable implementation
const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('js-cookie');
jest.mock('@/lib/api');

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockReplace.mockClear();
    mockPush.mockClear();
  });

  it('redirects to home when no token', async () => {
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

  it('shows loading spinner while checking auth', () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders children when authenticated', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('redirects to unauthorized when role does not match', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="admin">
        <div>Admin Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });
  });

  it('renders content when role matches', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="admin">
        <div>Admin Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Content')).toBeInTheDocument();
    });
  });

  it('redirects to home on auth error', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Auth failed'));

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

  it('shows navbar by default', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('TutorConnect')).toBeInTheDocument();
    });
  });

  it('hides navbar when showNavbar is false', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute showNavbar={false}>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.queryByText('TutorConnect')).not.toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });
});
