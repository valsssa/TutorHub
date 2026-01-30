/**
 * Tests for StatusBadge component
 * Tests status badge display for various status types
 */

import { render, screen } from '@testing-library/react';
import StatusBadge, {
  sessionStateConfig,
  sessionOutcomeConfig,
  paymentStateConfig,
  disputeStateConfig,
  genericStatusConfig,
} from '@/components/StatusBadge';

describe('StatusBadge', () => {
  describe('Basic Rendering', () => {
    it('renders with status text', () => {
      render(<StatusBadge status="pending" />);

      expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('renders icon by default', () => {
      const { container } = render(<StatusBadge status="pending" />);

      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('hides icon when showIcon is false', () => {
      const { container } = render(
        <StatusBadge status="pending" showIcon={false} />
      );

      const icon = container.querySelector('svg');
      expect(icon).not.toBeInTheDocument();
    });

    it('uses custom label when provided', () => {
      render(<StatusBadge status="pending" label="Awaiting Review" />);

      expect(screen.getByText('Awaiting Review')).toBeInTheDocument();
      expect(screen.queryByText('Pending')).not.toBeInTheDocument();
    });
  });

  describe('Session State Variants', () => {
    const sessionStates = [
      { status: 'REQUESTED', label: 'Pending', colorClass: 'text-amber-700' },
      { status: 'SCHEDULED', label: 'Scheduled', colorClass: 'text-blue-700' },
      { status: 'ACTIVE', label: 'In Progress', colorClass: 'text-emerald-700' },
      { status: 'ENDED', label: 'Completed', colorClass: 'text-green-700' },
      { status: 'EXPIRED', label: 'Expired', colorClass: 'text-slate-600' },
      { status: 'CANCELLED', label: 'Cancelled', colorClass: 'text-red-700' },
    ];

    sessionStates.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} session state with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="session" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });

    it('handles lowercase session state', () => {
      render(<StatusBadge status="requested" type="session" />);

      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  describe('Session Outcome Variants', () => {
    const outcomes = [
      { status: 'COMPLETED', label: 'Completed', colorClass: 'text-green-700' },
      { status: 'NOT_HELD', label: 'Not Held', colorClass: 'text-slate-600' },
      { status: 'NO_SHOW_STUDENT', label: 'Student No-Show', colorClass: 'text-orange-700' },
      { status: 'NO_SHOW_TUTOR', label: 'Tutor No-Show', colorClass: 'text-red-700' },
    ];

    outcomes.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} outcome with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="outcome" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });
  });

  describe('Payment State Variants', () => {
    const paymentStates = [
      { status: 'PENDING', label: 'Pending', colorClass: 'text-amber-700' },
      { status: 'AUTHORIZED', label: 'Authorized', colorClass: 'text-blue-700' },
      { status: 'CAPTURED', label: 'Paid', colorClass: 'text-green-700' },
      { status: 'VOIDED', label: 'Voided', colorClass: 'text-slate-600' },
      { status: 'REFUNDED', label: 'Refunded', colorClass: 'text-purple-700' },
      { status: 'PARTIALLY_REFUNDED', label: 'Partial Refund', colorClass: 'text-purple-700' },
    ];

    paymentStates.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} payment state with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="payment" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });
  });

  describe('Dispute State Variants', () => {
    const disputeStates = [
      { status: 'NONE', label: 'No Dispute', colorClass: 'text-slate-600' },
      { status: 'OPEN', label: 'Under Review', colorClass: 'text-amber-700' },
      { status: 'RESOLVED_UPHELD', label: 'Upheld', colorClass: 'text-blue-700' },
      { status: 'RESOLVED_REFUNDED', label: 'Refunded', colorClass: 'text-green-700' },
    ];

    disputeStates.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} dispute state with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="dispute" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });
  });

  describe('Generic Status Variants', () => {
    const genericStatuses = [
      { status: 'pending', label: 'Pending', colorClass: 'text-amber-700' },
      { status: 'approved', label: 'Approved', colorClass: 'text-emerald-700' },
      { status: 'rejected', label: 'Rejected', colorClass: 'text-red-700' },
      { status: 'active', label: 'Active', colorClass: 'text-emerald-700' },
      { status: 'inactive', label: 'Inactive', colorClass: 'text-slate-600' },
      { status: 'verified', label: 'Verified', colorClass: 'text-emerald-700' },
      { status: 'unverified', label: 'Unverified', colorClass: 'text-slate-600' },
      { status: 'warning', label: 'Warning', colorClass: 'text-amber-700' },
      { status: 'error', label: 'Error', colorClass: 'text-red-700' },
      { status: 'success', label: 'Success', colorClass: 'text-green-700' },
      { status: 'info', label: 'Info', colorClass: 'text-blue-700' },
    ];

    genericStatuses.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} generic status with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="generic" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });

    it('uses generic as default type', () => {
      const { container } = render(<StatusBadge status="pending" />);

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('text-amber-700');
    });
  });

  describe('Tutor Approval Variants', () => {
    const approvalStates = [
      { status: 'incomplete', label: 'Incomplete', colorClass: 'text-slate-600' },
      { status: 'pending_approval', label: 'Pending Review', colorClass: 'text-amber-700' },
      { status: 'under_review', label: 'Under Review', colorClass: 'text-blue-700' },
      { status: 'approved', label: 'Approved', colorClass: 'text-emerald-700' },
      { status: 'rejected', label: 'Rejected', colorClass: 'text-red-700' },
    ];

    approvalStates.forEach(({ status, label, colorClass }) => {
      it(`renders ${status} tutor approval with correct label and color`, () => {
        const { container } = render(
          <StatusBadge status={status} type="tutor-approval" />
        );

        expect(screen.getByText(label)).toBeInTheDocument();
        expect(container.firstChild).toHaveClass(colorClass);
      });
    });
  });

  describe('Size Variants', () => {
    it('applies sm size classes', () => {
      const { container } = render(
        <StatusBadge status="pending" size="sm" />
      );

      expect(container.firstChild).toHaveClass('text-xs', 'px-2', 'py-0.5');
      expect(container.querySelector('svg')).toHaveClass('w-3', 'h-3');
    });

    it('applies md size classes (default)', () => {
      const { container } = render(
        <StatusBadge status="pending" size="md" />
      );

      expect(container.firstChild).toHaveClass('text-xs', 'px-2.5', 'py-1');
      expect(container.querySelector('svg')).toHaveClass('w-3.5', 'h-3.5');
    });

    it('applies lg size classes', () => {
      const { container } = render(
        <StatusBadge status="pending" size="lg" />
      );

      expect(container.firstChild).toHaveClass('text-sm', 'px-3', 'py-1.5');
      expect(container.querySelector('svg')).toHaveClass('w-4', 'h-4');
    });

    it('uses md as default size', () => {
      const { container } = render(<StatusBadge status="pending" />);

      expect(container.firstChild).toHaveClass('px-2.5', 'py-1');
    });
  });

  describe('Style Variants', () => {
    it('applies default variant styles', () => {
      const { container } = render(
        <StatusBadge status="pending" variant="default" />
      );

      expect(container.firstChild).toHaveClass('rounded-md', 'bg-amber-100');
    });

    it('applies pill variant styles', () => {
      const { container } = render(
        <StatusBadge status="pending" variant="pill" />
      );

      expect(container.firstChild).toHaveClass('rounded-full', 'bg-amber-100');
    });

    it('applies outline variant styles', () => {
      const { container } = render(
        <StatusBadge status="pending" variant="outline" />
      );

      expect(container.firstChild).toHaveClass('rounded-md', 'border', 'bg-transparent');
    });

    it('applies subtle variant styles', () => {
      const { container } = render(
        <StatusBadge status="pending" variant="subtle" />
      );

      expect(container.firstChild).toHaveClass('rounded-md', 'bg-transparent');
    });

    it('uses default as default variant', () => {
      const { container } = render(<StatusBadge status="pending" />);

      expect(container.firstChild).toHaveClass('rounded-md', 'bg-amber-100');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <StatusBadge status="pending" className="custom-badge" />
      );

      expect(container.firstChild).toHaveClass('custom-badge');
    });
  });

  describe('Unknown Status Fallback', () => {
    it('falls back to info config for unknown session state', () => {
      const { container } = render(
        <StatusBadge status="UNKNOWN_STATE" type="session" />
      );

      expect(screen.getByText('Info')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('text-blue-700');
    });

    it('falls back to info config for unknown generic status', () => {
      const { container } = render(
        <StatusBadge status="unknown_status" type="generic" />
      );

      expect(screen.getByText('Info')).toBeInTheDocument();
      expect(container.firstChild).toHaveClass('text-blue-700');
    });
  });

  describe('Accessibility', () => {
    it('icon has aria-hidden attribute', () => {
      const { container } = render(<StatusBadge status="pending" />);

      const icon = container.querySelector('svg');
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    });

    it('renders as inline element', () => {
      const { container } = render(<StatusBadge status="pending" />);

      expect(container.firstChild).toHaveClass('inline-flex');
    });

    it('has proper text visibility with icon alignment', () => {
      const { container } = render(<StatusBadge status="pending" />);

      expect(container.firstChild).toHaveClass('items-center', 'gap-1.5');
    });
  });

  describe('Exported Configs', () => {
    it('exports sessionStateConfig', () => {
      expect(sessionStateConfig).toBeDefined();
      expect(sessionStateConfig.REQUESTED).toBeDefined();
      expect(sessionStateConfig.SCHEDULED).toBeDefined();
      expect(sessionStateConfig.ACTIVE).toBeDefined();
      expect(sessionStateConfig.ENDED).toBeDefined();
      expect(sessionStateConfig.EXPIRED).toBeDefined();
      expect(sessionStateConfig.CANCELLED).toBeDefined();
    });

    it('exports sessionOutcomeConfig', () => {
      expect(sessionOutcomeConfig).toBeDefined();
      expect(sessionOutcomeConfig.COMPLETED).toBeDefined();
      expect(sessionOutcomeConfig.NOT_HELD).toBeDefined();
      expect(sessionOutcomeConfig.NO_SHOW_STUDENT).toBeDefined();
      expect(sessionOutcomeConfig.NO_SHOW_TUTOR).toBeDefined();
    });

    it('exports paymentStateConfig', () => {
      expect(paymentStateConfig).toBeDefined();
      expect(paymentStateConfig.PENDING).toBeDefined();
      expect(paymentStateConfig.AUTHORIZED).toBeDefined();
      expect(paymentStateConfig.CAPTURED).toBeDefined();
      expect(paymentStateConfig.VOIDED).toBeDefined();
      expect(paymentStateConfig.REFUNDED).toBeDefined();
      expect(paymentStateConfig.PARTIALLY_REFUNDED).toBeDefined();
    });

    it('exports disputeStateConfig', () => {
      expect(disputeStateConfig).toBeDefined();
      expect(disputeStateConfig.NONE).toBeDefined();
      expect(disputeStateConfig.OPEN).toBeDefined();
      expect(disputeStateConfig.RESOLVED_UPHELD).toBeDefined();
      expect(disputeStateConfig.RESOLVED_REFUNDED).toBeDefined();
    });

    it('exports genericStatusConfig', () => {
      expect(genericStatusConfig).toBeDefined();
      expect(genericStatusConfig.pending).toBeDefined();
      expect(genericStatusConfig.approved).toBeDefined();
      expect(genericStatusConfig.rejected).toBeDefined();
      expect(genericStatusConfig.active).toBeDefined();
      expect(genericStatusConfig.inactive).toBeDefined();
      expect(genericStatusConfig.verified).toBeDefined();
      expect(genericStatusConfig.unverified).toBeDefined();
      expect(genericStatusConfig.warning).toBeDefined();
      expect(genericStatusConfig.error).toBeDefined();
      expect(genericStatusConfig.success).toBeDefined();
      expect(genericStatusConfig.info).toBeDefined();
    });

    it('config objects have required properties', () => {
      const config = sessionStateConfig.REQUESTED;
      expect(config).toHaveProperty('label');
      expect(config).toHaveProperty('icon');
      expect(config).toHaveProperty('colorClasses');
      expect(config).toHaveProperty('bgClasses');
      expect(config).toHaveProperty('borderClasses');
    });
  });
});
