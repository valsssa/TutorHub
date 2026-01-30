/**
 * Tests for BookingSuccess component
 * Tests booking confirmation modal functionality
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BookingSuccess from '@/components/BookingSuccess';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
}));

// Mock clipboard API
const mockWriteText = jest.fn();
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText,
  },
});

// Mock URL.createObjectURL and URL.revokeObjectURL
const mockCreateObjectURL = jest.fn(() => 'blob:test-url');
const mockRevokeObjectURL = jest.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

describe('BookingSuccess', () => {
  const mockOnClose = jest.fn();
  const mockOnViewBookings = jest.fn();
  const mockOnBookAnother = jest.fn();

  const defaultBooking = {
    bookingId: 12345,
    tutorName: 'John Smith',
    tutorAvatar: '/avatars/john.jpg',
    subject: 'Mathematics',
    date: new Date('2025-02-15T14:00:00'),
    duration: 60,
    price: 50,
    currency: 'USD',
  };

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    booking: defaultBooking,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockWriteText.mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('does not render when closed', () => {
      const { container } = render(
        <BookingSuccess {...defaultProps} isOpen={false} />
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders when open', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Booking Confirmed!')).toBeInTheDocument();
    });

    it('displays booking reference with booking ID', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Booking Reference')).toBeInTheDocument();
      expect(screen.getByText('#12345')).toBeInTheDocument();
    });

    it('displays tutor name', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Tutor')).toBeInTheDocument();
      expect(screen.getByText('John Smith')).toBeInTheDocument();
    });

    it('displays subject', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Subject')).toBeInTheDocument();
      expect(screen.getByText('Mathematics')).toBeInTheDocument();
    });

    it('displays formatted date and time', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Date & Time')).toBeInTheDocument();
      // Check for the date format - adjusting for locale differences
      expect(screen.getByText(/February 15, 2025/i)).toBeInTheDocument();
      // Check for duration
      expect(screen.getByText(/60 min/i)).toBeInTheDocument();
    });

    it('displays formatted price', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('Total Paid')).toBeInTheDocument();
      expect(screen.getByText('$50.00')).toBeInTheDocument();
    });

    it('displays different currency when specified', () => {
      const euroBooking = { ...defaultBooking, currency: 'EUR', price: 45 };
      render(<BookingSuccess {...defaultProps} booking={euroBooking} />);

      // EUR format may vary by locale, check for the value
      expect(screen.getByText(/45/)).toBeInTheDocument();
    });

    it('displays what happens next section', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByText('What happens next?')).toBeInTheDocument();
      expect(screen.getByText(/confirmation email has been sent/i)).toBeInTheDocument();
      expect(screen.getByText(/meeting link 15 minutes before/i)).toBeInTheDocument();
      expect(screen.getByText(/reschedule or cancel for free/i)).toBeInTheDocument();
    });

    it('displays success icon', () => {
      const { container } = render(<BookingSuccess {...defaultProps} />);

      // Check for the green success icon wrapper
      const iconWrapper = container.querySelector('.bg-emerald-100');
      expect(iconWrapper).toBeInTheDocument();
    });
  });

  describe('Copy Booking ID Functionality', () => {
    it('has copy button with proper aria-label', () => {
      render(<BookingSuccess {...defaultProps} />);

      const copyButton = screen.getByRole('button', { name: /copy booking id/i });
      expect(copyButton).toBeInTheDocument();
    });

    it('copies booking ID to clipboard when copy button clicked', async () => {
      const user = userEvent.setup();
      render(<BookingSuccess {...defaultProps} />);

      const copyButton = screen.getByRole('button', { name: /copy booking id/i });
      await user.click(copyButton);

      expect(mockWriteText).toHaveBeenCalledWith('12345');
    });

    it('shows check icon after copying', async () => {
      const user = userEvent.setup();
      const { container } = render(<BookingSuccess {...defaultProps} />);

      const copyButton = screen.getByRole('button', { name: /copy booking id/i });
      await user.click(copyButton);

      // Check icon should be visible after copy
      await waitFor(() => {
        const checkIcon = container.querySelector('.text-emerald-500');
        expect(checkIcon).toBeInTheDocument();
      });
    });

    it('handles clipboard API failure gracefully', async () => {
      mockWriteText.mockRejectedValueOnce(new Error('Clipboard failed'));

      // Mock execCommand for fallback
      const mockExecCommand = jest.fn(() => true);
      document.execCommand = mockExecCommand;

      const user = userEvent.setup();
      render(<BookingSuccess {...defaultProps} />);

      const copyButton = screen.getByRole('button', { name: /copy booking id/i });
      await user.click(copyButton);

      // Should use fallback method
      expect(mockExecCommand).toHaveBeenCalledWith('copy');
    });

    it('handles string booking ID', async () => {
      const user = userEvent.setup();
      const stringIdBooking = { ...defaultBooking, bookingId: 'ABC-123' };
      render(<BookingSuccess {...defaultProps} booking={stringIdBooking} />);

      expect(screen.getByText('#ABC-123')).toBeInTheDocument();

      const copyButton = screen.getByRole('button', { name: /copy booking id/i });
      await user.click(copyButton);

      expect(mockWriteText).toHaveBeenCalledWith('ABC-123');
    });
  });

  describe('Add to Calendar Functionality', () => {
    it('has add to calendar button', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByRole('button', { name: /add to calendar/i })).toBeInTheDocument();
    });

    it('generates ICS file when add to calendar clicked', async () => {
      const user = userEvent.setup();

      // Mock link click
      const mockClick = jest.fn();
      const mockAppendChild = jest.spyOn(document.body, 'appendChild');
      const mockRemoveChild = jest.spyOn(document.body, 'removeChild');

      render(<BookingSuccess {...defaultProps} />);

      const calendarButton = screen.getByRole('button', { name: /add to calendar/i });
      await user.click(calendarButton);

      // Should create blob URL
      expect(mockCreateObjectURL).toHaveBeenCalled();

      // Should clean up
      expect(mockRevokeObjectURL).toHaveBeenCalled();

      mockAppendChild.mockRestore();
      mockRemoveChild.mockRestore();
    });
  });

  describe('Navigation Actions', () => {
    it('calls onViewBookings when provided and View My Bookings clicked', async () => {
      const user = userEvent.setup();
      render(
        <BookingSuccess
          {...defaultProps}
          onViewBookings={mockOnViewBookings}
        />
      );

      const viewButton = screen.getByRole('button', { name: /view my bookings/i });
      await user.click(viewButton);

      expect(mockOnViewBookings).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('navigates to /bookings when View My Bookings clicked without custom handler', async () => {
      const user = userEvent.setup();
      render(<BookingSuccess {...defaultProps} />);

      const viewButton = screen.getByRole('button', { name: /view my bookings/i });
      await user.click(viewButton);

      expect(mockPush).toHaveBeenCalledWith('/bookings');
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('calls onBookAnother when provided and Book Another Lesson clicked', async () => {
      const user = userEvent.setup();
      render(
        <BookingSuccess
          {...defaultProps}
          onBookAnother={mockOnBookAnother}
        />
      );

      const bookAnotherButton = screen.getByRole('button', { name: /book another lesson/i });
      await user.click(bookAnotherButton);

      expect(mockOnBookAnother).toHaveBeenCalled();
      expect(mockOnClose).toHaveBeenCalled();
    });

    it('navigates to /tutors when Book Another Lesson clicked without custom handler', async () => {
      const user = userEvent.setup();
      render(<BookingSuccess {...defaultProps} />);

      const bookAnotherButton = screen.getByRole('button', { name: /book another lesson/i });
      await user.click(bookAnotherButton);

      expect(mockPush).toHaveBeenCalledWith('/tutors');
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Modal Behavior', () => {
    it('displays modal title', () => {
      render(<BookingSuccess {...defaultProps} />);

      // The Modal component receives "Booking Confirmed!" as title
      expect(screen.getByText('Booking Confirmed!')).toBeInTheDocument();
    });

    it('has footer with action buttons', () => {
      render(<BookingSuccess {...defaultProps} />);

      expect(screen.getByRole('button', { name: /view my bookings/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /book another lesson/i })).toBeInTheDocument();
    });

    it('renders arrow icon in View My Bookings button', () => {
      const { container } = render(<BookingSuccess {...defaultProps} />);

      // ArrowRight icon should be present
      const viewButton = screen.getByRole('button', { name: /view my bookings/i });
      const svg = viewButton.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles zero price', () => {
      const freeBooking = { ...defaultBooking, price: 0 };
      render(<BookingSuccess {...defaultProps} booking={freeBooking} />);

      expect(screen.getByText('$0.00')).toBeInTheDocument();
    });

    it('handles short duration', () => {
      const shortBooking = { ...defaultBooking, duration: 30 };
      render(<BookingSuccess {...defaultProps} booking={shortBooking} />);

      expect(screen.getByText(/30 min/i)).toBeInTheDocument();
    });

    it('handles long duration', () => {
      const longBooking = { ...defaultBooking, duration: 120 };
      render(<BookingSuccess {...defaultProps} booking={longBooking} />);

      expect(screen.getByText(/120 min/i)).toBeInTheDocument();
    });

    it('uses USD as default currency', () => {
      const noCurrencyBooking = {
        bookingId: 1,
        tutorName: 'Test',
        subject: 'Test',
        date: new Date(),
        duration: 60,
        price: 100,
      };
      render(<BookingSuccess {...defaultProps} booking={noCurrencyBooking} />);

      expect(screen.getByText('$100.00')).toBeInTheDocument();
    });
  });
});
