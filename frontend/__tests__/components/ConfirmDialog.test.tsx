/**
 * Tests for ConfirmDialog component
 * Tests confirmation dialog with various variants and interactions
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConfirmDialog, {
  DeleteConfirmDialog,
  LogoutConfirmDialog,
  UnsavedChangesDialog,
} from '@/components/ConfirmDialog';

describe('ConfirmDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
    title: 'Confirm Action',
    message: 'Are you sure you want to proceed?',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnConfirm.mockResolvedValue(undefined);
  });

  describe('rendering', () => {
    it('does not render when isOpen is false', () => {
      const { container } = render(
        <ConfirmDialog {...defaultProps} isOpen={false} />
      );
      expect(container.firstChild).toBeNull();
    });

    it('renders when isOpen is true', () => {
      render(<ConfirmDialog {...defaultProps} />);
      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    });

    it('displays the title correctly', () => {
      render(<ConfirmDialog {...defaultProps} title="Delete Item" />);
      expect(screen.getByText('Delete Item')).toBeInTheDocument();
    });

    it('displays string message correctly', () => {
      render(<ConfirmDialog {...defaultProps} message="This will delete the item." />);
      expect(screen.getByText('This will delete the item.')).toBeInTheDocument();
    });

    it('displays ReactNode message correctly', () => {
      render(
        <ConfirmDialog
          {...defaultProps}
          message={<span data-testid="custom-message">Custom content</span>}
        />
      );
      expect(screen.getByTestId('custom-message')).toBeInTheDocument();
    });

    it('displays children content', () => {
      render(
        <ConfirmDialog {...defaultProps}>
          <div data-testid="extra-content">Additional information</div>
        </ConfirmDialog>
      );
      expect(screen.getByTestId('extra-content')).toBeInTheDocument();
    });
  });

  describe('buttons', () => {
    it('renders confirm button with default text', () => {
      render(<ConfirmDialog {...defaultProps} />);
      expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
    });

    it('renders cancel button with default text', () => {
      render(<ConfirmDialog {...defaultProps} />);
      expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    });

    it('renders confirm button with custom text', () => {
      render(<ConfirmDialog {...defaultProps} confirmText="Delete" />);
      expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    });

    it('renders cancel button with custom text', () => {
      render(<ConfirmDialog {...defaultProps} cancelText="Go Back" />);
      expect(screen.getByRole('button', { name: 'Go Back' })).toBeInTheDocument();
    });
  });

  describe('confirm action', () => {
    it('calls onConfirm when confirm button is clicked', async () => {
      const user = userEvent.setup();

      render(<ConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Confirm' }));

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledTimes(1);
      });
    });

    it('awaits async onConfirm', async () => {
      const user = userEvent.setup();
      let resolved = false;
      mockOnConfirm.mockImplementation(async () => {
        await new Promise((r) => setTimeout(r, 100));
        resolved = true;
      });

      render(<ConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Confirm' }));

      await waitFor(() => {
        expect(resolved).toBe(true);
      });
    });
  });

  describe('cancel action', () => {
    it('calls onClose when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(<ConfirmDialog {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('escape key', () => {
    it('calls onClose when Escape key is pressed', () => {
      render(<ConfirmDialog {...defaultProps} />);

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });
  });

  describe('loading state', () => {
    it('shows loading indicator when isLoading is true', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByRole('button', { name: /loading/i })).toBeInTheDocument();
    });

    it('disables confirm button when isLoading is true', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByRole('button', { name: /loading/i })).toBeDisabled();
    });

    it('disables cancel button when isLoading is true', () => {
      render(<ConfirmDialog {...defaultProps} isLoading={true} />);

      expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled();
    });
  });

  describe('confirmDisabled', () => {
    it('disables confirm button when confirmDisabled is true', () => {
      render(<ConfirmDialog {...defaultProps} confirmDisabled={true} />);

      expect(screen.getByRole('button', { name: 'Confirm' })).toBeDisabled();
    });
  });

  describe('variants', () => {
    describe('danger variant', () => {
      it('displays danger icon background', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="danger" />
        );
        expect(container.querySelector('.bg-red-100')).toBeInTheDocument();
      });

      it('displays danger icon color', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="danger" />
        );
        expect(container.querySelector('.text-red-600')).toBeInTheDocument();
      });

      it('uses danger button variant', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="danger" />
        );
        // Danger button should have red styling
        const confirmButton = screen.getByRole('button', { name: 'Confirm' });
        expect(confirmButton).toHaveClass('bg-red-600');
      });
    });

    describe('warning variant', () => {
      it('displays warning icon background', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="warning" />
        );
        expect(container.querySelector('.bg-amber-100')).toBeInTheDocument();
      });

      it('displays warning icon color', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="warning" />
        );
        expect(container.querySelector('.text-amber-600')).toBeInTheDocument();
      });
    });

    describe('info variant', () => {
      it('displays info icon background', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="info" />
        );
        expect(container.querySelector('.bg-blue-100')).toBeInTheDocument();
      });

      it('displays info icon color', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="info" />
        );
        expect(container.querySelector('.text-blue-600')).toBeInTheDocument();
      });
    });

    describe('success variant', () => {
      it('displays success icon background', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="success" />
        );
        expect(container.querySelector('.bg-emerald-100')).toBeInTheDocument();
      });

      it('displays success icon color', () => {
        const { container } = render(
          <ConfirmDialog {...defaultProps} variant="success" />
        );
        expect(container.querySelector('.text-emerald-600')).toBeInTheDocument();
      });
    });
  });

  describe('custom icon', () => {
    it('renders custom icon when provided', () => {
      const CustomIcon = () => <span data-testid="custom-icon">Icon</span>;

      render(<ConfirmDialog {...defaultProps} icon={CustomIcon} />);

      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('default variant is danger', () => {
    it('uses danger variant by default', () => {
      const { container } = render(<ConfirmDialog {...defaultProps} />);
      expect(container.querySelector('.bg-red-100')).toBeInTheDocument();
    });
  });
});

describe('DeleteConfirmDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnConfirm.mockResolvedValue(undefined);
  });

  it('renders with "Delete Confirmation" title', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Delete Confirmation')).toBeInTheDocument();
  });

  it('displays default item name in message', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/delete this item/i)).toBeInTheDocument();
  });

  it('displays custom item name in message', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        itemName="your profile"
      />
    );

    expect(screen.getByText(/delete your profile/i)).toBeInTheDocument();
  });

  it('shows "Delete" as confirm button text', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
  });

  it('shows warning about action being undone', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
  });

  it('shows loading state when isLoading is true', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        isLoading={true}
      />
    );

    expect(screen.getByRole('button', { name: /loading/i })).toBeInTheDocument();
  });
});

describe('LogoutConfirmDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnConfirm.mockResolvedValue(undefined);
  });

  it('renders with "Sign Out" title', () => {
    render(
      <LogoutConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Sign Out')).toBeInTheDocument();
  });

  it('displays message about signing out', () => {
    render(
      <LogoutConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/sign out/i)).toBeInTheDocument();
    expect(screen.getByText(/sign in again/i)).toBeInTheDocument();
  });

  it('shows "Sign Out" as confirm button text', () => {
    render(
      <LogoutConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByRole('button', { name: 'Sign Out' })).toBeInTheDocument();
  });

  it('uses warning variant', () => {
    const { container } = render(
      <LogoutConfirmDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(container.querySelector('.bg-amber-100')).toBeInTheDocument();
  });
});

describe('UnsavedChangesDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();
  const mockOnSave = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnSave.mockResolvedValue(undefined);
  });

  it('renders with "Unsaved Changes" title', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText('Unsaved Changes')).toBeInTheDocument();
  });

  it('displays message about unsaved changes', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByText(/unsaved changes/i)).toBeInTheDocument();
  });

  it('shows "Keep Editing" button', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByRole('button', { name: /keep editing/i })).toBeInTheDocument();
  });

  it('shows "Discard Changes" button', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.getByRole('button', { name: /discard changes/i })).toBeInTheDocument();
  });

  it('calls onClose when "Keep Editing" is clicked', async () => {
    const user = userEvent.setup();

    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /keep editing/i }));

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onConfirm when "Discard Changes" is clicked', async () => {
    const user = userEvent.setup();

    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    await user.click(screen.getByRole('button', { name: /discard changes/i }));

    expect(mockOnConfirm).toHaveBeenCalled();
  });

  it('shows "Save Changes" button when onSave is provided', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        onSave={mockOnSave}
      />
    );

    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
  });

  it('does not show "Save Changes" button when onSave is not provided', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(screen.queryByRole('button', { name: /save changes/i })).not.toBeInTheDocument();
  });

  it('calls onSave when "Save Changes" is clicked', async () => {
    const user = userEvent.setup();

    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        onSave={mockOnSave}
      />
    );

    await user.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalled();
    });
  });

  it('shows loading state on save button when isSaving is true', () => {
    render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
        onSave={mockOnSave}
        isSaving={true}
      />
    );

    const saveButton = screen.getByRole('button', { name: /loading/i });
    expect(saveButton).toBeInTheDocument();
  });

  it('displays warning icon', () => {
    const { container } = render(
      <UnsavedChangesDialog
        isOpen={true}
        onClose={mockOnClose}
        onConfirm={mockOnConfirm}
      />
    );

    expect(container.querySelector('.bg-amber-100')).toBeInTheDocument();
  });
});
