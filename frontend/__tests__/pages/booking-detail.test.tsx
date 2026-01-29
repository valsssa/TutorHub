/**
 * Page-level tests for Booking Detail page
 *
 * Tests for booking detail view including:
 * - Booking information display
 * - Status-based actions (confirm, cancel, reschedule)
 * - Meeting join functionality
 * - Review submission
 * - Error handling
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { auth, bookings, reviews, messages } from '@/lib/api';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockBack = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
    back: mockBack,
  }),
  usePathname: () => '/bookings/1',
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

// Mock user data
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

// Mock booking data for different states
const createMockBooking = (overrides = {}) => ({
  id: 1,
  tutor_profile_id: 1,
  student_id: 1,
  tutor_name: 'Dr. Sarah Johnson',
  student_name: 'John Doe',
  subject_id: 1,
  subject_name: 'Mathematics',
  start_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
  end_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
  topic: 'Calculus Integration',
  notes_student: 'I need help with integration by parts',
  notes_tutor: null,
  session_state: 'confirmed',
  session_outcome: 'pending',
  payment_state: 'authorized',
  dispute_state: 'none',
  hourly_rate: 75,
  total_amount: 75,
  meeting_url: 'https://zoom.us/j/123456789',
  tutor_earnings_cents: 6375,
  created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
  updated_at: new Date().toISOString(),
  ...overrides,
});

describe('Booking Detail Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
  });

  describe('Booking Information Display', () => {
    it('displays booking details correctly', async () => {
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(bookings.get).toHaveBeenCalledWith(1);
      });

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
        expect(screen.getByText('Mathematics')).toBeInTheDocument();
        expect(screen.getByText('Calculus Integration')).toBeInTheDocument();
        expect(screen.getByText(/\$75/)).toBeInTheDocument();
      });
    });

    it('displays booking status badge', async () => {
      const mockBooking = createMockBooking({ session_state: 'confirmed' });
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/confirmed/i)).toBeInTheDocument();
      });
    });

    it('shows student notes', async () => {
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText('I need help with integration by parts')).toBeInTheDocument();
      });
    });

    it('formats date and time correctly', async () => {
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        // Should show formatted date
        expect(screen.getByText(/\d{1,2}.*\d{4}|january|february|march/i)).toBeInTheDocument();
        // Should show time
        expect(screen.getByText(/\d{1,2}:\d{2}.*[AP]M/i)).toBeInTheDocument();
      });
    });
  });

  describe('Student Actions', () => {
    beforeEach(() => {
      (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    });

    it('shows cancel button for confirmed booking', async () => {
      const mockBooking = createMockBooking({ session_state: 'confirmed' });
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });
    });

    it('handles booking cancellation', async () => {
      const user = userEvent.setup();
      const mockBooking = createMockBooking({ session_state: 'confirmed' });

      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);
      (bookings.cancel as jest.Mock).mockResolvedValue({
        ...mockBooking,
        session_state: 'cancelled',
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Fill in reason in modal
      const reasonInput = await screen.findByLabelText(/reason/i);
      await user.type(reasonInput, 'Schedule conflict');

      const confirmButton = screen.getByRole('button', { name: /confirm.*cancel/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(bookings.cancel).toHaveBeenCalledWith(1, expect.objectContaining({
          reason: 'Schedule conflict',
        }));
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('shows reschedule button for confirmed booking', async () => {
      const mockBooking = createMockBooking({ session_state: 'confirmed' });
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /reschedule/i })).toBeInTheDocument();
      });
    });

    it('shows join button near session time', async () => {
      const nearBooking = createMockBooking({
        session_state: 'confirmed',
        start_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(), // 10 minutes from now
        meeting_url: 'https://zoom.us/j/123456789',
      });
      (bookings.get as jest.Mock).mockResolvedValue(nearBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /join/i })).toBeInTheDocument();
      });
    });

    it('hides join button for future sessions', async () => {
      const futureBooking = createMockBooking({
        session_state: 'confirmed',
        start_at: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(), // 2 days from now
      });
      (bookings.get as jest.Mock).mockResolvedValue(futureBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /join/i })).not.toBeInTheDocument();
      });
    });

    it('allows messaging tutor', async () => {
      const user = userEvent.setup();
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /message/i })).toBeInTheDocument();
      });

      const messageButton = screen.getByRole('button', { name: /message/i });
      await user.click(messageButton);

      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('messages'));
    });
  });

  describe('Tutor Actions', () => {
    beforeEach(() => {
      (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockTutorUser);
    });

    it('shows confirm button for pending booking', async () => {
      const pendingBooking = createMockBooking({
        session_state: 'pending_tutor',
        student_id: 1,
      });
      (bookings.get as jest.Mock).mockResolvedValue(pendingBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm|accept/i })).toBeInTheDocument();
      });
    });

    it('shows decline button for pending booking', async () => {
      const pendingBooking = createMockBooking({ session_state: 'pending_tutor' });
      (bookings.get as jest.Mock).mockResolvedValue(pendingBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /decline|reject/i })).toBeInTheDocument();
      });
    });

    it('handles booking confirmation', async () => {
      const user = userEvent.setup();
      const pendingBooking = createMockBooking({ session_state: 'pending_tutor' });

      (bookings.get as jest.Mock).mockResolvedValue(pendingBooking);
      (bookings.confirm as jest.Mock).mockResolvedValue({
        ...pendingBooking,
        session_state: 'confirmed',
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /confirm|accept/i })).toBeInTheDocument();
      });

      const confirmButton = screen.getByRole('button', { name: /confirm|accept/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(bookings.confirm).toHaveBeenCalledWith(1, undefined);
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('handles booking decline with reason', async () => {
      const user = userEvent.setup();
      const pendingBooking = createMockBooking({ session_state: 'pending_tutor' });

      (bookings.get as jest.Mock).mockResolvedValue(pendingBooking);
      (bookings.decline as jest.Mock).mockResolvedValue({
        ...pendingBooking,
        session_state: 'cancelled',
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /decline|reject/i })).toBeInTheDocument();
      });

      const declineButton = screen.getByRole('button', { name: /decline|reject/i });
      await user.click(declineButton);

      // Fill in reason in modal
      const reasonInput = await screen.findByLabelText(/reason/i);
      await user.type(reasonInput, 'Not available at this time');

      const confirmButton = screen.getByRole('button', { name: /confirm.*decline|submit/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(bookings.decline).toHaveBeenCalledWith(1, 'Not available at this time');
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('shows mark no-show button during session time', async () => {
      const inProgressBooking = createMockBooking({
        session_state: 'in_progress',
        start_at: new Date(Date.now() - 10 * 60 * 1000).toISOString(), // Started 10 min ago
      });
      (bookings.get as jest.Mock).mockResolvedValue(inProgressBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /no.*show/i })).toBeInTheDocument();
      });
    });
  });

  describe('Review Submission', () => {
    beforeEach(() => {
      (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockStudentUser);
    });

    it('shows review form for completed booking', async () => {
      const completedBooking = createMockBooking({
        session_state: 'completed',
        session_outcome: 'successful',
        has_review: false,
      });
      (bookings.get as jest.Mock).mockResolvedValue(completedBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/leave.*review|rate.*session/i)).toBeInTheDocument();
      });
    });

    it('submits review successfully', async () => {
      const user = userEvent.setup();
      const completedBooking = createMockBooking({
        session_state: 'completed',
        session_outcome: 'successful',
        has_review: false,
      });

      (bookings.get as jest.Mock).mockResolvedValue(completedBooking);
      (reviews.create as jest.Mock).mockResolvedValue({
        id: 1,
        booking_id: 1,
        rating: 5,
        comment: 'Great session!',
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/leave.*review|rate/i)).toBeInTheDocument();
      });

      // Click 5 stars
      const stars = screen.getAllByRole('button', { name: /star/i });
      await user.click(stars[4]); // 5th star

      // Add comment
      const commentInput = screen.getByLabelText(/comment|review/i);
      await user.type(commentInput, 'Great session!');

      // Submit
      const submitButton = screen.getByRole('button', { name: /submit.*review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(reviews.create).toHaveBeenCalledWith(1, 5, 'Great session!');
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('hides review form if already reviewed', async () => {
      const reviewedBooking = createMockBooking({
        session_state: 'completed',
        session_outcome: 'successful',
        has_review: true,
        review: { rating: 5, comment: 'Great!' },
      });
      (bookings.get as jest.Mock).mockResolvedValue(reviewedBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.queryByText(/leave.*review/i)).not.toBeInTheDocument();
        expect(screen.getByText(/your.*review/i)).toBeInTheDocument();
      });
    });
  });

  describe('Booking States', () => {
    it('displays cancelled state correctly', async () => {
      const cancelledBooking = createMockBooking({
        session_state: 'cancelled',
        cancellation_reason: 'Schedule conflict',
        cancelled_by: 'student',
      });
      (bookings.get as jest.Mock).mockResolvedValue(cancelledBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
        expect(screen.getByText('Schedule conflict')).toBeInTheDocument();
      });
    });

    it('displays expired state correctly', async () => {
      const expiredBooking = createMockBooking({
        session_state: 'expired',
      });
      (bookings.get as jest.Mock).mockResolvedValue(expiredBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/expired/i)).toBeInTheDocument();
      });
    });

    it('displays no-show state with appropriate message', async () => {
      const noShowBooking = createMockBooking({
        session_state: 'no_show',
        no_show_party: 'student',
      });
      (bookings.get as jest.Mock).mockResolvedValue(noShowBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/no.*show/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error when booking not found', async () => {
      (bookings.get as jest.Mock).mockRejectedValue({
        response: { status: 404, data: { detail: 'Booking not found' } },
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '999' }} />);

      await waitFor(() => {
        expect(screen.getByText(/not.*found|doesn't.*exist/i)).toBeInTheDocument();
      });
    });

    it('shows error when unauthorized to view booking', async () => {
      (bookings.get as jest.Mock).mockRejectedValue({
        response: { status: 403, data: { detail: 'Not authorized' } },
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByText(/unauthorized|not.*allowed/i)).toBeInTheDocument();
      });
    });

    it('handles action failure gracefully', async () => {
      const user = userEvent.setup();
      const mockBooking = createMockBooking({ session_state: 'confirmed' });

      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);
      (bookings.cancel as jest.Mock).mockRejectedValue({
        response: { data: { detail: 'Cannot cancel booking within 24 hours' } },
      });

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      const reasonInput = await screen.findByLabelText(/reason/i);
      await user.type(reasonInput, 'Test');

      const confirmButton = screen.getByRole('button', { name: /confirm.*cancel/i });
      await user.click(confirmButton);

      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalledWith(
          expect.stringContaining('Cannot cancel')
        );
      });
    });
  });

  describe('Navigation', () => {
    it('navigates back to bookings list', async () => {
      const user = userEvent.setup();
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument();
      });

      const backButton = screen.getByRole('button', { name: /back/i });
      await user.click(backButton);

      expect(mockBack).toHaveBeenCalled();
    });

    it('navigates to tutor profile', async () => {
      const mockBooking = createMockBooking();
      (bookings.get as jest.Mock).mockResolvedValue(mockBooking);

      const BookingDetailPage = (await import('@/app/bookings/[id]/page')).default;
      render(<BookingDetailPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(screen.getByRole('link', { name: /view.*profile/i })).toBeInTheDocument();
      });

      const profileLink = screen.getByRole('link', { name: /view.*profile/i });
      expect(profileLink).toHaveAttribute('href', expect.stringContaining('tutor'));
    });
  });
});
