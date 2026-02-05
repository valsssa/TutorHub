import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ReviewForm } from '@/components/reviews/review-form';

describe('ReviewForm', () => {
  const defaultProps = {
    onSubmit: vi.fn(),
  };

  it('renders form with rating and comment fields', () => {
    render(<ReviewForm {...defaultProps} />);

    expect(screen.getByText(/rating/i)).toBeInTheDocument();
    expect(screen.getByText(/comment/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit review/i })).toBeInTheDocument();
  });

  it('renders star rating component', () => {
    render(<ReviewForm {...defaultProps} />);

    const starButtons = screen.getAllByRole('button', { name: /star/i });
    expect(starButtons.length).toBe(5);
  });

  it('renders comment textarea with placeholder', () => {
    render(<ReviewForm {...defaultProps} />);

    expect(
      screen.getByPlaceholderText(/share your experience with this tutor/i)
    ).toBeInTheDocument();
  });

  describe('form submission', () => {
    it('calls onSubmit with form data when valid', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      const starButton = screen.getByRole('button', { name: /4 stars/i });
      await user.click(starButton);

      const textarea = screen.getByPlaceholderText(/share your experience/i);
      await user.type(textarea, 'Great tutor!');

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });

      const callArgs = onSubmit.mock.calls[0][0];
      expect(callArgs.rating).toBe(4);
      expect(callArgs.comment).toBe('Great tutor!');
    });

    it('calls onSubmit with rating only when comment is empty', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      const starButton = screen.getByRole('button', { name: /5 stars/i });
      await user.click(starButton);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });

      const callArgs = onSubmit.mock.calls[0][0];
      expect(callArgs.rating).toBe(5);
      expect(callArgs.comment).toBe('');
    });
  });

  describe('star rating selection', () => {
    it('allows selecting 1 star', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      await user.click(screen.getByRole('button', { name: /1 star$/i }));
      await user.click(screen.getByRole('button', { name: /submit review/i }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });

      expect(onSubmit.mock.calls[0][0].rating).toBe(1);
    });

    it('allows selecting 5 stars', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      await user.click(screen.getByRole('button', { name: /5 stars/i }));
      await user.click(screen.getByRole('button', { name: /submit review/i }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });

      expect(onSubmit.mock.calls[0][0].rating).toBe(5);
    });

    it('allows changing rating selection', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      await user.click(screen.getByRole('button', { name: /3 stars/i }));
      await user.click(screen.getByRole('button', { name: /5 stars/i }));
      await user.click(screen.getByRole('button', { name: /submit review/i }));

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });

      expect(onSubmit.mock.calls[0][0].rating).toBe(5);
    });
  });

  describe('validation errors', () => {
    it('shows error when rating is not selected', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a rating/i)).toBeInTheDocument();
      });
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('does not call onSubmit when form has validation errors', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a rating/i)).toBeInTheDocument();
      });
      expect(onSubmit).not.toHaveBeenCalled();
    });

    it('clears rating error after selecting a rating', async () => {
      const user = userEvent.setup();
      render(<ReviewForm {...defaultProps} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/please select a rating/i)).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /4 stars/i }));

      await waitFor(() => {
        expect(screen.queryByText(/please select a rating/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('loading states', () => {
    it('shows loading state on submit button when isLoading is true', () => {
      render(<ReviewForm {...defaultProps} isLoading={true} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      expect(submitButton).toBeDisabled();
    });

    it('disables submit button when loading', () => {
      render(<ReviewForm {...defaultProps} isLoading={true} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      expect(submitButton).toBeDisabled();
    });

    it('enables submit button when not loading', () => {
      render(<ReviewForm {...defaultProps} isLoading={false} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('comment textarea', () => {
    it('allows typing in comment textarea', async () => {
      const user = userEvent.setup();
      render(<ReviewForm {...defaultProps} />);

      const textarea = screen.getByPlaceholderText(/share your experience/i);
      await user.type(textarea, 'This is my review');

      expect(textarea).toHaveValue('This is my review');
    });

    it('allows long comments', async () => {
      const user = userEvent.setup();
      render(<ReviewForm {...defaultProps} />);

      const longComment = 'A'.repeat(500);
      const textarea = screen.getByPlaceholderText(/share your experience/i);
      await user.type(textarea, longComment);

      expect(textarea).toHaveValue(longComment);
    });
  });

  describe('className prop', () => {
    it('applies custom className to form', () => {
      const { container } = render(
        <ReviewForm {...defaultProps} className="custom-class" />
      );

      const form = container.querySelector('form');
      expect(form).toHaveClass('custom-class');
    });

    it('preserves default classes when custom className is provided', () => {
      const { container } = render(
        <ReviewForm {...defaultProps} className="custom-class" />
      );

      const form = container.querySelector('form');
      expect(form).toHaveClass('space-y-4');
      expect(form).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('has accessible labels for rating', () => {
      render(<ReviewForm {...defaultProps} />);

      expect(screen.getByText(/rating/i)).toBeInTheDocument();
    });

    it('has accessible label for comment field', () => {
      render(<ReviewForm {...defaultProps} />);

      const textarea = screen.getByLabelText(/comment/i);
      expect(textarea).toBeInTheDocument();
    });

    it('star buttons have proper aria-labels', () => {
      render(<ReviewForm {...defaultProps} />);

      expect(screen.getByRole('button', { name: /1 star$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /2 stars/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /3 stars/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /4 stars/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /5 stars/i })).toBeInTheDocument();
    });
  });

  describe('form integration', () => {
    it('submits form on Enter key in textarea', async () => {
      const user = userEvent.setup();
      const onSubmit = vi.fn();
      render(<ReviewForm onSubmit={onSubmit} />);

      await user.click(screen.getByRole('button', { name: /4 stars/i }));

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });
    });

    it('full width submit button', () => {
      render(<ReviewForm {...defaultProps} />);

      const submitButton = screen.getByRole('button', { name: /submit review/i });
      expect(submitButton).toHaveClass('w-full');
    });
  });
});
