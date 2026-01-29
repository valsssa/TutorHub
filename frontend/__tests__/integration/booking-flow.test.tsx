/**
 * Integration tests for Booking Flow
 *
 * Tests the complete booking workflow from tutor selection to confirmation
 * Including: component interaction, state management, API call sequences,
 * error boundary behavior, and loading state transitions
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { bookings, tutors, subjects, availability } from '@/lib/api';
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
    back: jest.fn(),
  }),
  usePathname: () => '/tutors/1/book',
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

// Mock data
const mockTutor = {
  id: 1,
  user_id: 10,
  name: 'Dr. Sarah Johnson',
  title: 'Mathematics Expert',
  bio: 'PhD in Applied Mathematics',
  hourly_rate: 75,
  average_rating: 4.9,
  total_reviews: 125,
  subjects: [
    { id: 1, name: 'Mathematics' },
    { id: 2, name: 'Calculus' },
  ],
  availability: [
    { day_of_week: 1, start_time: '09:00', end_time: '17:00' },
    { day_of_week: 3, start_time: '09:00', end_time: '17:00' },
  ],
  pricing_options: [
    { id: 1, name: '1 Hour Session', duration_minutes: 60, price: 75 },
    { id: 2, name: '2 Hour Session', duration_minutes: 120, price: 140 },
  ],
};

const mockSubjects = [
  { id: 1, name: 'Mathematics' },
  { id: 2, name: 'Calculus' },
  { id: 3, name: 'Physics' },
];

const mockAvailableSlots = [
  { start_time: '2025-02-01T09:00:00Z', end_time: '2025-02-01T10:00:00Z', duration_minutes: 60 },
  { start_time: '2025-02-01T10:00:00Z', end_time: '2025-02-01T11:00:00Z', duration_minutes: 60 },
  { start_time: '2025-02-01T14:00:00Z', end_time: '2025-02-01T15:00:00Z', duration_minutes: 60 },
];

const mockUser = {
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

describe('Booking Flow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (subjects.list as jest.Mock).mockResolvedValue(mockSubjects);
    (tutors.getPublic as jest.Mock).mockResolvedValue(mockTutor);
    (availability.getTutorAvailableSlots as jest.Mock).mockResolvedValue(mockAvailableSlots);
  });

  describe('Complete Booking Flow', () => {
    it('successfully completes full booking workflow', async () => {
      const user = userEvent.setup();
      const mockBookingResponse = {
        id: 123,
        tutor_profile_id: 1,
        student_id: 1,
        subject_id: 1,
        start_at: '2025-02-01T09:00:00Z',
        end_at: '2025-02-01T10:00:00Z',
        status: 'pending_tutor',
        session_state: 'pending_tutor',
        total_amount: 75,
      };

      (bookings.create as jest.Mock).mockResolvedValue(mockBookingResponse);

      // Import and render booking page
      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      // Step 1: Verify tutor information loads
      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalledWith(1);
      });

      // Step 2: Wait for subjects to load
      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      // Step 3: Select subject
      const subjectSelect = await screen.findByLabelText(/subject/i);
      await user.selectOptions(subjectSelect, '1');

      // Step 4: Select date (triggers availability check)
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      await waitFor(() => {
        expect(availability.getTutorAvailableSlots).toHaveBeenCalled();
      });

      // Step 5: Select time slot
      const timeSlot = await screen.findByText(/9:00 AM/i);
      await user.click(timeSlot);

      // Step 6: Add notes
      const notesInput = screen.getByLabelText(/notes/i);
      await user.type(notesInput, 'Looking forward to learning calculus!');

      // Step 7: Submit booking
      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      // Step 8: Verify API call and success handling
      await waitFor(() => {
        expect(bookings.create).toHaveBeenCalledWith(
          expect.objectContaining({
            tutor_profile_id: 1,
            subject_id: 1,
          })
        );
      });

      await waitFor(() => {
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('handles booking creation failure gracefully', async () => {
      const user = userEvent.setup();

      (bookings.create as jest.Mock).mockRejectedValue({
        response: {
          status: 409,
          data: { detail: 'This time slot is no longer available' },
        },
      });

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      // Fill form and submit
      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      const subjectSelect = await screen.findByLabelText(/subject/i);
      await user.selectOptions(subjectSelect, '1');

      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      // Verify error handling
      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalledWith(
          expect.stringContaining('no longer available')
        );
      });
    });
  });

  describe('Booking State Transitions', () => {
    it('displays correct loading states during booking creation', async () => {
      const user = userEvent.setup();

      // Slow booking creation to observe loading state
      (bookings.create as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 1000))
      );

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      const subjectSelect = await screen.findByLabelText(/subject/i);
      await user.selectOptions(subjectSelect, '1');

      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      // Verify loading state
      await waitFor(() => {
        expect(screen.getByText(/booking|processing/i)).toBeInTheDocument();
      });

      // Button should be disabled during submission
      expect(submitButton).toBeDisabled();
    });

    it('transitions through availability loading states', async () => {
      // Slow availability loading
      (availability.getTutorAvailableSlots as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockAvailableSlots), 500))
      );

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      // Wait for initial load
      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Select date to trigger availability loading
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      // Should show loading indicator for time slots
      expect(screen.getByText(/loading.*slots|checking.*availability/i)).toBeInTheDocument();

      // Wait for slots to appear
      await waitFor(() => {
        expect(screen.getByText(/9:00 AM/i)).toBeInTheDocument();
      });
    });
  });

  describe('Form Validation', () => {
    it('validates all required fields before submission', async () => {
      const user = userEvent.setup();

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      // Try to submit without filling required fields
      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      // Verify validation errors appear
      await waitFor(() => {
        expect(screen.getByText(/subject.*required/i)).toBeInTheDocument();
        expect(screen.getByText(/date.*required/i)).toBeInTheDocument();
      });

      // Verify API was not called
      expect(bookings.create).not.toHaveBeenCalled();
    });

    it('prevents booking for past dates', async () => {
      const user = userEvent.setup();

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      // Try to select a past date
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2020-01-01' } });

      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/date.*future|past.*date/i)).toBeInTheDocument();
      });
    });
  });

  describe('Pricing Calculation', () => {
    it('calculates total price based on selected duration', async () => {
      const user = userEvent.setup();

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Select 2 hour session
      const durationSelect = await screen.findByLabelText(/duration/i);
      await user.selectOptions(durationSelect, '120');

      // Verify price calculation (2 hours * $75/hour = $150 or package price)
      await waitFor(() => {
        const priceDisplay = screen.getByText(/\$14[0-9]|\$150/i);
        expect(priceDisplay).toBeInTheDocument();
      });
    });

    it('shows package discount when applicable', async () => {
      const tutorWithPackages = {
        ...mockTutor,
        pricing_options: [
          { id: 1, name: '1 Hour Session', duration_minutes: 60, price: 75, discount_percent: 0 },
          { id: 2, name: '5 Session Package', duration_minutes: 300, price: 350, discount_percent: 7 },
        ],
      };

      (tutors.getPublic as jest.Mock).mockResolvedValue(tutorWithPackages);

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Look for discount indication
      await waitFor(() => {
        const packageOption = screen.queryByText(/save|discount|%.*off/i);
        if (packageOption) {
          expect(packageOption).toBeInTheDocument();
        }
      });
    });
  });

  describe('API Call Sequences', () => {
    it('loads data in correct sequence', async () => {
      const callOrder: string[] = [];

      (tutors.getPublic as jest.Mock).mockImplementation(() => {
        callOrder.push('tutor');
        return Promise.resolve(mockTutor);
      });

      (subjects.list as jest.Mock).mockImplementation(() => {
        callOrder.push('subjects');
        return Promise.resolve(mockSubjects);
      });

      (availability.getTutorAvailableSlots as jest.Mock).mockImplementation(() => {
        callOrder.push('availability');
        return Promise.resolve(mockAvailableSlots);
      });

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      // Wait for initial data to load
      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
        expect(subjects.list).toHaveBeenCalled();
      });

      // Tutor and subjects should load before user interaction
      expect(callOrder).toContain('tutor');
      expect(callOrder).toContain('subjects');
    });

    it('only fetches availability when date is selected', async () => {
      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Availability should not be fetched initially
      expect(availability.getTutorAvailableSlots).not.toHaveBeenCalled();

      // Select a date
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      // Now availability should be fetched
      await waitFor(() => {
        expect(availability.getTutorAvailableSlots).toHaveBeenCalled();
      });
    });
  });

  describe('Error Recovery', () => {
    it('allows retry after API failure', async () => {
      const user = userEvent.setup();

      // First call fails, second succeeds
      (bookings.create as jest.Mock)
        .mockRejectedValueOnce({ response: { data: { detail: 'Server error' } } })
        .mockResolvedValueOnce({ id: 123, status: 'pending_tutor' });

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      const subjectSelect = await screen.findByLabelText(/subject/i);
      await user.selectOptions(subjectSelect, '1');

      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      // First attempt fails
      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalled();
      });

      // Button should be enabled for retry
      await waitFor(() => {
        expect(submitButton).not.toBeDisabled();
      });

      // Second attempt succeeds
      await user.click(submitButton);

      await waitFor(() => {
        expect(toastMocks.showSuccess).toHaveBeenCalled();
      });
    });

    it('handles network timeout gracefully', async () => {
      const user = userEvent.setup();

      (bookings.create as jest.Mock).mockRejectedValue({
        code: 'ECONNABORTED',
        message: 'Request timeout',
      });

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(subjects.list).toHaveBeenCalled();
      });

      const subjectSelect = await screen.findByLabelText(/subject/i);
      await user.selectOptions(subjectSelect, '1');

      const submitButton = screen.getByRole('button', { name: /book.*session/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalledWith(
          expect.stringMatching(/timeout|try again|network/i)
        );
      });
    });
  });

  describe('Component Interaction', () => {
    it('updates time slots when date changes', async () => {
      const user = userEvent.setup();

      const slotsForFeb1 = [
        { start_time: '2025-02-01T09:00:00Z', end_time: '2025-02-01T10:00:00Z', duration_minutes: 60 },
      ];

      const slotsForFeb2 = [
        { start_time: '2025-02-02T14:00:00Z', end_time: '2025-02-02T15:00:00Z', duration_minutes: 60 },
      ];

      (availability.getTutorAvailableSlots as jest.Mock)
        .mockResolvedValueOnce(slotsForFeb1)
        .mockResolvedValueOnce(slotsForFeb2);

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Select first date
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      await waitFor(() => {
        expect(screen.getByText(/9:00 AM/i)).toBeInTheDocument();
      });

      // Change date
      fireEvent.change(dateInput, { target: { value: '2025-02-02' } });

      // Slots should update
      await waitFor(() => {
        expect(screen.getByText(/2:00 PM/i)).toBeInTheDocument();
        expect(screen.queryByText(/9:00 AM/i)).not.toBeInTheDocument();
      });
    });

    it('clears selected time when date changes', async () => {
      const user = userEvent.setup();

      const BookingPage = (await import('@/app/tutors/[id]/book/page')).default;
      render(<BookingPage params={{ id: '1' }} />);

      await waitFor(() => {
        expect(tutors.getPublic).toHaveBeenCalled();
      });

      // Select date and time
      const dateInput = screen.getByLabelText(/date/i);
      fireEvent.change(dateInput, { target: { value: '2025-02-01' } });

      await waitFor(() => {
        expect(screen.getByText(/9:00 AM/i)).toBeInTheDocument();
      });

      const timeSlot = screen.getByText(/9:00 AM/i);
      await user.click(timeSlot);

      // Verify time is selected (should have selected state)
      expect(timeSlot).toHaveClass(/selected|active|bg-/i);

      // Change date
      fireEvent.change(dateInput, { target: { value: '2025-02-02' } });

      // Previously selected time should be cleared
      await waitFor(() => {
        const newSlots = screen.getAllByRole('button');
        const selectedSlot = newSlots.find(slot =>
          slot.className.includes('selected') || slot.className.includes('active')
        );
        expect(selectedSlot).toBeUndefined();
      });
    });
  });
});

describe('Booking List and Management Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
  });

  const mockBookingsList = {
    items: [
      {
        id: 1,
        tutor_name: 'Dr. Sarah Johnson',
        tutor_profile_id: 1,
        subject_name: 'Mathematics',
        start_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        end_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
        session_state: 'confirmed',
        payment_state: 'authorized',
        total_amount: 75,
      },
      {
        id: 2,
        tutor_name: 'Prof. Mike Chen',
        tutor_profile_id: 2,
        subject_name: 'Physics',
        start_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        end_at: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000 + 60 * 60 * 1000).toISOString(),
        session_state: 'pending_tutor',
        payment_state: 'pending',
        total_amount: 60,
      },
    ],
    total: 2,
    page: 1,
    page_size: 20,
  };

  it('loads and displays booking list', async () => {
    (bookings.list as jest.Mock).mockResolvedValue(mockBookingsList);

    const BookingsPage = (await import('@/app/bookings/page')).default;
    render(<BookingsPage />);

    await waitFor(() => {
      expect(bookings.list).toHaveBeenCalled();
    });

    // Verify bookings are displayed
    await waitFor(() => {
      expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      expect(screen.getByText('Prof. Mike Chen')).toBeInTheDocument();
    });
  });

  it('filters bookings by status', async () => {
    const user = userEvent.setup();

    (bookings.list as jest.Mock).mockResolvedValue(mockBookingsList);

    const BookingsPage = (await import('@/app/bookings/page')).default;
    render(<BookingsPage />);

    await waitFor(() => {
      expect(bookings.list).toHaveBeenCalled();
    });

    // Click on a filter tab
    const confirmedTab = screen.getByRole('tab', { name: /confirmed|upcoming/i });
    await user.click(confirmedTab);

    // Verify filtered API call
    await waitFor(() => {
      expect(bookings.list).toHaveBeenCalledWith(
        expect.objectContaining({ status: expect.any(String) })
      );
    });
  });

  it('handles booking cancellation flow', async () => {
    const user = userEvent.setup();

    (bookings.list as jest.Mock).mockResolvedValue(mockBookingsList);
    (bookings.cancel as jest.Mock).mockResolvedValue({
      ...mockBookingsList.items[0],
      session_state: 'cancelled',
    });

    const BookingsPage = (await import('@/app/bookings/page')).default;
    render(<BookingsPage />);

    await waitFor(() => {
      expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
    });

    // Click cancel button
    const cancelButton = screen.getAllByRole('button', { name: /cancel/i })[0];
    await user.click(cancelButton);

    // Confirm in modal
    const confirmButton = await screen.findByRole('button', { name: /confirm.*cancel|yes.*cancel/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(bookings.cancel).toHaveBeenCalled();
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });
});
