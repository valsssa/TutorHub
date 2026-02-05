import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorDisplay } from '@/components/error/error-display';

describe('ErrorDisplay', () => {
  describe('rendering', () => {
    it('renders with default title and message', () => {
      render(<ErrorDisplay />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByText(/unexpected error/i)).toBeInTheDocument();
    });

    it('renders with custom title', () => {
      render(<ErrorDisplay title="Custom Error Title" />);

      expect(screen.getByText('Custom Error Title')).toBeInTheDocument();
    });

    it('renders with custom message', () => {
      render(<ErrorDisplay message="Custom error message" />);

      expect(screen.getByText('Custom error message')).toBeInTheDocument();
    });

    it('renders retry button when onRetry is provided', () => {
      const onRetry = vi.fn();
      render(<ErrorDisplay onRetry={onRetry} />);

      expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
    });

    it('does not render retry button when onRetry is not provided', () => {
      render(<ErrorDisplay />);

      expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
    });

    it('renders home link by default', () => {
      render(<ErrorDisplay />);

      expect(screen.getByRole('link', { name: /go home/i })).toBeInTheDocument();
    });

    it('does not render home link when showHome is false', () => {
      render(<ErrorDisplay showHome={false} />);

      expect(screen.queryByRole('link', { name: /go home/i })).not.toBeInTheDocument();
    });

    it('renders back button when showBack is true', () => {
      render(<ErrorDisplay showBack={true} />);

      expect(screen.getByRole('button', { name: /go back/i })).toBeInTheDocument();
    });

    it('does not render back button by default', () => {
      render(<ErrorDisplay />);

      expect(screen.queryByRole('button', { name: /go back/i })).not.toBeInTheDocument();
    });
  });

  describe('error details', () => {
    it('does not show error details by default', () => {
      render(<ErrorDisplay errorDetails="Stack trace here" />);

      expect(screen.queryByText('Stack trace here')).not.toBeInTheDocument();
    });

    it('shows error details when showDetails is true', () => {
      render(<ErrorDisplay errorDetails="Stack trace here" showDetails={true} />);

      expect(screen.getByText('Stack trace here')).toBeInTheDocument();
    });
  });

  describe('interactions', () => {
    it('calls onRetry when retry button is clicked', () => {
      const onRetry = vi.fn();
      render(<ErrorDisplay onRetry={onRetry} />);

      const retryButton = screen.getByRole('button', { name: /try again/i });
      fireEvent.click(retryButton);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('calls window.history.back when back button is clicked', () => {
      const mockBack = vi.fn();
      const originalBack = window.history.back;
      window.history.back = mockBack;

      render(<ErrorDisplay showBack={true} />);

      const backButton = screen.getByRole('button', { name: /go back/i });
      fireEvent.click(backButton);

      expect(mockBack).toHaveBeenCalledTimes(1);

      window.history.back = originalBack;
    });
  });

  describe('styling', () => {
    it('applies custom className', () => {
      const { container } = render(<ErrorDisplay className="custom-class" />);

      expect(container.firstChild).toHaveClass('custom-class');
    });

    it('renders error icon', () => {
      render(<ErrorDisplay />);

      // Check for the alert circle icon container
      const iconContainer = document.querySelector('.rounded-full.bg-red-100');
      expect(iconContainer).toBeInTheDocument();
    });
  });
});
