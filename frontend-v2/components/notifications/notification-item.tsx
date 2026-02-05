'use client';

import Link from 'next/link';
import {
  Bell,
  Calendar,
  CheckCircle,
  XCircle,
  MessageCircle,
  Star,
  CreditCard,
  Info,
} from 'lucide-react';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { Notification, NotificationType } from '@/types/notification';

interface NotificationItemProps {
  notification: Notification;
  onClick?: () => void;
}

const typeIcons: Record<NotificationType, React.ReactNode> = {
  booking_request: <Calendar className="h-5 w-5 text-primary-500" />,
  booking_confirmed: <CheckCircle className="h-5 w-5 text-green-500" />,
  booking_cancelled: <XCircle className="h-5 w-5 text-red-500" />,
  message: <MessageCircle className="h-5 w-5 text-blue-500" />,
  review: <Star className="h-5 w-5 text-amber-500" />,
  payment: <CreditCard className="h-5 w-5 text-purple-500" />,
  system: <Info className="h-5 w-5 text-slate-500" />,
};

const typeColors: Record<NotificationType, string> = {
  booking_request: 'bg-primary-50 dark:bg-primary-900/20',
  booking_confirmed: 'bg-green-50 dark:bg-green-900/20',
  booking_cancelled: 'bg-red-50 dark:bg-red-900/20',
  message: 'bg-blue-50 dark:bg-blue-900/20',
  review: 'bg-amber-50 dark:bg-amber-900/20',
  payment: 'bg-purple-50 dark:bg-purple-900/20',
  system: 'bg-slate-50 dark:bg-slate-800/50',
};

export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const timeAgo = formatRelativeTime(notification.created_at);

  // Support both is_read and read for backward compatibility
  const isRead = notification.is_read ?? notification.read ?? false;

  const content = (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-xl transition-colors',
        'hover:bg-slate-50 dark:hover:bg-slate-800/50',
        !isRead && 'bg-slate-50/50 dark:bg-slate-800/30'
      )}
      onClick={onClick}
    >
      <div
        className={cn(
          'shrink-0 p-2 rounded-lg',
          typeColors[notification.type as NotificationType]
        )}
      >
        {typeIcons[notification.type as NotificationType] || <Bell className="h-5 w-5 text-slate-500" />}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p
            className={cn(
              'text-sm text-slate-900 dark:text-white',
              !isRead && 'font-semibold'
            )}
          >
            {notification.title}
          </p>
          <div className="flex items-center gap-2 shrink-0">
            {!isRead && (
              <span className="h-2 w-2 rounded-full bg-primary-500" />
            )}
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {timeAgo}
            </span>
          </div>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
          {notification.message}
        </p>
      </div>
    </div>
  );

  if (notification.action_url) {
    return (
      <Link href={notification.action_url} className="block">
        {content}
      </Link>
    );
  }

  return content;
}
