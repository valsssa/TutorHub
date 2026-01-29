/**
 * Tests for Navbar component
 * Critical: Role-based navigation, accessibility, user menu
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Navbar from '@/components/Navbar';
import { messages } from '@/lib/api';

// Mock dependencies
jest.mock('@/lib/api', () => ({
  auth: {
    logout: jest.fn(),
  },
  messages: {
    getUnreadCount: jest.fn(),
  },
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

jest.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: jest.fn(),
  }),
}));

jest.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    lastMessage: null,
    isConnected: true,
  }),
}));

jest.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode }) => <div {...props}>{children}</div>,
  },
}));

const mockPush = jest.fn();

describe('Navbar', () => {
  const studentUser = {
    id: 1,
    email: 'student@example.com',
    role: 'student',
    is_active: true,
    is_verified: true,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    avatar_url: null,
    avatarUrl: null,
    currency: 'USD',
    timezone: 'UTC',
    first_name: 'John',
    last_name: 'Student',
    country: null,
    bio: null,
    learning_goal: null,
  };

  const tutorUser = {
    ...studentUser,
    id: 2,
    email: 'tutor@example.com',
    role: 'tutor',
    first_name: 'Jane',
    last_name: 'Tutor',
  };

  const adminUser = {
    ...studentUser,
    id: 3,
    email: 'admin@example.com',
    role: 'admin',
    first_name: 'Admin',
    last_name: 'User',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (messages.getUnreadCount as jest.Mock).mockResolvedValue({ total: 0, by_sender: {} });
  });

  describe('Role-based navigation', () => {
    it('shows Dashboard link for students', () => {
      render(<Navbar user={studentUser} />);

      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    });

    it('shows Dashboard link for tutors', () => {
      render(<Navbar user={tutorUser} />);

      expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    });

    it('shows Admin Panel link for admins', () => {
      render(<Navbar user={adminUser} />);

      expect(screen.getByRole('link', { name: /admin panel/i })).toBeInTheDocument();
    });

    it('shows Saved Tutors button only for students', () => {
      render(<Navbar user={studentUser} />);

      expect(screen.getByRole('button', { name: /saved tutors/i })).toBeInTheDocument();
    });

    it('does not show Saved Tutors for tutors', () => {
      render(<Navbar user={tutorUser} />);

      expect(screen.queryByRole('button', { name: /saved tutors/i })).not.toBeInTheDocument();
    });
  });

  describe('User menu', () => {
    it('displays user email in dropdown', async () => {
      render(<Navbar user={studentUser} />);

      // Open dropdown
      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByText('student@example.com')).toBeInTheDocument();
      });
    });

    it('displays user role in dropdown', async () => {
      render(<Navbar user={studentUser} />);

      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByText('student')).toBeInTheDocument();
      });
    });

    it('shows logout option in dropdown', async () => {
      render(<Navbar user={studentUser} />);

      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
      });
    });

    it('shows Settings link in dropdown', async () => {
      render(<Navbar user={studentUser} />);

      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
      });
    });
  });

  describe('Messages', () => {
    it('shows messages link', () => {
      render(<Navbar user={studentUser} />);

      expect(screen.getByRole('link', { name: /messages/i })).toBeInTheDocument();
    });

    it('displays unread message count badge when there are unread messages', async () => {
      (messages.getUnreadCount as jest.Mock).mockResolvedValue({ total: 5, by_sender: {} });

      render(<Navbar user={studentUser} />);

      await waitFor(() => {
        expect(screen.getByText('5')).toBeInTheDocument();
      });
    });

    it('displays 99+ for large unread counts', async () => {
      (messages.getUnreadCount as jest.Mock).mockResolvedValue({ total: 150, by_sender: {} });

      render(<Navbar user={studentUser} />);

      await waitFor(() => {
        expect(screen.getByText('99+')).toBeInTheDocument();
      });
    });
  });

  describe('Theme toggle', () => {
    it('renders theme toggle button with proper aria attributes', () => {
      render(<Navbar user={studentUser} />);

      const themeButton = screen.getByRole('button', { name: /toggle theme/i });
      expect(themeButton).toBeInTheDocument();
      expect(themeButton).toHaveAttribute('aria-pressed');
    });
  });

  describe('Accessibility', () => {
    it('user menu has proper aria attributes', async () => {
      render(<Navbar user={studentUser} />);

      const menuButton = screen.getByRole('button', { name: /student/i });
      expect(menuButton).toHaveAttribute('aria-haspopup', 'menu');
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(menuButton);

      await waitFor(() => {
        expect(menuButton).toHaveAttribute('aria-expanded', 'true');
      });
    });

    it('mobile menu button has proper aria attributes', () => {
      render(<Navbar user={studentUser} />);

      const mobileMenuButton = screen.getByRole('button', { name: /open menu/i });
      expect(mobileMenuButton).toHaveAttribute('aria-expanded', 'false');
    });

    it('messages link has accessible label with unread count', async () => {
      (messages.getUnreadCount as jest.Mock).mockResolvedValue({ total: 3, by_sender: {} });

      render(<Navbar user={studentUser} />);

      await waitFor(() => {
        const messagesLink = screen.getByRole('link', { name: /messages \(3 unread\)/i });
        expect(messagesLink).toBeInTheDocument();
      });
    });
  });

  describe('Tutor-specific menu items', () => {
    it('shows My Profile link for tutors', async () => {
      render(<Navbar user={tutorUser} />);

      const avatarButton = screen.getByRole('button', { name: /tutor/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /my profile/i })).toBeInTheDocument();
      });
    });

    it('shows Share Profile button for tutors', async () => {
      render(<Navbar user={tutorUser} />);

      const avatarButton = screen.getByRole('button', { name: /tutor/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /share profile/i })).toBeInTheDocument();
      });
    });
  });

  describe('Student-specific menu items', () => {
    it('shows My Lessons link for students', async () => {
      render(<Navbar user={studentUser} />);

      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /my lessons/i })).toBeInTheDocument();
      });
    });

    it('shows Saved Tutors link in dropdown for students', async () => {
      render(<Navbar user={studentUser} />);

      const avatarButton = screen.getByRole('button', { name: /student/i });
      fireEvent.click(avatarButton);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /saved tutors/i })).toBeInTheDocument();
      });
    });
  });
});
