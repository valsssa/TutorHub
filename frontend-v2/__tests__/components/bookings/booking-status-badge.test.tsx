import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BookingStatusBadge } from '@/components/bookings/booking-status-badge';
import type { SessionState } from '@/types';

describe('BookingStatusBadge', () => {
  describe('uppercase states', () => {
    it('renders REQUESTED status', () => {
      render(<BookingStatusBadge status="REQUESTED" />);
      expect(screen.getByText(/requested/i)).toBeInTheDocument();
    });

    it('renders SCHEDULED status', () => {
      render(<BookingStatusBadge status="SCHEDULED" />);
      expect(screen.getByText(/scheduled/i)).toBeInTheDocument();
    });

    it('renders ACTIVE status', () => {
      render(<BookingStatusBadge status="ACTIVE" />);
      expect(screen.getByText(/active/i)).toBeInTheDocument();
    });

    it('renders ENDED status', () => {
      render(<BookingStatusBadge status="ENDED" />);
      expect(screen.getByText(/ended/i)).toBeInTheDocument();
    });

    it('renders EXPIRED status', () => {
      render(<BookingStatusBadge status="EXPIRED" />);
      expect(screen.getByText(/expired/i)).toBeInTheDocument();
    });

    it('renders CANCELLED status', () => {
      render(<BookingStatusBadge status="CANCELLED" />);
      expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
    });
  });

  describe('state labels', () => {
    const statusLabelMap: Array<{
      status: SessionState;
      expectedLabel: string;
    }> = [
      { status: 'REQUESTED', expectedLabel: 'Requested' },
      { status: 'SCHEDULED', expectedLabel: 'Scheduled' },
      { status: 'ACTIVE', expectedLabel: 'Active' },
      { status: 'ENDED', expectedLabel: 'Ended' },
      { status: 'EXPIRED', expectedLabel: 'Expired' },
      { status: 'CANCELLED', expectedLabel: 'Cancelled' },
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
