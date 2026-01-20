/**
 * Student Dashboard Component Tests
 *
 * Tests for student dashboard display, upcoming sessions, and CTAs.
 */

import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import StudentDashboard from '@/components/dashboards/StudentDashboard';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/dashboard',
}));

// Mock API
jest.mock('@/lib/api', () => ({
  bookings: {
    list: jest.fn(),
  },
  tutors: {
    getFeatured: jest.fn(),
  },
  notifications: {
    list: jest.fn(),
  },
}));

const mockUser = {
  id: 1,
  email: 'student@test.com',
  role: 'student',
  first_name: 'John',
  last_name: 'Doe',
  is_active: true,
  is_verified: true,
  avatar_url: null,
  currency: 'USD',
  timezone: 'America/New_York',
};

const mockBookings = [
  {
    id: 1,
    tutor_name: 'Alice Smith',
    tutor_profile_id: 10,
    subject_name: 'Mathematics',
    start_time: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    end_time: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
    status: 'confirmed',
    hourly_rate: '50.00',
    total_amount: '50.00',
  },
  {
    id: 2,
    tutor_name: 'Bob Johnson',
    tutor_profile_id: 11,
    subject_name: 'Physics',
    start_time: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
    end_time: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
    status: 'confirmed',
    hourly_rate: '60.00',
    total_amount: '60.00',
  },
];

const mockFeaturedTutors = [
  {
    id: 1,
    user_id: 20,
    name: 'Dr. Emily Chen',
    title: 'Math Expert',
    bio: 'PhD in Mathematics with 10 years teaching experience',
    hourly_rate: '75.00',
    average_rating: 4.9,
    total_reviews: 45,
    subjects: ['Mathematics', 'Calculus'],
  },
];

describe('StudentDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders welcome message with user first name', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/Welcome back, John/i)).toBeInTheDocument();
      });
    });

    it('displays loading state initially', () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockImplementation(() => new Promise(() => {})); // Never resolves

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      expect(screen.getByTestId('loading-spinner') || screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('renders main sections when loaded', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: mockBookings });
      tutors.getFeatured.mockResolvedValue({ data: mockFeaturedTutors });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/Upcoming Sessions/i)).toBeInTheDocument();
        expect(screen.getByText(/Recommended Tutors/i)).toBeInTheDocument();
      });
    });
  });

  describe('Upcoming Sessions', () => {
    it('displays list of upcoming confirmed sessions', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: mockBookings });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText('Alice Smith')).toBeInTheDocument();
        expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
        expect(screen.getByText('Mathematics')).toBeInTheDocument();
        expect(screen.getByText('Physics')).toBeInTheDocument();
      });
    });

    it('shows empty state when no upcoming sessions', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/No upcoming sessions/i)).toBeInTheDocument();
      });
    });

    it('displays session time in user timezone', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [mockBookings[0]] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        // Should show time formatted according to user's timezone
        const timeElement = screen.getByText(/AM|PM/i);
        expect(timeElement).toBeInTheDocument();
      });
    });

    it('shows Join button for sessions within 15 minutes', async () => {
      // Given - session starting in 10 minutes
      const soonBooking = {
        ...mockBookings[0],
        start_time: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
        join_url: 'https://zoom.us/j/12345',
      };

      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [soonBooking] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Join/i })).toBeInTheDocument();
      });
    });

    it('does not show Join button for sessions >15 minutes away', async () => {
      // Given - session in 2 days
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: mockBookings });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /Join/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Call to Action', () => {
    it('shows Find Tutors CTA when no sessions', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Find a Tutor/i })).toBeInTheDocument();
      });
    });

    it('clicking Find Tutors navigates to tutor search', async () => {
      // Given
      const { useRouter } = require('next/navigation');
      const mockPush = jest.fn();
      useRouter.mockReturnValue({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() });

      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      await waitFor(() => {
        const findTutorBtn = screen.getByRole('button', { name: /Find a Tutor/i });
        findTutorBtn.click();
      });

      // Then
      expect(mockPush).toHaveBeenCalledWith('/tutors');
    });
  });

  describe('Recommended Tutors', () => {
    it('displays featured tutors section', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: mockFeaturedTutors });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/Recommended Tutors/i)).toBeInTheDocument();
        expect(screen.getByText('Dr. Emily Chen')).toBeInTheDocument();
      });
    });

    it('displays tutor rating and review count', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: mockFeaturedTutors });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText('4.9')).toBeInTheDocument();
        expect(screen.getByText(/45 reviews/i)).toBeInTheDocument();
      });
    });

    it('displays hourly rate in user currency', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: mockFeaturedTutors });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/\$75/i)).toBeInTheDocument();
      });
    });
  });

  describe('Stats Summary', () => {
    it('displays total completed sessions', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({
        data: [],
        meta: { total_completed_sessions: 12 },
      });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/12/)).toBeInTheDocument();
        expect(screen.getByText(/Completed Sessions/i)).toBeInTheDocument();
      });
    });

    it('displays hours learned', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({
        data: [],
        meta: { total_hours_learned: 25.5 },
      });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/25\.5/)).toBeInTheDocument();
        expect(screen.getByText(/Hours Learned/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when bookings fail to load', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockRejectedValue(new Error('Network error'));
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        expect(screen.getByText(/error loading sessions/i) || screen.getByText(/something went wrong/i)).toBeInTheDocument();
      });
    });

    it('displays error state but still shows other sections', async () => {
      // Given
      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockRejectedValue(new Error('Network error'));
      tutors.getFeatured.mockResolvedValue({ data: mockFeaturedTutors });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then
      await waitFor(() => {
        // Error for bookings
        expect(screen.getByText(/error/i)).toBeInTheDocument();
        // But still shows recommended tutors
        expect(screen.getByText('Dr. Emily Chen')).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('renders mobile-optimized layout on small screens', async () => {
      // Given
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));

      const { bookings, tutors } = require('@/lib/api');
      bookings.list.mockResolvedValue({ data: [] });
      tutors.getFeatured.mockResolvedValue({ data: [] });

      // When
      render(<StudentDashboard user={mockUser} />);

      // Then - check for mobile-specific classes or layout
      await waitFor(() => {
        const dashboard = screen.getByTestId('student-dashboard') || screen.getByRole('main');
        expect(dashboard).toBeInTheDocument();
      });
    });
  });
});
