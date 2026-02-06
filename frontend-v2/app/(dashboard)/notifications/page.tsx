'use client';

import { useState, useMemo } from 'react';
import { Bell, CheckCheck, Filter } from 'lucide-react';
import {
  useNotifications,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
  useUnreadNotificationCount,
} from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Skeleton,
  Badge,
} from '@/components/ui';
import { NotificationItem } from '@/components/notifications';
import type { Notification, NotificationType } from '@/types/notification';

const mockNotifications: Notification[] = [
  {
    id: 1,
    type: 'booking_request',
    title: 'New Booking Request',
    message: 'John Doe has requested a tutoring session for Mathematics on Feb 15.',
    is_read: false,
    read: false,
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    action_url: '/bookings',
  },
  {
    id: 2,
    type: 'message',
    title: 'New Message',
    message: 'Sarah Williams sent you a message: "Hi! I have a question about..."',
    is_read: false,
    read: false,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    action_url: '/messages/1',
  },
  {
    id: 3,
    type: 'booking_confirmed',
    title: 'Booking Confirmed',
    message: 'Your tutoring session with Michael Chen has been confirmed for Feb 14.',
    is_read: true,
    read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    action_url: '/bookings',
  },
  {
    id: 4,
    type: 'payment',
    title: 'Payment Received',
    message: 'You received a payment of $50.00 for your tutoring session.',
    is_read: true,
    read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    action_url: '/wallet',
  },
  {
    id: 5,
    type: 'review',
    title: 'New Review',
    message: 'Emily Johnson left you a 5-star review!',
    is_read: true,
    read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
  },
  {
    id: 6,
    type: 'booking_cancelled',
    title: 'Booking Cancelled',
    message: 'Your session scheduled for Feb 10 has been cancelled by the student.',
    is_read: true,
    read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
  },
  {
    id: 7,
    type: 'system',
    title: 'Profile Update Reminder',
    message: 'Complete your profile to attract more students and get more bookings.',
    is_read: true,
    read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
    action_url: '/profile',
  },
];

const filterOptions: { value: NotificationType | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'booking_request', label: 'Booking Requests' },
  { value: 'booking_confirmed', label: 'Confirmed' },
  { value: 'booking_cancelled', label: 'Cancelled' },
  { value: 'message', label: 'Messages' },
  { value: 'review', label: 'Reviews' },
  { value: 'payment', label: 'Payments' },
  { value: 'system', label: 'System' },
];

function NotificationSkeleton() {
  return (
    <div className="flex items-start gap-3 p-4">
      <Skeleton className="h-9 w-9 rounded-lg" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
}

function groupNotificationsByDate(notifications: Notification[]) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  const groups: { label: string; notifications: Notification[] }[] = [
    { label: 'Today', notifications: [] },
    { label: 'Yesterday', notifications: [] },
    { label: 'Earlier', notifications: [] },
  ];

  notifications.forEach((notification) => {
    const date = new Date(notification.created_at);
    date.setHours(0, 0, 0, 0);

    if (date.getTime() === today.getTime()) {
      groups[0].notifications.push(notification);
    } else if (date.getTime() === yesterday.getTime()) {
      groups[1].notifications.push(notification);
    } else {
      groups[2].notifications.push(notification);
    }
  });

  return groups.filter((group) => group.notifications.length > 0);
}

export default function NotificationsPage() {
  const [selectedFilter, setSelectedFilter] = useState<NotificationType | 'all'>('all');

  const { data: apiData, isLoading } = useNotifications(
    selectedFilter === 'all' ? undefined : { type: selectedFilter }
  );
  const { data: countData } = useUnreadNotificationCount();
  const markAsRead = useMarkNotificationAsRead();
  const markAllAsRead = useMarkAllNotificationsAsRead();

  const notifications = apiData?.items ?? mockNotifications;
  const unreadCount = countData?.unread_count ?? notifications.filter((n) => !n.read).length;

  const filteredNotifications = useMemo(() => {
    if (selectedFilter === 'all') return notifications;
    return notifications.filter((n) => n.type === selectedFilter);
  }, [notifications, selectedFilter]);

  const groupedNotifications = useMemo(
    () => groupNotificationsByDate(filteredNotifications),
    [filteredNotifications]
  );

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.read) {
      markAsRead.mutate(notification.id);
    }
  };

  const handleMarkAllAsRead = () => {
    markAllAsRead.mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Notifications
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            Stay updated with your tutoring activity
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            onClick={handleMarkAllAsRead}
            disabled={markAllAsRead.isPending}
          >
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark all as read
          </Button>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filter
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedFilter(option.value)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  selectedFilter === option.value
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>All Notifications</span>
            {unreadCount > 0 && (
              <Badge variant="primary">{unreadCount} unread</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              <NotificationSkeleton />
              <NotificationSkeleton />
              <NotificationSkeleton />
              <NotificationSkeleton />
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="text-center py-12">
              <Bell className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
              <p className="text-slate-500 dark:text-slate-400">
                {selectedFilter === 'all'
                  ? 'No notifications yet'
                  : `No ${filterOptions.find((o) => o.value === selectedFilter)?.label.toLowerCase()} notifications`}
              </p>
              <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
                You will see notifications for bookings, messages, and more here
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {groupedNotifications.map((group) => (
                <div key={group.label}>
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-2 px-1">
                    {group.label}
                  </h3>
                  <div className="divide-y divide-slate-100 dark:divide-slate-800 rounded-xl border border-slate-100 dark:border-slate-800 overflow-hidden">
                    {group.notifications.map((notification) => (
                      <NotificationItem
                        key={notification.id}
                        notification={notification}
                        onClick={() => handleNotificationClick(notification)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
