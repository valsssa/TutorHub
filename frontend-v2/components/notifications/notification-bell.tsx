'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNotifications, useUnreadNotificationCount, useMarkNotificationAsRead } from '@/lib/hooks';
import { NotificationItem } from './notification-item';
import { Button, Skeleton } from '@/components/ui';

export function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const { data: countData } = useUnreadNotificationCount();
  const { data: notificationsData, isLoading } = useNotifications({ page_size: 5 });
  const markAsRead = useMarkNotificationAsRead();

  const unreadCount = countData?.unread_count ?? 0;
  const notifications = notificationsData?.items ?? [];

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNotificationClick = (id: number, read: boolean) => {
    if (!read) {
      markAsRead.mutate(id);
    }
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'relative p-2 rounded-lg transition-colors',
          'text-slate-600 hover:text-slate-900 hover:bg-slate-100',
          'dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800',
          isOpen && 'bg-slate-100 dark:bg-slate-800'
        )}
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 min-w-[1.25rem] flex items-center justify-center px-1 text-xs font-medium text-white bg-primary-500 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden z-50">
          <div className="flex items-center justify-between p-4 border-b border-slate-100 dark:border-slate-800">
            <h3 className="font-semibold text-slate-900 dark:text-white">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <span className="text-xs font-medium text-primary-600 dark:text-primary-400">
                {unreadCount} new
              </span>
            )}
          </div>

          <div className="max-h-[400px] overflow-y-auto">
            {isLoading ? (
              <div className="p-4 space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Skeleton className="h-9 w-9 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <Bell className="h-10 w-10 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  No notifications yet
                </p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {notifications.map((notification) => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClick={() => handleNotificationClick(notification.id, notification.read ?? notification.is_read ?? false)}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="p-3 border-t border-slate-100 dark:border-slate-800">
            <Link href="/notifications" onClick={() => setIsOpen(false)}>
              <Button variant="ghost" className="w-full">
                View all notifications
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
