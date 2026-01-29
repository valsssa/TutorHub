/**
 * Page-level tests for Settings pages
 *
 * Tests for various settings sections including:
 * - Account settings
 * - Notification preferences
 * - Privacy settings
 * - Payment settings
 * - Integration settings
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { auth, notifications, avatars } from '@/lib/api';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => '/settings',
  useSearchParams: () => new URLSearchParams(),
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
  showWarning: jest.fn(),
};

jest.mock('@/components/ToastContainer', () => ({
  useToast: () => toastMocks,
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock user data
const mockUser = {
  id: 1,
  email: 'user@example.com',
  role: 'student',
  is_active: true,
  is_verified: true,
  first_name: 'John',
  last_name: 'Doe',
  timezone: 'America/New_York',
  currency: 'USD',
  avatar_url: null,
};

const mockNotificationPreferences = {
  email_enabled: true,
  push_enabled: true,
  sms_enabled: false,
  session_reminders_enabled: true,
  booking_requests_enabled: true,
  learning_nudges_enabled: false,
  review_prompts_enabled: true,
  achievements_enabled: true,
  marketing_enabled: false,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',
  preferred_notification_time: null,
  max_daily_notifications: 10,
  max_weekly_nudges: 3,
};

describe('Account Settings Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('renders account settings with user info', async () => {
    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
      expect(screen.getByDisplayValue('user@example.com')).toBeInTheDocument();
    });
  });

  it('allows updating profile information', async () => {
    const user = userEvent.setup();

    (auth.updateUser as jest.Mock).mockResolvedValue({
      ...mockUser,
      first_name: 'Johnny',
    });

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    });

    // Clear and update first name
    const firstNameInput = screen.getByLabelText(/first.*name/i);
    await user.clear(firstNameInput);
    await user.type(firstNameInput, 'Johnny');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save|update/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(auth.updateUser).toHaveBeenCalledWith(
        expect.objectContaining({ first_name: 'Johnny' })
      );
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });

  it('validates email format', async () => {
    const user = userEvent.setup();

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('user@example.com')).toBeInTheDocument();
    });

    // Enter invalid email
    const emailInput = screen.getByLabelText(/email/i);
    await user.clear(emailInput);
    await user.type(emailInput, 'invalid-email');

    const saveButton = screen.getByRole('button', { name: /save|update/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/valid.*email|invalid.*email/i)).toBeInTheDocument();
    });

    expect(auth.updateUser).not.toHaveBeenCalled();
  });

  it('allows timezone selection', async () => {
    const user = userEvent.setup();

    (auth.updatePreferences as jest.Mock).mockResolvedValue({
      ...mockUser,
      timezone: 'Europe/London',
    });

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue(/new.*york/i)).toBeInTheDocument();
    });

    // Change timezone
    const timezoneSelect = screen.getByLabelText(/timezone/i);
    await user.selectOptions(timezoneSelect, 'Europe/London');

    const saveButton = screen.getByRole('button', { name: /save|update/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(auth.updatePreferences).toHaveBeenCalledWith(
        expect.any(String),
        'Europe/London'
      );
    });
  });

  it('allows currency selection', async () => {
    const user = userEvent.setup();

    (auth.updatePreferences as jest.Mock).mockResolvedValue({
      ...mockUser,
      currency: 'EUR',
    });

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('USD')).toBeInTheDocument();
    });

    // Change currency
    const currencySelect = screen.getByLabelText(/currency/i);
    await user.selectOptions(currencySelect, 'EUR');

    const saveButton = screen.getByRole('button', { name: /save|update/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(auth.updatePreferences).toHaveBeenCalledWith(
        'EUR',
        expect.any(String)
      );
    });
  });
});

describe('Avatar Upload', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('allows uploading new avatar', async () => {
    const user = userEvent.setup();

    (avatars.upload as jest.Mock).mockResolvedValue({
      avatarUrl: 'https://storage.example.com/avatar.jpg',
      expiresAt: new Date(Date.now() + 3600000).toISOString(),
    });

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    // Find file input
    const fileInput = screen.getByLabelText(/avatar|photo|picture/i);
    const file = new File(['test'], 'avatar.jpg', { type: 'image/jpeg' });

    await user.upload(fileInput, file);

    await waitFor(() => {
      expect(avatars.upload).toHaveBeenCalledWith(file);
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });

  it('validates file type for avatar', async () => {
    const user = userEvent.setup();

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    const fileInput = screen.getByLabelText(/avatar|photo|picture/i);
    const invalidFile = new File(['test'], 'document.pdf', { type: 'application/pdf' });

    await user.upload(fileInput, invalidFile);

    await waitFor(() => {
      expect(screen.getByText(/invalid.*file|image.*only|supported.*format/i)).toBeInTheDocument();
    });

    expect(avatars.upload).not.toHaveBeenCalled();
  });

  it('allows removing avatar', async () => {
    const user = userEvent.setup();
    const userWithAvatar = {
      ...mockUser,
      avatar_url: 'https://storage.example.com/avatar.jpg',
    };

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(userWithAvatar);
    (avatars.remove as jest.Mock).mockResolvedValue({});

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(auth.getCurrentUser).toHaveBeenCalled();
    });

    const removeButton = screen.getByRole('button', { name: /remove|delete.*avatar/i });
    await user.click(removeButton);

    // Confirm removal
    const confirmButton = await screen.findByRole('button', { name: /confirm|yes/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(avatars.remove).toHaveBeenCalled();
      expect(toastMocks.showSuccess).toHaveBeenCalled();
    });
  });
});

describe('Notification Settings Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
    (notifications.getPreferences as jest.Mock).mockResolvedValue(mockNotificationPreferences);
  });

  it('loads and displays notification preferences', async () => {
    const NotificationsPage = (await import('@/app/settings/notifications/page')).default;
    render(<NotificationsPage />);

    await waitFor(() => {
      expect(notifications.getPreferences).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText(/notification.*setting/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email.*notification/i)).toBeChecked();
      expect(screen.getByLabelText(/push.*notification/i)).toBeChecked();
      expect(screen.getByLabelText(/sms.*notification/i)).not.toBeChecked();
    });
  });

  it('toggles email notifications', async () => {
    const user = userEvent.setup();

    (notifications.updatePreferences as jest.Mock).mockResolvedValue({
      ...mockNotificationPreferences,
      email_enabled: false,
    });

    const NotificationsPage = (await import('@/app/settings/notifications/page')).default;
    render(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/email.*notification/i)).toBeChecked();
    });

    // Toggle email off
    const emailToggle = screen.getByLabelText(/email.*notification/i);
    await user.click(emailToggle);

    await waitFor(() => {
      expect(notifications.updatePreferences).toHaveBeenCalledWith(
        expect.objectContaining({ email_enabled: false })
      );
    });
  });

  it('updates quiet hours settings', async () => {
    const user = userEvent.setup();

    (notifications.updatePreferences as jest.Mock).mockResolvedValue({
      ...mockNotificationPreferences,
      quiet_hours_start: '23:00',
      quiet_hours_end: '07:00',
    });

    const NotificationsPage = (await import('@/app/settings/notifications/page')).default;
    render(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/quiet.*hours.*start/i)).toBeInTheDocument();
    });

    // Update quiet hours
    const startInput = screen.getByLabelText(/quiet.*hours.*start/i);
    await user.clear(startInput);
    await user.type(startInput, '23:00');

    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(notifications.updatePreferences).toHaveBeenCalledWith(
        expect.objectContaining({ quiet_hours_start: '23:00' })
      );
    });
  });

  it('shows category-specific notification toggles', async () => {
    const NotificationsPage = (await import('@/app/settings/notifications/page')).default;
    render(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByText(/session.*reminder/i)).toBeInTheDocument();
      expect(screen.getByText(/booking.*request/i)).toBeInTheDocument();
      expect(screen.getByText(/review.*prompt/i)).toBeInTheDocument();
      expect(screen.getByText(/achievement/i)).toBeInTheDocument();
    });
  });

  it('handles save error gracefully', async () => {
    const user = userEvent.setup();

    (notifications.updatePreferences as jest.Mock).mockRejectedValue(
      new Error('Failed to save preferences')
    );

    const NotificationsPage = (await import('@/app/settings/notifications/page')).default;
    render(<NotificationsPage />);

    await waitFor(() => {
      expect(screen.getByLabelText(/email.*notification/i)).toBeInTheDocument();
    });

    const emailToggle = screen.getByLabelText(/email.*notification/i);
    await user.click(emailToggle);

    await waitFor(() => {
      expect(toastMocks.showError).toHaveBeenCalled();
    });
  });
});

describe('Privacy Settings Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('renders privacy settings options', async () => {
    const PrivacyPage = (await import('@/app/settings/privacy/page')).default;
    render(<PrivacyPage />);

    await waitFor(() => {
      expect(screen.getByText(/privacy.*setting/i)).toBeInTheDocument();
      expect(screen.getByText(/profile.*visibility/i)).toBeInTheDocument();
    });
  });

  it('displays data export option', async () => {
    const PrivacyPage = (await import('@/app/settings/privacy/page')).default;
    render(<PrivacyPage />);

    await waitFor(() => {
      expect(screen.getByText(/export.*data|download.*data/i)).toBeInTheDocument();
    });
  });

  it('shows account deletion warning', async () => {
    const PrivacyPage = (await import('@/app/settings/privacy/page')).default;
    render(<PrivacyPage />);

    await waitFor(() => {
      expect(screen.getByText(/delete.*account/i)).toBeInTheDocument();
      expect(screen.getByText(/permanent|cannot.*undo/i)).toBeInTheDocument();
    });
  });
});

describe('Danger Zone Settings', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('renders danger zone with warnings', async () => {
    const DangerPage = (await import('@/app/settings/danger/page')).default;
    render(<DangerPage />);

    await waitFor(() => {
      expect(screen.getByText(/danger.*zone/i)).toBeInTheDocument();
      expect(screen.getByText(/delete.*account/i)).toBeInTheDocument();
    });
  });

  it('requires confirmation for account deletion', async () => {
    const user = userEvent.setup();

    const DangerPage = (await import('@/app/settings/danger/page')).default;
    render(<DangerPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete.*account/i })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete.*account/i });
    await user.click(deleteButton);

    // Should show confirmation modal
    await waitFor(() => {
      expect(screen.getByText(/are.*sure|confirm.*deletion/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/type.*confirm|enter.*email/i)).toBeInTheDocument();
    });
  });

  it('prevents deletion without proper confirmation', async () => {
    const user = userEvent.setup();

    const DangerPage = (await import('@/app/settings/danger/page')).default;
    render(<DangerPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete.*account/i })).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete.*account/i });
    await user.click(deleteButton);

    // Try to confirm without typing
    const confirmDeleteButton = await screen.findByRole('button', { name: /confirm.*delete|delete.*permanently/i });
    expect(confirmDeleteButton).toBeDisabled();
  });
});

describe('Settings Navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  });

  it('renders settings sidebar with navigation links', async () => {
    const SettingsPage = (await import('@/app/settings/page')).default;
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/account/i)).toBeInTheDocument();
      expect(screen.getByText(/notification/i)).toBeInTheDocument();
      expect(screen.getByText(/privacy/i)).toBeInTheDocument();
    });
  });

  it('highlights active settings section', async () => {
    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      const accountLink = screen.getByRole('link', { name: /account/i });
      expect(accountLink).toHaveClass(/active|selected|current/i);
    });
  });

  it('navigates between settings sections', async () => {
    const user = userEvent.setup();

    const SettingsPage = (await import('@/app/settings/page')).default;
    render(<SettingsPage />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /notification/i })).toBeInTheDocument();
    });

    const notificationLink = screen.getByRole('link', { name: /notification/i });
    expect(notificationLink).toHaveAttribute('href', expect.stringContaining('notification'));
  });
});

describe('Settings Loading and Error States', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');
  });

  it('shows loading state during data fetch', async () => {
    (auth.getCurrentUser as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 500))
    );

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    expect(screen.getByTestId('loading-spinner') || screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    });
  });

  it('shows error message when settings fail to load', async () => {
    (auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Failed to load'));

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByText(/error|failed.*load/i)).toBeInTheDocument();
    });
  });

  it('shows save indicator during update', async () => {
    const user = userEvent.setup();

    (auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
    (auth.updateUser as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockUser), 500))
    );

    const AccountPage = (await import('@/app/settings/account/page')).default;
    render(<AccountPage />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    });

    const saveButton = screen.getByRole('button', { name: /save|update/i });
    await user.click(saveButton);

    expect(screen.getByText(/saving|updating/i)).toBeInTheDocument();
  });
});
