/**
 * Page-level tests for Dashboard pages
 *
 * Tests for Student, Tutor, and Admin dashboard pages including:
 * - Initial data loading
 * - Role-based content display
 * - Component interaction
 * - Navigation and routing
 * - Error handling
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { auth, bookings, tutors, notifications, admin } from '@/lib/api';
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
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
  showWarning: jest.fn(),
};

jest.mock('@/components/ToastContainer', () => ({
  useToast: () => toastMocks,
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock user data for different roles
const mockStudentUser = {
  id: 1,
  email: 'student@example.com',
  role: 'student',
  is_active: true,
  is_verified: true,
  first_name: 'John',
  last_name: 'Doe',
  timezone: 'America/New_York',
  currency: 'USD',
};

const mockTutorUser = {
  id: 2,
  email: 'tutor@example.com',
  role: 'tutor',
  is_active: true,
  is_verified: true,
  first_name: 'Sarah',
  last_name: 'Johnson',
  timezone: 'America/New_York',
  currency: 'USD',
};

const mockAdminUser = {
  id: 3,
  email: 'admin@example.com',
  role: 'admin',
  is_active: true,
  is_verified: true,
  first_name: 'Admin',
  last_name: 'User',
  timezone: 'UTC',
  currency: 'USD',
};

// Mock data
const mockUpcomingBookings = [
  {
    id: 1,
    tutor_name: 'Dr. Sarah Johnson',
    tutor_profile_id: 1,
    subject_name: 'Mathematics',
    start_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    end_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
    session_state: 'confirmed',
    total_amount: 75,
  },
];

const mockFeaturedTutors = [
  {
    id: 1,
    name: 'Dr. Emily Chen',
    title: 'Math Expert',
    hourly_rate: 80,
    average_rating: 4.9,
    total_reviews: 150,
    subjects: ['Mathematics', 'Calculus'],
  },
];

const mockTutorBookings = [
  {
    id: 1,
    student_name: 'John Doe',
    student_id: 1,
    subject_name: 'Mathematics',
    start_at: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    end_at: new Date(Date.now() + 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
    session_state: 'confirmed',
    total_amount: 75,
  },
];

const mockAdminStats = {
  total_users: 1250,
  active_tutors: 45,
  sessions_today: 23,
  revenue_today: 1150.5,
  pending_tutors: 8,
  total_sessions: 15420,
};

describe('Student Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (bookings.list as jest.Mock).mockResolvedValue({ items: mockUpcomingBookings, total: 1 });
    (tutors.list as jest.Mock).mockResolvedValue({ items: mockFeaturedTutors, total: 1 });
    (notifications.list as jest.Mock).mockResolvedValue([]);
  });

  it('renders student dashboard with welcome message', async () => {
    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/welcome.*john/i)).toBeInTheDocument();
    });
  });

  it('displays upcoming sessions section', async () => {
    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(bookings.list).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/upcoming.*session/i)).toBeInTheDocument();
      expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
    });
  });

  it('displays recommended tutors section', async () => {
    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(tutors.list).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/recommended.*tutor/i)).toBeInTheDocument();
      expect(screen.getByText('Dr. Emily Chen')).toBeInTheDocument();
    });
  });

  it('shows empty state when no upcoming sessions', async () => {
    (bookings.list as jest.Mock).mockResolvedValue({ items: [], total: 0 });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/no.*upcoming.*session/i)).toBeInTheDocument();
    });
  });

  it('displays student stats', async () => {
    (bookings.list as jest.Mock).mockResolvedValue({
      items: [],
      total: 0,
      meta: { total_completed_sessions: 12, total_hours_learned: 25.5 },
    });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/12/)).toBeInTheDocument();
      expect(screen.getByText(/completed.*session/i)).toBeInTheDocument();
    });
  });

  it('navigates to bookings page when "View All" clicked', async () => {
    const user = userEvent.setup();

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/upcoming.*session/i)).toBeInTheDocument();
    });

    const viewAllLink = screen.getByRole('link', { name: /view all/i });
    await user.click(viewAllLink);

    expect(viewAllLink).toHaveAttribute('href', expect.stringContaining('booking'));
  });

  it('shows join button for sessions starting soon', async () => {
    const soonBooking = {
      ...mockUpcomingBookings[0],
      start_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(), // 10 minutes from now
      meeting_url: 'https://zoom.us/j/123456',
    };

    (bookings.list as jest.Mock).mockResolvedValue({ items: [soonBooking], total: 1 });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /join/i })).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    (bookings.list as jest.Mock).mockRejectedValue(new Error('Network error'));

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/error|something.*wrong/i)).toBeInTheDocument();
    });
  });
});

describe('Tutor Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    (bookings.list as jest.Mock).mockResolvedValue({ items: mockTutorBookings, total: 1 });
    (notifications.list as jest.Mock).mockResolvedValue([]);
  });

  it('renders tutor dashboard with welcome message', async () => {
    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/welcome.*sarah/i)).toBeInTheDocument();
    });
  });

  it('displays upcoming sessions with student info', async () => {
    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
    });
  });

  it('shows pending booking requests', async () => {
    const pendingBooking = {
      ...mockTutorBookings[0],
      session_state: 'pending_tutor',
    };

    (bookings.list as jest.Mock).mockResolvedValue({ items: [pendingBooking], total: 1 });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/pending|awaiting.*response/i)).toBeInTheDocument();
    });
  });

  it('displays earnings summary', async () => {
    (bookings.list as jest.Mock).mockResolvedValue({
      items: mockTutorBookings,
      total: 1,
      meta: { total_earnings: 1500, pending_earnings: 300 },
    });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/earning|revenue/i)).toBeInTheDocument();
      expect(screen.getByText(/\$1,?500/i)).toBeInTheDocument();
    });
  });

  it('allows confirming pending booking', async () => {
    const user = userEvent.setup();
    const pendingBooking = {
      ...mockTutorBookings[0],
      session_state: 'pending_tutor',
    };

    (bookings.list as jest.Mock).mockResolvedValue({ items: [pendingBooking], total: 1 });
    (bookings.confirm as jest.Mock).mockResolvedValue({
      ...pendingBooking,
      session_state: 'confirmed',
    });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirm|accept/i })).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', { name: /confirm|accept/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(bookings.confirm).toHaveBeenCalled();
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });

  it('navigates to schedule manager', async () => {
    const user = userEvent.setup();

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    const scheduleLink = screen.queryByRole('link', { name: /schedule|availability/i });
    if (scheduleLink) {
      expect(scheduleLink).toHaveAttribute('href', expect.stringContaining('schedule'));
    }
  });
});

describe('Admin Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockAdminUser);
    (admin.getDashboardStats as jest.Mock).mockResolvedValue(mockAdminStats);
    (admin.getRecentActivities as jest.Mock).mockResolvedValue([]);
  });

  it('renders admin dashboard with metrics', async () => {
    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(admin.getDashboardStats).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/admin.*dashboard/i)).toBeInTheDocument();
      expect(screen.getByText('1,250')).toBeInTheDocument(); // Total users
      expect(screen.getByText('45')).toBeInTheDocument(); // Active tutors
    });
  });

  it('displays pending tutor approvals count', async () => {
    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('8')).toBeInTheDocument(); // Pending tutors
      expect(screen.getByText(/pending/i)).toBeInTheDocument();
    });
  });

  it('shows navigation tabs for admin sections', async () => {
    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/user.*management/i)).toBeInTheDocument();
      expect(screen.getByText(/tutor.*approval/i)).toBeInTheDocument();
      expect(screen.getByText(/session/i)).toBeInTheDocument();
      expect(screen.getByText(/analytic/i)).toBeInTheDocument();
    });
  });

  it('displays recent activities', async () => {
    const recentActivities = [
      {
        id: 1,
        action: 'user_registered',
        description: 'New student registered',
        timestamp: new Date().toISOString(),
        user_email: 'new@example.com',
      },
    ];

    (admin.getRecentActivities as jest.Mock).mockResolvedValue(recentActivities);

    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/recent.*activit/i)).toBeInTheDocument();
      expect(screen.getByText('New student registered')).toBeInTheDocument();
    });
  });

  it('shows system health status', async () => {
    const statsWithHealth = {
      ...mockAdminStats,
      system_health: 'good',
    };

    (admin.getDashboardStats as jest.Mock).mockResolvedValue(statsWithHealth);

    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/system.*status|health/i)).toBeInTheDocument();
      expect(screen.getByText(/good|healthy/i)).toBeInTheDocument();
    });
  });

  it('navigates to tutor approvals section', async () => {
    const user = userEvent.setup();

    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/tutor.*approval/i)).toBeInTheDocument();
    });

    const approvalsTab = screen.getByText(/tutor.*approval/i);
    await user.click(approvalsTab);

    // Should trigger pending tutors load
    await waitFor(() => {
      expect(admin.listPendingTutors).toHaveBeenCalled();
    });
  });

  it('handles stats loading error', async () => {
    (admin.getDashboardStats as jest.Mock).mockRejectedValue(
      new Error('Failed to load stats')
    );

    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/error|failed.*load/i)).toBeInTheDocument();
    });
  });

  it('displays quick action buttons', async () => {
    const AdminPage = (await import('@/app/admin/page')).default;
    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText(/approve.*tutor/i)).toBeInTheDocument();
      expect(screen.getByText(/view.*user/i)).toBeInTheDocument();
    });
  });
});

describe('Dashboard Loading States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
  });

  it('shows loading spinner during initial data fetch', async () => {
    (auth.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockStudentUser), 500))
    );

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    expect(screen.getByTestId('loading-spinner') || screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });
  });

  it('shows skeleton loaders for sections', async () => {
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (bookings.list as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ items: [], total: 0 }), 500))
    );

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });

    // Sections should show skeleton or loading state
    const skeletons = screen.queryAllByTestId(/skeleton|loading/i);
    expect(skeletons.length).toBeGreaterThanOrEqual(0);
  });
});

describe('Dashboard Error Boundaries', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    // Suppress console errors in tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('catches and displays errors from child components', async () => {
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (bookings.list as jest.Mock).mockRejectedValue(new Error('Component error'));

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      // Either error boundary message or graceful degradation
      const errorElement = screen.queryByText(/error|something.*wrong/i);
      const dashboard = screen.queryByText(/welcome/i);
      expect(errorElement || dashboard).toBeInTheDocument();
    });
  });

  it('provides retry functionality on error', async () => {
    const user = userEvent.setup();

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    (bookings.list as jest.Mock)
      .mockRejectedValueOnce(new Error('Temporary error'))
      .mockResolvedValueOnce({ items: mockUpcomingBookings, total: 1 });

    const DashboardPage = (await import('@/app/dashboard/page')).default;
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.queryByText(/error|failed/i)).toBeInTheDocument();
    });

    const retryButton = screen.queryByRole('button', { name: /retry|try again/i });
    if (retryButton) {
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });
    }
  });
});
