import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FavoriteButton } from '@/components/favorites/favorite-button';

// Mock the useToggleFavorite hook
const mockToggle = vi.fn();
vi.mock('@/lib/hooks', () => ({
  useToggleFavorite: (tutorId: number) => mockUseToggleFavorite(tutorId),
}));

const mockUseToggleFavorite = vi.fn();

describe('FavoriteButton', () => {
  const defaultProps = {
    tutorId: 1,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseToggleFavorite.mockReturnValue({
      isFavorite: false,
      isLoading: false,
      toggle: mockToggle,
    });
  });

  it('renders favorite button', () => {
    render(<FavoriteButton {...defaultProps} />);

    const button = screen.getByRole('button', { name: /add to favorites/i });
    expect(button).toBeInTheDocument();
  });

  describe('toggle states', () => {
    it('shows "Add to favorites" label when not favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button', { name: /add to favorites/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-pressed', 'false');
    });

    it('shows "Remove from favorites" label when favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: true,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button', { name: /remove from favorites/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('aria-pressed', 'true');
    });

    it('displays heart icon', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      const svg = button.querySelector('svg');
      expect(svg).toBeInTheDocument();
    });

    it('shows filled heart when favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: true,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      const heartIcon = button.querySelector('svg');
      expect(heartIcon).toHaveClass('fill-red-500');
      expect(heartIcon).toHaveClass('text-red-500');
    });

    it('shows unfilled heart when not favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      const heartIcon = button.querySelector('svg');
      expect(heartIcon).toHaveClass('text-slate-400');
    });
  });

  describe('click handlers', () => {
    it('calls toggle when clicked', async () => {
      const user = userEvent.setup();
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockToggle).toHaveBeenCalledTimes(1);
    });

    it('prevents default click behavior', async () => {
      const user = userEvent.setup();
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockToggle).toHaveBeenCalled();
    });

    it('stops event propagation', async () => {
      const user = userEvent.setup();
      const parentHandler = vi.fn();

      render(
        <div onClick={parentHandler}>
          <FavoriteButton {...defaultProps} />
        </div>
      );

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockToggle).toHaveBeenCalled();
      expect(parentHandler).not.toHaveBeenCalled();
    });

    it('does not call toggle when disabled', async () => {
      const user = userEvent.setup();
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: true,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(mockToggle).not.toHaveBeenCalled();
    });

    it('passes correct tutorId to hook', () => {
      render(<FavoriteButton tutorId={42} />);

      expect(mockUseToggleFavorite).toHaveBeenCalledWith(42);
    });
  });

  describe('loading states', () => {
    it('shows loading spinner when isLoading is true', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: true,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      const spinner = button.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('disables button when loading', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: true,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('shows heart icon when not loading', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      const spinner = button.querySelector('.animate-spin');
      expect(spinner).not.toBeInTheDocument();
    });

    it('enables button when not loading', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).not.toBeDisabled();
    });
  });

  describe('sizes', () => {
    it('renders with small size', () => {
      render(<FavoriteButton {...defaultProps} size="sm" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-8', 'w-8');
    });

    it('renders with medium size (default)', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });

    it('renders with medium size when explicitly set', () => {
      render(<FavoriteButton {...defaultProps} size="md" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10', 'w-10');
    });

    it('renders with large size', () => {
      render(<FavoriteButton {...defaultProps} size="lg" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-12', 'w-12');
    });

    it('renders icon with correct size for small button', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} size="sm" />);

      const button = screen.getByRole('button');
      const icon = button.querySelector('svg');
      expect(icon).toHaveClass('h-4', 'w-4');
    });

    it('renders icon with correct size for medium button', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} size="md" />);

      const button = screen.getByRole('button');
      const icon = button.querySelector('svg');
      expect(icon).toHaveClass('h-5', 'w-5');
    });

    it('renders icon with correct size for large button', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} size="lg" />);

      const button = screen.getByRole('button');
      const icon = button.querySelector('svg');
      expect(icon).toHaveClass('h-6', 'w-6');
    });
  });

  describe('className prop', () => {
    it('applies custom className', () => {
      render(<FavoriteButton {...defaultProps} className="custom-class" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });

    it('preserves default classes with custom className', () => {
      render(<FavoriteButton {...defaultProps} className="custom-class" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('rounded-full');
      expect(button).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('has correct aria-label when not favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: false,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Add to favorites');
    });

    it('has correct aria-label when favorited', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: true,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Remove from favorites');
    });

    it('has aria-pressed attribute', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-pressed');
    });

    it('aria-pressed reflects favorite state', () => {
      mockUseToggleFavorite.mockReturnValue({
        isFavorite: true,
        isLoading: false,
        toggle: mockToggle,
      });

      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-pressed', 'true');
    });

    it('is focusable', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();
    });

    it('has focus ring styles', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('focus:outline-none', 'focus:ring-2');
    });
  });

  describe('styling', () => {
    it('has rounded-full class', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('rounded-full');
    });

    it('has backdrop blur styling', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('backdrop-blur-sm');
    });

    it('has hover scale effect class', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:scale-105');
    });

    it('has active scale effect class', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('active:scale-95');
    });

    it('has shadow classes', () => {
      render(<FavoriteButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('shadow-md', 'hover:shadow-lg');
    });
  });
});
