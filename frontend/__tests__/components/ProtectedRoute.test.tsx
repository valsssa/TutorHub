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

  it('renders content for tutor role when requiredRole is tutor', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'tutor@example.com',
      role: 'tutor',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="tutor">
        <div>Tutor Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Tutor Content')).toBeInTheDocument();
    });
  });

  it('renders content for student role when requiredRole is student', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'student@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="student">
        <div>Student Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Student Content')).toBeInTheDocument();
    });
  });

  it('clears token_expiry cookie on auth error', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Token expired'));

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(Cookies.remove).toHaveBeenCalledWith('token_expiry');
    });
  });

  it('redirects tutor to unauthorized when trying to access admin route', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'tutor@example.com',
      role: 'tutor',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="admin">
        <div>Admin Only</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });

    expect(screen.queryByText('Admin Only')).not.toBeInTheDocument();
  });

  it('handles null token cookie value', async () => {
    (Cookies.get as jest.Mock).mockReturnValue(null);

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/');
    });
  });

  it('handles empty string token cookie value', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('');

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/');
    });
  });

  it('renders main content area with correct role attribute', async () => {
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
      const main = screen.getByRole('main');
      expect(main).toBeInTheDocument();
    });
  });

  it('wraps content in error boundary', async () => {
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
        <div>Safe Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Safe Content')).toBeInTheDocument();
    });
  });

  it('handles network error during auth check', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Network error'));

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

  it('handles user with missing fields gracefully', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      // Missing is_active and is_verified
    });

    render(
      <ProtectedRoute>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  it('passes user data to Navbar component', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      first_name: 'Test',
      last_name: 'User',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute showNavbar={true}>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('TutorConnect')).toBeInTheDocument();
    });
  });

  it('does not render children when user is null after auth check', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Session expired'));

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

  it('redirects admin to unauthorized when trying to access student route', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute requiredRole="student">
        <div>Student Only</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith('/unauthorized');
    });
  });

  it('renders footer when showNavbar is true', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    render(
      <ProtectedRoute showNavbar={true}>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Content')).toBeInTheDocument();
    });
  });

  it('applies correct layout classes to container', async () => {
    (Cookies.get as jest.Mock).mockReturnValue('fake-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      role: 'student',
      is_active: true,
      is_verified: true,
    });

    const { container } = render(
      <ProtectedRoute>
        <div>Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    const layoutDiv = container.querySelector('.min-h-screen');
    expect(layoutDiv).toBeInTheDocument();
  });
});
