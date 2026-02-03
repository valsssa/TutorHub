import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BookingStatusBadge } from '@/components/bookings/booking-status-badge';
import type { SessionState } from '@/types';

describe('BookingStatusBadge', () => {
  it('renders pending_tutor status', () => {
    render(<BookingStatusBadge status="pending_tutor" />);
    expect(screen.getByText(/awaiting tutor/i)).toBeInTheDocument();
  });

  it('renders pending_student status', () => {
    render(<BookingStatusBadge status="pending_student" />);
    expect(screen.getByText(/awaiting you/i)).toBeInTheDocument();
  });

  it('renders confirmed status', () => {
    render(<BookingStatusBadge status="confirmed" />);
    expect(screen.getByText(/confirmed/i)).toBeInTheDocument();
  });

  it('renders in_progress status', () => {
    render(<BookingStatusBadge status="in_progress" />);
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
  });

  it('renders completed status', () => {
    render(<BookingStatusBadge status="completed" />);
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('renders cancelled status', () => {
    render(<BookingStatusBadge status="cancelled" />);
    expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
  });

  it('renders expired status', () => {
    render(<BookingStatusBadge status="expired" />);
    expect(screen.getByText(/expired/i)).toBeInTheDocument();
  });

  it('renders no_show status', () => {
    render(<BookingStatusBadge status="no_show" />);
    expect(screen.getByText(/no show/i)).toBeInTheDocument();
  });

  describe('status variant colors', () => {
    const statusVariantMap: Array<{
      status: SessionState;
      expectedClass: string;
    }> = [
      { status: 'pending_tutor', expectedClass: 'bg-amber-100' },
      { status: 'pending_student', expectedClass: 'bg-blue-100' },
      { status: 'confirmed', expectedClass: 'bg-green-100' },
      { status: 'in_progress', expectedClass: 'bg-primary-100' },
      { status: 'completed', expectedClass: 'bg-green-100' },
      { status: 'cancelled', expectedClass: 'bg-red-100' },
      { status: 'expired', expectedClass: 'bg-slate-100' },
      { status: 'no_show', expectedClass: 'bg-red-100' },
    ];

    statusVariantMap.forEach(({ status, expectedClass }) => {
      it(`applies ${expectedClass} for ${status} status`, () => {
        const { container } = render(<BookingStatusBadge status={status} />);
        const badge = container.firstChild;
        expect(badge).toHaveClass(expectedClass);
      });
    });
  });

  describe('status labels', () => {
    const statusLabelMap: Array<{
      status: SessionState;
      expectedLabel: string;
    }> = [
      { status: 'pending_tutor', expectedLabel: 'Awaiting Tutor' },
      { status: 'pending_student', expectedLabel: 'Awaiting You' },
      { status: 'confirmed', expectedLabel: 'Confirmed' },
      { status: 'in_progress', expectedLabel: 'In Progress' },
      { status: 'completed', expectedLabel: 'Completed' },
      { status: 'cancelled', expectedLabel: 'Cancelled' },
      { status: 'expired', expectedLabel: 'Expired' },
      { status: 'no_show', expectedLabel: 'No Show' },
    ];

    statusLabelMap.forEach(({ status, expectedLabel }) => {
      it(`displays "${expectedLabel}" for ${status} status`, () => {
        render(<BookingStatusBadge status={status} />);
        expect(screen.getByText(expectedLabel)).toBeInTheDocument();
      });
    });
  });

  it('handles unknown status gracefully', () => {
    render(<BookingStatusBadge status={'unknown_status' as SessionState} />);
    expect(screen.getByText('unknown_status')).toBeInTheDocument();
  });
});
