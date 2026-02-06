import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { NotificationItem } from '@/components/notifications/notification-item';
import type { Notification, NotificationType } from '@/types/notification';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

// Mock formatRelativeTime
vi.mock('@/lib/utils', async () => {
  const actual = await vi.importActual('@/lib/utils');
  return {
    ...actual,
    formatRelativeTime: vi.fn().mockReturnValue('5m ago'),
  };
});

describe('NotificationItem', () => {
  const createNotification = (overrides: Partial<Notification> = {}): Notification => {
    // Sync is_read and read fields - is_read takes priority
    const isRead = overrides.is_read ?? overrides.read ?? false;
    const { is_read: _, read: __, ...restOverrides } = overrides;
    return {
      id: 1,
      type: 'message',
      title: 'New message',
      message: 'You have received a new message',
      is_read: isRead,
      read: isRead,
      created_at: new Date().toISOString(),
      ...restOverrides,
    };
  };

  describe('different notification types', () => {
    const notificationTypes: NotificationType[] = [
      'booking_request',
      'booking_confirmed',
      'booking_cancelled',
      'message',
      'review',
      'payment',
      'system',
    ];

    it.each(notificationTypes)('renders %s notification type correctly', (type) => {
      const notification = createNotification({ type });
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText(notification.title)).toBeInTheDocument();
      expect(screen.getByText(notification.message)).toBeInTheDocument();
    });

    it('renders booking_request with calendar icon styling', () => {
      const notification = createNotification({ type: 'booking_request' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-primary-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders booking_confirmed with green styling', () => {
      const notification = createNotification({ type: 'booking_confirmed' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-green-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders booking_cancelled with red styling', () => {
      const notification = createNotification({ type: 'booking_cancelled' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-red-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders message type with blue styling', () => {
      const notification = createNotification({ type: 'message' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-blue-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders review type with amber styling', () => {
      const notification = createNotification({ type: 'review' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-amber-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders payment type with purple styling', () => {
      const notification = createNotification({ type: 'payment' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-purple-50');
      expect(iconContainer).toBeInTheDocument();
    });

    it('renders system type with slate styling', () => {
      const notification = createNotification({ type: 'system' });
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.bg-slate-50');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('read/unread states', () => {
    it('shows unread indicator when notification is unread', () => {
      const notification = createNotification({ read: false });
      const { container } = render(<NotificationItem notification={notification} />);

      const unreadIndicator = container.querySelector('.bg-primary-500');
      expect(unreadIndicator).toBeInTheDocument();
    });

    it('hides unread indicator when notification is read', () => {
      const notification = createNotification({ read: true });
      const { container } = render(<NotificationItem notification={notification} />);

      const unreadIndicator = container.querySelector('.h-2.w-2.rounded-full.bg-primary-500');
      expect(unreadIndicator).not.toBeInTheDocument();
    });

    it('applies bold text style for unread notifications', () => {
      const notification = createNotification({ read: false });
      render(<NotificationItem notification={notification} />);

      const title = screen.getByText(notification.title);
      expect(title).toHaveClass('font-semibold');
    });

    it('does not apply bold text style for read notifications', () => {
      const notification = createNotification({ read: true });
      render(<NotificationItem notification={notification} />);

      const title = screen.getByText(notification.title);
      expect(title).not.toHaveClass('font-semibold');
    });

    it('applies background highlight for unread notifications', () => {
      const notification = createNotification({ read: false });
      const { container } = render(<NotificationItem notification={notification} />);

      const contentDiv = container.querySelector('.bg-slate-50\\/50');
      expect(contentDiv).toBeInTheDocument();
    });
  });

  describe('content display', () => {
    it('displays notification title', () => {
      const notification = createNotification({ title: 'Test Title' });
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('displays notification message', () => {
      const notification = createNotification({
        message: 'This is a test message',
      });
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText('This is a test message')).toBeInTheDocument();
    });

    it('displays relative time', () => {
      const notification = createNotification();
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });

    it('truncates long messages with line-clamp', () => {
      const notification = createNotification({
        message: 'A'.repeat(500),
      });
      const { container } = render(<NotificationItem notification={notification} />);

      const messageElement = container.querySelector('.line-clamp-2');
      expect(messageElement).toBeInTheDocument();
    });
  });

  describe('action buttons and click handlers', () => {
    it('calls onClick when notification is clicked', async () => {
      const user = userEvent.setup();
      const onClick = vi.fn();
      const notification = createNotification();

      render(<NotificationItem notification={notification} onClick={onClick} />);

      const notificationContent = screen.getByText(notification.title).closest('div');
      if (notificationContent) {
        await user.click(notificationContent);
        expect(onClick).toHaveBeenCalled();
      }
    });

    it('renders as a link when action_url is provided', () => {
      const notification = createNotification({
        action_url: '/bookings/123',
      });
      render(<NotificationItem notification={notification} />);

      const link = screen.getByRole('link');
      expect(link).toHaveAttribute('href', '/bookings/123');
    });

    it('does not render as a link when action_url is not provided', () => {
      const notification = createNotification({ action_url: undefined });
      render(<NotificationItem notification={notification} />);

      expect(screen.queryByRole('link')).not.toBeInTheDocument();
    });

    it('link wraps entire notification content', () => {
      const notification = createNotification({
        action_url: '/messages/456',
      });
      render(<NotificationItem notification={notification} />);

      const link = screen.getByRole('link');
      expect(link).toContainElement(screen.getByText(notification.title));
      expect(link).toContainElement(screen.getByText(notification.message));
    });
  });

  describe('icons for notification types', () => {
    it('displays icon for each notification type', () => {
      const types: NotificationType[] = [
        'booking_request',
        'booking_confirmed',
        'booking_cancelled',
        'message',
        'review',
        'payment',
        'system',
      ];

      types.forEach((type) => {
        const notification = createNotification({ type });
        const { container, unmount } = render(
          <NotificationItem notification={notification} />
        );

        const svg = container.querySelector('svg');
        expect(svg).toBeInTheDocument();

        unmount();
      });
    });

    it('booking_confirmed has green icon color', () => {
      const notification = createNotification({ type: 'booking_confirmed' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-green-500');
      expect(icon).toBeInTheDocument();
    });

    it('booking_cancelled has red icon color', () => {
      const notification = createNotification({ type: 'booking_cancelled' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-red-500');
      expect(icon).toBeInTheDocument();
    });

    it('message has blue icon color', () => {
      const notification = createNotification({ type: 'message' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-blue-500');
      expect(icon).toBeInTheDocument();
    });

    it('review has amber icon color', () => {
      const notification = createNotification({ type: 'review' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-amber-500');
      expect(icon).toBeInTheDocument();
    });

    it('payment has purple icon color', () => {
      const notification = createNotification({ type: 'payment' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-purple-500');
      expect(icon).toBeInTheDocument();
    });

    it('system has slate icon color', () => {
      const notification = createNotification({ type: 'system' });
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('.text-slate-500');
      expect(icon).toBeInTheDocument();
    });
  });

  describe('styling', () => {
    it('has hover state styling', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const contentDiv = container.querySelector('.hover\\:bg-slate-50');
      expect(contentDiv).toBeInTheDocument();
    });

    it('has rounded corners', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const contentDiv = container.querySelector('.rounded-xl');
      expect(contentDiv).toBeInTheDocument();
    });

    it('has proper padding', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const contentDiv = container.querySelector('.p-4');
      expect(contentDiv).toBeInTheDocument();
    });

    it('has flex layout with gap', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const contentDiv = container.querySelector('.flex.items-start.gap-3');
      expect(contentDiv).toBeInTheDocument();
    });

    it('icon container has shrink-0 class', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const iconContainer = container.querySelector('.shrink-0.p-2.rounded-lg');
      expect(iconContainer).toBeInTheDocument();
    });
  });

  describe('timestamp display', () => {
    it('displays formatted relative time', () => {
      const notification = createNotification();
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText('5m ago')).toBeInTheDocument();
    });

    it('timestamp has correct styling', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const timestamp = screen.getByText('5m ago');
      expect(timestamp).toHaveClass('text-xs', 'text-slate-500');
    });
  });

  describe('accessibility', () => {
    it('notification content is accessible', () => {
      const notification = createNotification();
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText(notification.title)).toBeInTheDocument();
      expect(screen.getByText(notification.message)).toBeInTheDocument();
    });

    it('link is accessible when action_url is provided', () => {
      const notification = createNotification({
        action_url: '/test-url',
      });
      render(<NotificationItem notification={notification} />);

      const link = screen.getByRole('link');
      expect(link).toBeInTheDocument();
    });

    it('icons have proper sizing for visibility', () => {
      const notification = createNotification();
      const { container } = render(<NotificationItem notification={notification} />);

      const icon = container.querySelector('svg');
      expect(icon).toHaveClass('h-5', 'w-5');
    });
  });

  describe('edge cases', () => {
    it('handles very long title gracefully', () => {
      const notification = createNotification({
        title: 'A'.repeat(200),
      });
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText('A'.repeat(200))).toBeInTheDocument();
    });

    it('handles empty message', () => {
      const notification = createNotification({ message: '' });
      render(<NotificationItem notification={notification} />);

      expect(screen.getByText(notification.title)).toBeInTheDocument();
    });

    it('handles special characters in title and message', () => {
      const notification = createNotification({
        title: 'Test <script>alert("xss")</script>',
        message: 'Message with "quotes" & ampersand',
      });
      render(<NotificationItem notification={notification} />);

      expect(
        screen.getByText('Test <script>alert("xss")</script>')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Message with "quotes" & ampersand')
      ).toBeInTheDocument();
    });
  });
});
