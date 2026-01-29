/**
 * Tests for BookingCardStudent component
 * Revenue critical: Tests booking display and action buttons
 */

import { render, screen, fireEvent } from '@testing-library/react';
import BookingCardStudent from '@/components/bookings/BookingCardStudent';
import { BookingDTO } from '@/types/booking';

// Mock dependencies
jest.mock('@/contexts/TimezoneContext', () => ({
  useTimezone: () => ({ userTimezone: 'UTC' }),
}));

jest.mock('@/components/TimeDisplay', () => ({
  __esModule: true,
  default: ({ date }: { date: string }) => <span data-testid="time-display">{date}</span>,
}));

// Mock bookingUtils with all required exports
jest.mock('@/lib/bookingUtils', () => ({
  BOOKING_STATUS_COLORS: { pending: 'bg-yellow-100' },
  LESSON_TYPE_BADGES: { regular: 'bg-blue-100', package: 'bg-purple-100' },
  SESSION_STATE_COLORS: {
    REQUESTED: 'bg-yellow-100',
    SCHEDULED: 'bg-blue-100',
    ACTIVE: 'bg-green-100',
    ENDED: 'bg-gray-100',
    CANCELLED: 'bg-red-100',
  },
  DISPUTE_STATE_COLORS: {
    NONE: '',
    FILED: 'bg-orange-100',
    UNDER_REVIEW: 'bg-yellow-100',
  },
  calculateBookingTiming: () => ({
    startDate: new Date('2025-02-01T10:00:00Z'),
    endDate: new Date('2025-02-01T11:00:00Z'),
    duration: 60,
    hoursUntil: 24,
    canCancelFree: true,
  }),
  formatBookingPrice: (cents: number) => `$${(cents / 100).toFixed(2)}`,
  getDisplayTimezone: () => 'UTC',
  getSessionStateLabel: (state: string) => state,
  getSessionOutcomeLabel: (outcome: string) => outcome,
  getDisputeStateLabel: (state: string) => state,
  isUpcomingBooking: (state: string) => ['REQUESTED', 'SCHEDULED'].includes(state),
  isCancellableBooking: (state: string) => ['REQUESTED', 'SCHEDULED'].includes(state),
  hasOpenDispute: (state: string) => ['FILED', 'UNDER_REVIEW'].includes(state),
}));

describe('BookingCardStudent', () => {
  const baseBooking: BookingDTO = {
    id: 1,
    tutor_profile_id: 1,
    student_id: 1,
    subject_id: 1,
    start_at: '2025-02-01T10:00:00Z',
    end_at: '2025-02-01T11:00:00Z',
    topic: 'Calculus Help',
    notes_student: 'Need help with integration',
    notes_tutor: 'Prepare examples',
    rate_cents: 5000,
    currency: 'USD',
    status: 'pending',
    session_state: 'SCHEDULED',
    session_outcome: null,
    payment_state: 'AUTHORIZED',
    dispute_state: 'NONE',
    lesson_type: 'regular',
    subject_name: 'Mathematics',
    tutor: {
      id: 1,
      name: 'John Tutor',
      title: 'Math Expert',
      avatar_url: null,
      rating_avg: 4.8,
    },
    tutor_tz: 'America/New_York',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Tutor information display', () => {
    it('displays tutor name', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByRole('heading', { name: 'John Tutor' })).toBeInTheDocument();
    });

    it('displays tutor title', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText('Math Expert')).toBeInTheDocument();
    });

    it('displays tutor rating', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText('4.8')).toBeInTheDocument();
    });

    it('displays fallback icon when no avatar', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      // Should have a user icon when no avatar
      const avatarContainer = document.querySelector('.rounded-full');
      expect(avatarContainer).toBeInTheDocument();
    });

    it('displays tutor avatar when provided', () => {
      const bookingWithAvatar = {
        ...baseBooking,
        tutor: { ...baseBooking.tutor, avatar_url: 'https://example.com/avatar.jpg' },
      };

      render(<BookingCardStudent booking={bookingWithAvatar} />);

      const img = screen.getByAltText('John Tutor');
      expect(img).toHaveAttribute('src', 'https://example.com/avatar.jpg');
    });
  });

  describe('Booking details display', () => {
    it('displays price', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText('$50.00')).toBeInTheDocument();
      expect(screen.getByText('USD')).toBeInTheDocument();
    });

    it('displays subject name', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText(/mathematics/i)).toBeInTheDocument();
    });

    it('displays student notes', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText(/need help with integration/i)).toBeInTheDocument();
    });

    it('displays tutor notes', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText(/prepare examples/i)).toBeInTheDocument();
    });

    it('displays lesson type badge', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText('regular')).toBeInTheDocument();
    });
  });

  describe('Status badges', () => {
    it('displays session state badge', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText('SCHEDULED')).toBeInTheDocument();
    });

    it('displays session outcome when present', () => {
      const completedBooking = {
        ...baseBooking,
        session_state: 'ENDED',
        session_outcome: 'COMPLETED',
      };

      render(<BookingCardStudent booking={completedBooking} />);

      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });

    it('displays dispute badge when dispute exists', () => {
      const disputedBooking = {
        ...baseBooking,
        dispute_state: 'FILED',
      };

      render(<BookingCardStudent booking={disputedBooking} />);

      expect(screen.getByText('FILED')).toBeInTheDocument();
    });
  });

  describe('Action buttons', () => {
    it('shows cancel button for cancellable bookings', () => {
      const mockOnCancel = jest.fn();
      render(<BookingCardStudent booking={baseBooking} onCancel={mockOnCancel} />);

      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('calls onCancel when cancel button clicked', () => {
      const mockOnCancel = jest.fn();
      render(<BookingCardStudent booking={baseBooking} onCancel={mockOnCancel} />);

      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
      expect(mockOnCancel).toHaveBeenCalledWith(1);
    });

    it('shows reschedule button for upcoming bookings', () => {
      const mockOnReschedule = jest.fn();
      render(<BookingCardStudent booking={baseBooking} onReschedule={mockOnReschedule} />);

      expect(screen.getByRole('button', { name: /reschedule/i })).toBeInTheDocument();
    });

    it('calls onReschedule when clicked', () => {
      const mockOnReschedule = jest.fn();
      render(<BookingCardStudent booking={baseBooking} onReschedule={mockOnReschedule} />);

      fireEvent.click(screen.getByRole('button', { name: /reschedule/i }));
      expect(mockOnReschedule).toHaveBeenCalledWith(1);
    });

    it('shows open dispute button for ended sessions without dispute', () => {
      const mockOnDispute = jest.fn();
      const endedBooking = {
        ...baseBooking,
        session_state: 'ENDED',
        dispute_state: 'NONE',
      };

      render(<BookingCardStudent booking={endedBooking} onDispute={mockOnDispute} />);

      expect(screen.getByRole('button', { name: /open dispute/i })).toBeInTheDocument();
    });
  });

  describe('Policy hints', () => {
    it('shows free cancellation message when applicable', () => {
      render(<BookingCardStudent booking={baseBooking} />);

      expect(screen.getByText(/free cancellation available/i)).toBeInTheDocument();
    });
  });
});
