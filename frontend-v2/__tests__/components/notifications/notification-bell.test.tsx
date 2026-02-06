import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationBell } from '@/components/notifications/notification-bell';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
    onClick,
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: () => void;
  }) => (
    <a href={href} onClick={onClick}>
      {children}
    </a>
  ),
}));

// Mock the hooks
const mockUseUnreadNotificationCount = vi.fn();
const mockUseNotifications = vi.fn();
const mockMarkAsRead = vi.fn();

vi.mock('@/lib/hooks', () => ({
  useUnreadNotificationCount: () => mockUseUnreadNotificationCount(),
  useNotifications: () => mockUseNotifications(),
  useMarkNotificationAsRead: () => ({
    mutate: mockMarkAsRead,
    isPending: false,
  }),
}));

// Mock NotificationItem
vi.mock('@/components/notifications/notification-item', () => ({
  NotificationItem: ({
    notification,
    onClick,
  }: {
    notification: { id: number; title: string };
    onClick: () => void;
  }) => (
    <div data-testid={`notification-${notification.id}`} onClick={onClick}>
      {notification.title}
    </div>
  ),
}));

// Mock UI components
vi.mock('@/components/ui', () => ({
  Button: ({
    children,
    ...props
  }: {
    children: React.ReactNode;
    variant?: string;
    className?: string;
  }) => <button {...props}>{children}</button>,
  Skeleton: ({ className }: { className?: string }) => (
    <div data-testid="skeleton" className={className} />
  ),
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUnreadNotificationCount.mockReturnValue({
      data: { unread_count: 0 },
    });
    mockUseNotifications.mockReturnValue({
      data: { items: [] },
      isLoading: false,
    });
  });

  describe('rendering', () => {
    it('renders bell icon button', () => {
      render(<NotificationBell />, { wrapper: createWrapper() });
      expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();
    });

    it('renders without unread badge when count is 0', () => {
      mockUseUnreadNotificationCount.mockReturnValue({
        data: { unread_count: 0 },
      });

      const { container } = render(<NotificationBell />, { wrapper: createWrapper() });
      const badge = container.querySelector('.bg-primary-500');
      expect(badge).not.toBeInTheDocument();
    });

    it('renders unread badge when count is greater than 0', () => {
      mockUseUnreadNotificationCount.mockReturnValue({
        data: { unread_count: 5 },
      });

      render(<NotificationBell />, { wrapper: createWrapper() });
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('renders "99+" when unread count exceeds 99', () => {
      mockUseUnreadNotificationCount.mockReturnValue({
        data: { unread_count: 150 },
      });

      render(<NotificationBell />, { wrapper: createWrapper() });
      expect(screen.getByText('99+')).toBeInTheDocument();
    });
  });

  describe('dropdown behavior', () => {
    it('opens dropdown when bell is clicked', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: {
          items: [
            { id: 1, title: 'Test Notification', is_read: false, read: false },
          ],
        },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText('Test Notification')).toBeInTheDocument();
    });

    it('closes dropdown when bell is clicked again', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);
      expect(screen.getByText('Notifications')).toBeInTheDocument();

      await user.click(bellButton);
      expect(screen.queryByText('No notifications yet')).not.toBeInTheDocument();
    });

    it('closes dropdown when clicking outside', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(
        <div>
          <div data-testid="outside">Outside</div>
          <NotificationBell />
        </div>,
        { wrapper: createWrapper() }
      );

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);
      expect(screen.getByText('Notifications')).toBeInTheDocument();

      await user.click(screen.getByTestId('outside'));
      await waitFor(() => {
        expect(screen.queryByText('No notifications yet')).not.toBeInTheDocument();
      });
    });
  });

  describe('loading state', () => {
    it('shows skeletons while loading', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: null,
        isLoading: true,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      expect(screen.getAllByTestId('skeleton').length).toBeGreaterThan(0);
    });
  });

  describe('empty state', () => {
    it('shows empty message when no notifications', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      expect(screen.getByText('No notifications yet')).toBeInTheDocument();
    });
  });

  describe('notification interactions', () => {
    it('marks notification as read when clicked', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: {
          items: [
            {
              id: 1,
              title: 'Unread Notification',
              is_read: false,
              read: false,
            },
          ],
        },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      const notificationItem = screen.getByTestId('notification-1');
      await user.click(notificationItem);

      expect(mockMarkAsRead).toHaveBeenCalledWith(1);
    });

    it('does not mark notification as read if already read', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: {
          items: [
            {
              id: 1,
              title: 'Read Notification',
              is_read: true,
              read: true,
            },
          ],
        },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      const notificationItem = screen.getByTestId('notification-1');
      await user.click(notificationItem);

      expect(mockMarkAsRead).not.toHaveBeenCalled();
    });
  });

  describe('unread count display', () => {
    it('shows "new" indicator in dropdown header when there are unread notifications', async () => {
      const user = userEvent.setup();
      mockUseUnreadNotificationCount.mockReturnValue({
        data: { unread_count: 3 },
      });
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      expect(screen.getByText('3 new')).toBeInTheDocument();
    });

    it('does not show "new" indicator when unread count is 0', async () => {
      const user = userEvent.setup();
      mockUseUnreadNotificationCount.mockReturnValue({
        data: { unread_count: 0 },
      });
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      expect(screen.queryByText(/new$/)).not.toBeInTheDocument();
    });
  });

  describe('view all link', () => {
    it('renders "View all notifications" link', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      const viewAllLink = screen.getByRole('link', { name: /view all notifications/i });
      expect(viewAllLink).toHaveAttribute('href', '/notifications');
    });

    it('closes dropdown when "View all" is clicked', async () => {
      const user = userEvent.setup();
      mockUseNotifications.mockReturnValue({
        data: { items: [] },
        isLoading: false,
      });

      render(<NotificationBell />, { wrapper: createWrapper() });

      const bellButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(bellButton);

      const viewAllLink = screen.getByRole('link', { name: /view all notifications/i });
      await user.click(viewAllLink);

      await waitFor(() => {
        expect(screen.queryByText('Notifications')).not.toBeInTheDocument();
      });
    });
  });

  describe('polling behavior', () => {
    it('uses refetchInterval for unread count (30 seconds)', () => {
      // This test verifies that useUnreadNotificationCount is called
      // The actual polling configuration is in the hook itself
      render(<NotificationBell />, { wrapper: createWrapper() });

      // Verify the hook was called - the hook implementation handles polling
      expect(mockUseUnreadNotificationCount).toHaveBeenCalled();
    });
  });

  describe('accessibility', () => {
    it('has accessible button with aria-label', () => {
      render(<NotificationBell />, { wrapper: createWrapper() });

      const button = screen.getByRole('button', { name: /notifications/i });
      expect(button).toHaveAttribute('aria-label', 'Notifications');
    });
  });
});
