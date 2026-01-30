/**
 * Tests for EmptyState component
 * Tests empty state display for various use cases
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EmptyState, {
  NoResultsEmptyState,
  ErrorEmptyState,
  FirstTimeEmptyState,
} from '@/components/EmptyState';

describe('EmptyState', () => {
  describe('Basic Rendering', () => {
    it('renders with required title', () => {
      render(<EmptyState title="No items found" />);

      expect(screen.getByRole('heading', { name: /no items found/i })).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      render(
        <EmptyState
          title="Empty"
          description="There are no items to display"
        />
      );

      expect(screen.getByText('There are no items to display')).toBeInTheDocument();
    });

    it('renders hint when provided', () => {
      render(
        <EmptyState
          title="Empty"
          hint="Try adding some items"
        />
      );

      expect(screen.getByText('Try adding some items')).toBeInTheDocument();
    });

    it('has proper accessibility role and label', () => {
      render(<EmptyState title="No data" />);

      const container = screen.getByRole('status');
      expect(container).toHaveAttribute('aria-label', 'No data');
    });
  });

  describe('Variants', () => {
    const variants = [
      'no-data',
      'no-results',
      'error',
      'first-time',
      'no-messages',
      'no-bookings',
      'no-favorites',
      'no-packages',
      'no-notifications',
      'no-students',
      'no-earnings',
    ] as const;

    variants.forEach((variant) => {
      it(`renders ${variant} variant with icon`, () => {
        const { container } = render(
          <EmptyState variant={variant} title={`Test ${variant}`} />
        );

        // Each variant should have an icon
        const icon = container.querySelector('svg');
        expect(icon).toBeInTheDocument();
        expect(icon).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('renders no-data variant with slate colors', () => {
      const { container } = render(
        <EmptyState variant="no-data" title="No data" />
      );

      // Should have slate background color
      const iconWrapper = container.querySelector('.bg-slate-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-results variant with amber colors', () => {
      const { container } = render(
        <EmptyState variant="no-results" title="No results" />
      );

      // Should have amber background color
      const iconWrapper = container.querySelector('.bg-amber-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders error variant with red colors', () => {
      const { container } = render(
        <EmptyState variant="error" title="Error" />
      );

      // Should have red background color
      const iconWrapper = container.querySelector('.bg-red-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders first-time variant with emerald colors', () => {
      const { container } = render(
        <EmptyState variant="first-time" title="Welcome" />
      );

      // Should have emerald background color
      const iconWrapper = container.querySelector('.bg-emerald-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-messages variant with blue colors', () => {
      const { container } = render(
        <EmptyState variant="no-messages" title="No messages" />
      );

      const iconWrapper = container.querySelector('.bg-blue-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-bookings variant with purple colors', () => {
      const { container } = render(
        <EmptyState variant="no-bookings" title="No bookings" />
      );

      const iconWrapper = container.querySelector('.bg-purple-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-favorites variant with rose colors', () => {
      const { container } = render(
        <EmptyState variant="no-favorites" title="No favorites" />
      );

      const iconWrapper = container.querySelector('.bg-rose-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-packages variant with indigo colors', () => {
      const { container } = render(
        <EmptyState variant="no-packages" title="No packages" />
      );

      const iconWrapper = container.querySelector('.bg-indigo-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-notifications variant with orange colors', () => {
      const { container } = render(
        <EmptyState variant="no-notifications" title="No notifications" />
      );

      const iconWrapper = container.querySelector('.bg-orange-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-students variant with cyan colors', () => {
      const { container } = render(
        <EmptyState variant="no-students" title="No students" />
      );

      const iconWrapper = container.querySelector('.bg-cyan-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('renders no-earnings variant with green colors', () => {
      const { container } = render(
        <EmptyState variant="no-earnings" title="No earnings" />
      );

      const iconWrapper = container.querySelector('.bg-green-100');
      expect(iconWrapper).toBeInTheDocument();
    });

    it('uses no-data as default variant', () => {
      const { container } = render(<EmptyState title="Default" />);

      const iconWrapper = container.querySelector('.bg-slate-100');
      expect(iconWrapper).toBeInTheDocument();
    });
  });

  describe('Action Buttons', () => {
    it('renders primary action button when provided', () => {
      const mockAction = jest.fn();
      render(
        <EmptyState
          title="Empty"
          action={{ label: 'Add Item', onClick: mockAction }}
        />
      );

      expect(screen.getByRole('button', { name: /add item/i })).toBeInTheDocument();
    });

    it('calls action onClick when button clicked', async () => {
      const user = userEvent.setup();
      const mockAction = jest.fn();
      render(
        <EmptyState
          title="Empty"
          action={{ label: 'Add Item', onClick: mockAction }}
        />
      );

      await user.click(screen.getByRole('button', { name: /add item/i }));
      expect(mockAction).toHaveBeenCalled();
    });

    it('renders secondary action button when provided', () => {
      const mockPrimary = jest.fn();
      const mockSecondary = jest.fn();
      render(
        <EmptyState
          title="Empty"
          action={{ label: 'Primary', onClick: mockPrimary }}
          secondaryAction={{ label: 'Secondary', onClick: mockSecondary }}
        />
      );

      expect(screen.getByRole('button', { name: /primary/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /secondary/i })).toBeInTheDocument();
    });

    it('calls secondary action onClick when button clicked', async () => {
      const user = userEvent.setup();
      const mockSecondary = jest.fn();
      render(
        <EmptyState
          title="Empty"
          secondaryAction={{ label: 'Learn More', onClick: mockSecondary }}
        />
      );

      await user.click(screen.getByRole('button', { name: /learn more/i }));
      expect(mockSecondary).toHaveBeenCalled();
    });

    it('applies action variant styles', () => {
      render(
        <EmptyState
          title="Empty"
          action={{ label: 'Danger Action', onClick: jest.fn(), variant: 'secondary' }}
        />
      );

      const button = screen.getByRole('button', { name: /danger action/i });
      // Secondary variant should have slate background
      expect(button).toHaveClass('bg-slate-100');
    });

    it('uses primary variant as default for action', () => {
      render(
        <EmptyState
          title="Empty"
          action={{ label: 'Default', onClick: jest.fn() }}
        />
      );

      const button = screen.getByRole('button', { name: /default/i });
      expect(button).toHaveClass('bg-emerald-600');
    });

    it('uses ghost variant as default for secondary action', () => {
      render(
        <EmptyState
          title="Empty"
          secondaryAction={{ label: 'Ghost', onClick: jest.fn() }}
        />
      );

      const button = screen.getByRole('button', { name: /ghost/i });
      expect(button).toHaveClass('text-slate-700');
    });
  });

  describe('Custom Icons', () => {
    it('uses custom icon component when provided', () => {
      const CustomIcon = () => <span data-testid="custom-icon">Custom</span>;
      // Note: The icon prop expects a LucideIcon component
      // For testing purposes, we can't easily pass a custom component
      // This test documents the expected behavior
      const { container } = render(
        <EmptyState
          title="Custom"
          iconElement={<span data-testid="custom-element">Custom</span>}
        />
      );

      expect(screen.getByTestId('custom-element')).toBeInTheDocument();
    });

    it('uses iconElement over variant icon', () => {
      render(
        <EmptyState
          variant="error"
          title="Test"
          iconElement={<span data-testid="override-icon">Override</span>}
        />
      );

      expect(screen.getByTestId('override-icon')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it('applies sm size classes', () => {
      const { container } = render(
        <EmptyState title="Small" size="sm" />
      );

      expect(container.querySelector('.py-6')).toBeInTheDocument();
      expect(container.querySelector('.w-12')).toBeInTheDocument();
    });

    it('applies md size classes (default)', () => {
      const { container } = render(
        <EmptyState title="Medium" size="md" />
      );

      expect(container.querySelector('.py-10')).toBeInTheDocument();
      expect(container.querySelector('.w-16')).toBeInTheDocument();
    });

    it('applies lg size classes', () => {
      const { container } = render(
        <EmptyState title="Large" size="lg" />
      );

      expect(container.querySelector('.py-16')).toBeInTheDocument();
      expect(container.querySelector('.w-20')).toBeInTheDocument();
    });

    it('uses md as default size', () => {
      const { container } = render(<EmptyState title="Default Size" />);

      expect(container.querySelector('.py-10')).toBeInTheDocument();
    });
  });

  describe('Background', () => {
    it('shows background by default', () => {
      const { container } = render(
        <EmptyState variant="no-data" title="With Background" />
      );

      expect(container.querySelector('.bg-slate-100')).toBeInTheDocument();
    });

    it('hides background when showBackground is false', () => {
      const { container } = render(
        <EmptyState
          variant="no-data"
          title="No Background"
          showBackground={false}
        />
      );

      // The icon wrapper should not have the background class
      const iconWrapper = container.querySelector('.w-16.h-16');
      expect(iconWrapper).not.toHaveClass('bg-slate-100');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <EmptyState title="Custom" className="custom-empty-state" />
      );

      expect(container.firstChild).toHaveClass('custom-empty-state');
    });
  });
});

describe('NoResultsEmptyState', () => {
  it('renders with default messaging', () => {
    render(<NoResultsEmptyState />);

    expect(screen.getByRole('heading', { name: /no results found/i })).toBeInTheDocument();
    expect(screen.getByText(/check your spelling/i)).toBeInTheDocument();
  });

  it('displays search query in description', () => {
    render(<NoResultsEmptyState searchQuery="math tutor" />);

    expect(screen.getByText(/couldn't find anything matching "math tutor"/i)).toBeInTheDocument();
  });

  it('shows clear search button when handler provided', () => {
    const mockClear = jest.fn();
    render(<NoResultsEmptyState onClearSearch={mockClear} />);

    expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument();
  });

  it('calls onClearSearch when button clicked', async () => {
    const user = userEvent.setup();
    const mockClear = jest.fn();
    render(<NoResultsEmptyState onClearSearch={mockClear} />);

    await user.click(screen.getByRole('button', { name: /clear search/i }));
    expect(mockClear).toHaveBeenCalled();
  });

  it('does not show button when no handler provided', () => {
    render(<NoResultsEmptyState />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});

describe('ErrorEmptyState', () => {
  it('renders with default messaging', () => {
    render(<ErrorEmptyState />);

    expect(screen.getByRole('heading', { name: /something went wrong/i })).toBeInTheDocument();
    expect(screen.getByText(/encountered an error/i)).toBeInTheDocument();
  });

  it('displays custom error message', () => {
    render(<ErrorEmptyState message="Network connection failed" />);

    expect(screen.getByText('Network connection failed')).toBeInTheDocument();
  });

  it('shows try again button when handler provided', () => {
    const mockRetry = jest.fn();
    render(<ErrorEmptyState onRetry={mockRetry} />);

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('calls onRetry when button clicked', async () => {
    const user = userEvent.setup();
    const mockRetry = jest.fn();
    render(<ErrorEmptyState onRetry={mockRetry} />);

    await user.click(screen.getByRole('button', { name: /try again/i }));
    expect(mockRetry).toHaveBeenCalled();
  });

  it('does not show button when no handler provided', () => {
    render(<ErrorEmptyState />);

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});

describe('FirstTimeEmptyState', () => {
  it('renders with feature name in title', () => {
    render(
      <FirstTimeEmptyState
        featureName="Bookings"
        description="Book your first lesson"
      />
    );

    expect(screen.getByRole('heading', { name: /welcome to bookings/i })).toBeInTheDocument();
  });

  it('displays description', () => {
    render(
      <FirstTimeEmptyState
        featureName="Messages"
        description="Start chatting with tutors"
      />
    );

    expect(screen.getByText('Start chatting with tutors')).toBeInTheDocument();
  });

  it('shows get started hint', () => {
    render(
      <FirstTimeEmptyState
        featureName="Test"
        description="Test description"
      />
    );

    expect(screen.getByText(/let's get you started/i)).toBeInTheDocument();
  });

  it('shows get started button when handler provided', () => {
    const mockGetStarted = jest.fn();
    render(
      <FirstTimeEmptyState
        featureName="Wallet"
        description="Manage your funds"
        onGetStarted={mockGetStarted}
      />
    );

    expect(screen.getByRole('button', { name: /get started/i })).toBeInTheDocument();
  });

  it('calls onGetStarted when button clicked', async () => {
    const user = userEvent.setup();
    const mockGetStarted = jest.fn();
    render(
      <FirstTimeEmptyState
        featureName="Packages"
        description="Create lesson packages"
        onGetStarted={mockGetStarted}
      />
    );

    await user.click(screen.getByRole('button', { name: /get started/i }));
    expect(mockGetStarted).toHaveBeenCalled();
  });

  it('does not show button when no handler provided', () => {
    render(
      <FirstTimeEmptyState
        featureName="Reviews"
        description="See your reviews"
      />
    );

    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
