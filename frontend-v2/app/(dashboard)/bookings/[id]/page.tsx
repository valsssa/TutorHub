'use client';

import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Calendar,
  Clock,
  MessageSquare,
  Video,
  DollarSign,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import {
  useBooking,
  useCancelBooking,
  useConfirmBooking,
  useAuth,
} from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  Avatar,
  Skeleton,
} from '@/components/ui';
import { BookingStatusBadge } from '@/components/bookings';
import { formatDate, formatTime, formatCurrency } from '@/lib/utils';
import type { SessionState } from '@/types';

interface TimelineStep {
  label: string;
  status: 'completed' | 'current' | 'upcoming';
  icon: React.ElementType;
}

function getTimeline(sessionState: SessionState): TimelineStep[] {
  const steps: TimelineStep[] = [
    { label: 'Requested', status: 'completed', icon: CheckCircle },
    { label: 'Confirmed', status: 'upcoming', icon: CheckCircle },
    { label: 'In Progress', status: 'upcoming', icon: Video },
    { label: 'Completed', status: 'upcoming', icon: CheckCircle },
  ];

  switch (sessionState) {
    case 'REQUESTED':
      steps[0].status = 'completed';
      steps[1].status = 'current';
      break;
    case 'SCHEDULED':
      steps[0].status = 'completed';
      steps[1].status = 'completed';
      steps[2].status = 'current';
      break;
    case 'ACTIVE':
      steps[0].status = 'completed';
      steps[1].status = 'completed';
      steps[2].status = 'current';
      break;
    case 'ENDED':
      steps.forEach((s) => (s.status = 'completed'));
      break;
    case 'CANCELLED':
    case 'EXPIRED':
      steps[0].status = 'completed';
      steps[1] = { label: 'Cancelled', status: 'completed', icon: XCircle };
      steps.splice(2);
      break;
  }

  return steps;
}

export default function BookingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const bookingId = Number(params.id);

  const { data: booking, isLoading } = useBooking(bookingId);
  const cancelBooking = useCancelBooking();
  const confirmBooking = useConfirmBooking();

  const handleCancel = () => {
    if (window.confirm('Are you sure you want to cancel this booking?')) {
      cancelBooking.mutate(
        { id: bookingId },
        {
          onSuccess: () => router.push('/bookings'),
        }
      );
    }
  };

  const handleConfirm = () => {
    confirmBooking.mutate(bookingId);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Card>
          <CardContent className="p-6">
            <div className="flex gap-6">
              <Skeleton className="h-24 w-24 rounded-full" />
              <div className="flex-1 space-y-3">
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">Booking not found</p>
        <Button asChild variant="link" className="mt-2">
          <Link href="/bookings">Back to bookings</Link>
        </Button>
      </div>
    );
  }

  const timeline = getTimeline(booking.session_state);
  const userRole = user?.role === 'tutor' ? 'tutor' : 'student';
  const canCancel = ['REQUESTED', 'SCHEDULED'].includes(
    booking.session_state
  );
  const canConfirm =
    userRole === 'tutor' && booking.session_state === 'REQUESTED';
  const canReschedule =
    ['REQUESTED', 'SCHEDULED'].includes(
      booking.session_state
    );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link href="/bookings">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Booking Details
          </h1>
          <p className="text-slate-500">#{booking.id}</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Session Information</CardTitle>
              <BookingStatusBadge status={booking.session_state} />
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-start gap-4">
                <Avatar
                  src={booking.tutor?.avatar_url}
                  name={booking.tutor?.name}
                  size="xl"
                />
                <div>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                    {booking.subject_name ?? 'Session'}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    with {booking.tutor?.name ?? 'Tutor'}
                  </p>
                  {booking.tutor?.title && (
                    <p className="text-sm text-slate-500 mt-1">
                      {booking.tutor.title}
                    </p>
                  )}
                </div>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <Calendar className="h-5 w-5 text-primary-600" />
                  <div>
                    <p className="text-sm text-slate-500">Date</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {formatDate(booking.start_at, {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <Clock className="h-5 w-5 text-primary-600" />
                  <div>
                    <p className="text-sm text-slate-500">Time</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {formatTime(booking.start_at)} - {formatTime(booking.end_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <Video className="h-5 w-5 text-primary-600" />
                  <div>
                    <p className="text-sm text-slate-500">Location</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      Online Session
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <DollarSign className="h-5 w-5 text-primary-600" />
                  <div>
                    <p className="text-sm text-slate-500">Total</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {formatCurrency(booking.rate_cents / 100, booking.currency)}
                    </p>
                  </div>
                </div>
              </div>

              {booking.notes_student && (
                <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Message to tutor
                  </p>
                  <p className="text-slate-600 dark:text-slate-400">
                    {booking.notes_student}
                  </p>
                </div>
              )}
            </CardContent>
            <CardFooter className="gap-2">
              {canConfirm && (
                <Button onClick={handleConfirm} loading={confirmBooking.isPending}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Confirm Booking
                </Button>
              )}

              {booking.session_state === 'SCHEDULED' && (
                <Button>
                  <Video className="h-4 w-4 mr-2" />
                  Join Session
                </Button>
              )}

              {canReschedule && (
                <Button variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Request Reschedule
                </Button>
              )}

              {canCancel && (
                <Button
                  variant="ghost"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  onClick={handleCancel}
                  loading={cancelBooking.isPending}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Cancel Booking
                </Button>
              )}
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Messages</CardTitle>
              <Button asChild variant="outline" size="sm">
                <Link href={`/messages?booking=${booking.id}`}>
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Open Chat
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <MessageSquare className="h-10 w-10 text-slate-300 mx-auto mb-2" />
                <p className="text-slate-500">
                  Message the tutor about this session
                </p>
                <Button asChild variant="link" className="mt-2">
                  <Link href={`/messages?booking=${booking.id}`}>
                    Start conversation
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Status Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {timeline.map((step, index) => {
                  const Icon = step.icon;
                  return (
                    <div key={step.label} className="flex items-start gap-3 pb-6 last:pb-0">
                      <div className="relative">
                        <div
                          className={`h-8 w-8 rounded-full flex items-center justify-center ${
                            step.status === 'completed'
                              ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                              : step.status === 'current'
                              ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/30 dark:text-primary-400 ring-2 ring-primary-500'
                              : 'bg-slate-100 text-slate-400 dark:bg-slate-800'
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        {index < timeline.length - 1 && (
                          <div
                            className={`absolute left-1/2 top-8 w-0.5 h-6 -translate-x-1/2 ${
                              step.status === 'completed'
                                ? 'bg-green-300 dark:bg-green-700'
                                : 'bg-slate-200 dark:bg-slate-700'
                            }`}
                          />
                        )}
                      </div>
                      <div className="pt-1">
                        <p
                          className={`font-medium ${
                            step.status === 'upcoming'
                              ? 'text-slate-400'
                              : 'text-slate-900 dark:text-white'
                          }`}
                        >
                          {step.label}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Payment</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-500">Session fee</span>
                <span className="font-medium text-slate-900 dark:text-white">
                  {formatCurrency(booking.total_amount ?? booking.rate_cents / 100, booking.currency)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <span
                  className={`font-medium ${
                    booking.payment_state === 'CAPTURED'
                      ? 'text-green-600'
                      : booking.payment_state === 'REFUNDED' ||
                        booking.payment_state === 'VOIDED'
                      ? 'text-red-600'
                      : 'text-amber-600'
                  }`}
                >
                  {booking.payment_state.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </div>
              <hr className="border-slate-200 dark:border-slate-700" />
              <div className="flex justify-between text-lg">
                <span className="font-semibold text-slate-900 dark:text-white">
                  Total
                </span>
                <span className="font-bold text-slate-900 dark:text-white">
                  {formatCurrency(booking.total_amount ?? booking.rate_cents / 100, booking.currency)}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
