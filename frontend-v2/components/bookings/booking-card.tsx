'use client';

import Link from 'next/link';
import { Calendar, Clock, User } from 'lucide-react';
import { Card, CardContent, Button, Avatar } from '@/components/ui';
import { BookingStatusBadge } from './booking-status-badge';
import { formatDate, formatTime, formatCurrency } from '@/lib/utils';
import type { Booking } from '@/types';

interface BookingCardProps {
  booking: Booking;
  userRole?: 'student' | 'tutor';
  onCancel?: (id: number) => void;
  onConfirm?: (id: number) => void;
}

export function BookingCard({
  booking,
  userRole = 'student',
  onCancel,
  onConfirm,
}: BookingCardProps) {
  const displayName =
    userRole === 'student'
      ? booking.tutor?.name ?? 'Tutor'
      : booking.student?.name ?? 'Student';

  const avatarUrl = userRole === 'student' ? booking.tutor?.avatar_url : undefined;

  const canCancel = (['REQUESTED', 'SCHEDULED'] as string[]).includes(booking.session_state);

  // Tutor confirms REQUESTED -> SCHEDULED
  const canConfirm =
    userRole === 'tutor' && booking.session_state === 'REQUESTED';

  return (
    <Card hover className="transition-all">
      <CardContent className="p-3 sm:p-4">
        <div className="flex items-start gap-3 sm:gap-4">
          <Avatar src={avatarUrl} name={displayName} size="lg" className="shrink-0" />

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="font-semibold text-slate-900 dark:text-white truncate">
                  {booking.subject_name ?? 'Session'}
                </h3>
                <p className="text-sm text-slate-500 flex items-center gap-1 truncate">
                  <User className="h-3 w-3 shrink-0" />
                  {displayName}
                </p>
              </div>
              <BookingStatusBadge status={booking.session_state} />
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-600 dark:text-slate-400">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4 shrink-0" />
                {formatDate(booking.start_at)}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4 shrink-0" />
                {formatTime(booking.start_at)} - {formatTime(booking.end_at)}
              </span>
              <span className="font-medium text-slate-900 dark:text-white">
                {formatCurrency(booking.rate_cents / 100, booking.currency)}
              </span>
            </div>

            <div className="mt-3 sm:mt-4 flex items-center gap-2 flex-wrap">
              <Button asChild size="sm" variant="outline">
                <Link href={`/bookings/${booking.id}`}>View Details</Link>
              </Button>

              {canConfirm && onConfirm && (
                <Button size="sm" onClick={() => onConfirm(booking.id)}>
                  Confirm
                </Button>
              )}

              {canCancel && onCancel && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={() => onCancel(booking.id)}
                >
                  Cancel
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
