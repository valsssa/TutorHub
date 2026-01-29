/**
 * Tests for CancelBookingModal component
 * Critical action: Tests booking cancellation flow
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CancelBookingModal from '@/components/modals/CancelBookingModal';

describe('CancelBookingModal', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnConfirm.mockResolvedValue(undefined);
  });

  it('does not render when closed', () => {
    const { container } = render(
      <CancelBookingModal
        isOpen={false}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders when open', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByRole('heading', { name: /cancel booking/i })).toBeInTheDocument();
  });

  it('displays tutor name when provided', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        tutorName="John Tutor"
      />
    );

    expect(screen.getByText(/session with john tutor/i)).toBeInTheDocument();
  });

  it('displays warning message', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/are you sure you want to cancel/i)).toBeInTheDocument();
    expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
  });

  it('has reason input field', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByLabelText(/reason for cancellation/i)).toBeInTheDocument();
  });

  it('closes when "Keep Booking" is clicked', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /keep booking/i }));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('closes when backdrop is clicked', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    // Click backdrop (first fixed div)
    const backdrop = document.querySelector('.bg-black.bg-opacity-50');
    fireEvent.click(backdrop!);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onConfirm with reason when cancel button clicked', async () => {
    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    const reasonInput = screen.getByLabelText(/reason for cancellation/i);
    await user.type(reasonInput, 'Schedule conflict');

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith('Schedule conflict');
    });
  });

  it('calls onConfirm with undefined when no reason provided', async () => {
    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledWith(undefined);
    });
  });

  it('shows loading state during submission', async () => {
    mockOnConfirm.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    expect(screen.getByText(/canceling.../i)).toBeInTheDocument();
  });

  it('disables buttons during submission', async () => {
    mockOnConfirm.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    expect(screen.getByRole('button', { name: /keep booking/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /canceling.../i })).toBeDisabled();
  });

  it('disables textarea during submission', async () => {
    mockOnConfirm.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    expect(screen.getByLabelText(/reason for cancellation/i)).toBeDisabled();
  });

  it('does not close during submission when backdrop clicked', async () => {
    mockOnConfirm.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    // Try to click backdrop during submission
    const backdrop = document.querySelector('.bg-black.bg-opacity-50');
    fireEvent.click(backdrop!);

    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('closes modal after successful cancellation', async () => {
    const user = userEvent.setup();

    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('clears reason input after successful cancellation', async () => {
    const user = userEvent.setup();
    let resolvePromise: () => void;
    mockOnConfirm.mockImplementation(() => new Promise((r) => { resolvePromise = r; }));

    const { rerender } = render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    const reasonInput = screen.getByLabelText(/reason for cancellation/i);
    await user.type(reasonInput, 'Test reason');

    await user.click(screen.getByRole('button', { name: /^cancel booking$/i }));

    // Resolve the promise
    resolvePromise!();

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('shows helper text for reason field', () => {
    render(
      <CancelBookingModal
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/optional.*helps the tutor understand/i)).toBeInTheDocument();
  });
});
