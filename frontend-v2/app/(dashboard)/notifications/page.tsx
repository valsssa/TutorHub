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

  const notifications = apiData?.items ?? [];
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
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
            Notifications
          </h1>
          <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400">
            Stay updated with your tutoring activity
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            variant="outline"
            onClick={handleMarkAllAsRead}
            disabled={markAllAsRead.isPending}
            className="self-start sm:self-auto"
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
          <div className="flex gap-2 overflow-x-auto pb-1 sm:pb-0 sm:flex-wrap scrollbar-none -mx-1 px-1">
            {filterOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedFilter(option.value)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors whitespace-nowrap flex-shrink-0 ${
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
