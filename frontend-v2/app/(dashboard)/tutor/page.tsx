'use client';

import Link from 'next/link';
import { useState } from 'react';
import {
  Calendar,
  Clock,
  DollarSign,
  Star,
  CalendarCheck,
  Settings,
  TrendingUp,
  User,
  MessageSquare,
  AlertCircle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import {
  useAuth,
  useBookings,
  useMyTutorProfile,
  useConfirmBooking,
  useDeclineBooking,
} from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Skeleton,
  SkeletonCard,
} from '@/components/ui';
import { formatDate, formatTime, formatCurrency } from '@/lib/utils';
import type { Booking } from '@/types';

function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  isLoading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  isLoading?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
            <Icon className="h-5 w-5 text-primary-600" />
          </div>
          <div className="flex-1">
            {isLoading ? (
              <Skeleton className="h-8 w-16 mb-1" />
            ) : (
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {value}
              </p>
            )}
            <p className="text-sm text-slate-500">{label}</p>
          </div>
          {trend && (
            <span className="text-xs text-green-600 font-medium">{trend}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function getDateLabel(startDate: Date): string {
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const isToday = today.toDateString() === startDate.toDateString();
  const isTomorrow = tomorrow.toDateString() === startDate.toDateString();

  if (isToday) return 'Today';
  if (isTomorrow) return 'Tomorrow';
  return formatDate(startDate, { weekday: 'short', month: 'short', day: 'numeric' });
}

function PendingRequestCard({
  booking,
  onAccept,
  onDecline,
  isConfirming,
  isDeclining,
}: {
  booking: Booking;
  onAccept: () => void;
  onDecline: () => void;
  isConfirming: boolean;
  isDeclining: boolean;
}) {
  const startDate = new Date(booking.start_at);
  const dateLabel = getDateLabel(startDate);

  return (
    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-primary-100 dark:bg-primary-900/30">
            <User className="h-4 w-4 text-primary-600" />
          </div>
          <div>
            <p className="font-medium text-slate-900 dark:text-white">
              {booking.student?.name || 'Student'}
            </p>
            <p className="text-sm text-slate-500">
              {booking.subject_name || 'General'} - 60 min
            </p>
            <p className="text-xs text-slate-400 mt-1">
              <Clock className="h-3 w-3 inline mr-1" />
              {dateLabel}, {formatTime(startDate)}
            </p>
            {booking.notes_student && (
              <p className="text-xs text-slate-500 mt-2 italic">
                &ldquo;{booking.notes_student}&rdquo;
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onDecline}
            disabled={isConfirming || isDeclining}
          >
            {isDeclining ? (
              <span className="flex items-center gap-1">
                <XCircle className="h-3 w-3 animate-spin" />
                Declining...
              </span>
            ) : (
              'Decline'
            )}
          </Button>
          <Button
            size="sm"
            onClick={onAccept}
            disabled={isConfirming || isDeclining}
          >
            {isConfirming ? (
              <span className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 animate-spin" />
                Accepting...
              </span>
            ) : (
              'Accept'
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function ScheduleCard({ booking }: { booking: Booking }) {
  const startDate = new Date(booking.start_at);
  const endDate = new Date(booking.end_at);

  const getStatusBadge = () => {
    const now = new Date();
    if (booking.session_state === 'ACTIVE' || booking.session_state === 'in_progress') {
      return <Badge variant="success">In Progress</Badge>;
    }
    if (startDate > now) {
      return <Badge variant="primary">Upcoming</Badge>;
    }
    return <Badge variant="default">Scheduled</Badge>;
  };

  return (
    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="text-center min-w-[60px]">
          <p className="text-xs text-slate-500">{formatTime(startDate)}</p>
          <p className="text-xs text-slate-400">-</p>
          <p className="text-xs text-slate-500">{formatTime(endDate)}</p>
        </div>
        <div className="h-10 w-px bg-slate-200 dark:bg-slate-700" />
        <div>
          <p className="font-medium text-slate-900 dark:text-white">
            {booking.subject_name || 'Session'}
          </p>
          <p className="text-sm text-slate-500">
            with {booking.student?.name || 'Student'}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        {getStatusBadge()}
        {booking.join_url && (
          <Button size="sm" asChild>
            <a href={booking.join_url} target="_blank" rel="noopener noreferrer">
              Join
            </a>
          </Button>
        )}
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-24 rounded-2xl" />
        <Skeleton className="h-24 rounded-2xl" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <SkeletonCard />
          <SkeletonCard />
        </div>
        <SkeletonCard />
      </div>
    </div>
  );
}

function ErrorDisplay({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <AlertCircle className="h-12 w-12 text-red-400 mb-3" />
      <p className="text-slate-600 dark:text-slate-400 mb-4">{message}</p>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </div>
  );
}

export default function TutorDashboard() {
  const { user, isLoading: authLoading } = useAuth();
  const [processingBookingId, setProcessingBookingId] = useState<number | null>(null);

  // Fetch tutor profile for stats
  const {
    data: tutorProfile,
    isLoading: profileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useMyTutorProfile();

  // Fetch pending booking requests
  const {
    data: pendingData,
    isLoading: pendingLoading,
    error: pendingError,
    refetch: refetchPending,
  } = useBookings({
    status: 'pending',
    role: 'tutor',
    page_size: 10,
  });

  // Get today's date range for filtering
  const today = new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const todayEnd = new Date(todayStart.getTime() + 24 * 60 * 60 * 1000);

  // Fetch scheduled sessions (upcoming and active)
  const {
    data: scheduledData,
    isLoading: scheduledLoading,
    error: scheduledError,
    refetch: refetchScheduled,
  } = useBookings({
    status: 'upcoming',
    role: 'tutor',
    page_size: 20,
  });

  // Mutations for accept/decline
  const confirmMutation = useConfirmBooking();
  const declineMutation = useDeclineBooking();

  // Handle accept booking
  const handleAccept = async (bookingId: number) => {
    setProcessingBookingId(bookingId);
    try {
      await confirmMutation.mutateAsync(bookingId);
    } finally {
      setProcessingBookingId(null);
    }
  };

  // Handle decline booking
  const handleDecline = async (bookingId: number) => {
    setProcessingBookingId(bookingId);
    try {
      await declineMutation.mutateAsync({ id: bookingId, reason: 'Declined by tutor' });
    } finally {
      setProcessingBookingId(null);
    }
  };

  if (authLoading) {
    return <LoadingSkeleton />;
  }

  // Get bookings from response
  const pendingRequests = pendingData?.bookings ?? [];
  const allUpcoming = scheduledData?.bookings ?? [];

  // Filter for today's sessions only
  const todaySchedule = allUpcoming.filter((booking: Booking) => {
    const startTime = new Date(booking.start_at);
    return startTime >= todayStart && startTime < todayEnd;
  });

  // Calculate stats from tutor profile
  const totalSessions = tutorProfile?.total_sessions ?? 0;
  const averageRating = tutorProfile?.average_rating ?? 0;
  const upcomingCount = allUpcoming.length;
  const pendingCount = pendingRequests.length;

  // Calculate earnings (placeholder - would need a real endpoint)
  // For now, estimate based on hourly rate and completed sessions
  const hourlyRate = tutorProfile?.hourly_rate ?? 0;
  const estimatedMonthlyEarnings = Math.round(totalSessions * hourlyRate * 0.8); // 80% after fees

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Welcome back, {user?.first_name}!
          </h1>
          <p className="text-slate-500">
            Here&apos;s what&apos;s happening with your tutoring sessions.
          </p>
        </div>
        <Link href="/profile/availability">
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Manage Availability
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Upcoming Sessions"
          value={upcomingCount}
          icon={Calendar}
          isLoading={scheduledLoading}
        />
        <StatCard
          label="Total Sessions"
          value={totalSessions}
          icon={CalendarCheck}
          isLoading={profileLoading}
        />
        <StatCard
          label="Est. Earnings"
          value={formatCurrency(estimatedMonthlyEarnings)}
          icon={DollarSign}
          isLoading={profileLoading}
        />
        <StatCard
          label="Average Rating"
          value={averageRating > 0 ? averageRating.toFixed(1) : 'N/A'}
          icon={Star}
          isLoading={profileLoading}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Booking Requests */}
          <Card>
            <CardHeader>
              <CardTitle>Pending Booking Requests</CardTitle>
              {pendingCount > 0 && (
                <Badge variant="warning">{pendingCount} pending</Badge>
              )}
            </CardHeader>
            <CardContent>
              {pendingLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 rounded-xl" />
                  <Skeleton className="h-24 rounded-xl" />
                </div>
              ) : pendingError ? (
                <ErrorDisplay
                  message="Failed to load pending requests"
                  onRetry={() => refetchPending()}
                />
              ) : pendingRequests.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No pending requests</p>
                  <p className="text-sm text-slate-400 mt-1">
                    New booking requests will appear here
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingRequests.map((request: Booking) => (
                    <PendingRequestCard
                      key={request.id}
                      booking={request}
                      onAccept={() => handleAccept(request.id)}
                      onDecline={() => handleDecline(request.id)}
                      isConfirming={
                        processingBookingId === request.id && confirmMutation.isPending
                      }
                      isDeclining={
                        processingBookingId === request.id && declineMutation.isPending
                      }
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Today's Schedule */}
          <Card>
            <CardHeader>
              <CardTitle>Today&apos;s Schedule</CardTitle>
              <Link
                href="/bookings"
                className="text-sm text-primary-600 hover:underline"
              >
                View full schedule
              </Link>
            </CardHeader>
            <CardContent>
              {scheduledLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-20 rounded-xl" />
                  <Skeleton className="h-20 rounded-xl" />
                </div>
              ) : scheduledError ? (
                <ErrorDisplay
                  message="Failed to load schedule"
                  onRetry={() => refetchScheduled()}
                />
              ) : todaySchedule.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No sessions scheduled for today</p>
                  <p className="text-sm text-slate-400 mt-1">
                    {allUpcoming.length > 0
                      ? `You have ${allUpcoming.length} upcoming session${allUpcoming.length > 1 ? 's' : ''}`
                      : 'Check back when students book sessions'}
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {todaySchedule.map((session: Booking) => (
                    <ScheduleCard key={session.id} booking={session} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link href="/bookings" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <Calendar className="h-4 w-4 mr-3" />
                  View Schedule
                </Button>
              </Link>
              <Link href="/profile/availability" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-3" />
                  Manage Availability
                </Button>
              </Link>
              <Link href="/wallet" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <TrendingUp className="h-4 w-4 mr-3" />
                  View Earnings
                </Button>
              </Link>
              <Link href="/messages" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <MessageSquare className="h-4 w-4 mr-3" />
                  Messages
                </Button>
              </Link>
              <Link href="/tutor/students" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <User className="h-4 w-4 mr-3" />
                  My Students
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Performance Card */}
          <Card>
            <CardHeader>
              <CardTitle>Performance</CardTitle>
            </CardHeader>
            <CardContent>
              {profileLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
              ) : profileError ? (
                <ErrorDisplay
                  message="Failed to load performance data"
                  onRetry={() => refetchProfile()}
                />
              ) : (
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-500">Response Rate</span>
                      <span className="font-medium text-slate-900 dark:text-white">
                        {pendingCount === 0 ? '100%' : 'Active'}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 rounded-full transition-all duration-500"
                        style={{ width: pendingCount === 0 ? '100%' : '80%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-500">Completion Rate</span>
                      <span className="font-medium text-slate-900 dark:text-white">
                        {totalSessions > 0 ? '95%' : 'N/A'}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all duration-500"
                        style={{ width: totalSessions > 0 ? '95%' : '0%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-500">Student Satisfaction</span>
                      <span className="font-medium text-slate-900 dark:text-white">
                        {averageRating > 0 ? `${averageRating.toFixed(1)}/5` : 'N/A'}
                      </span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full transition-all duration-500"
                        style={{ width: averageRating > 0 ? `${(averageRating / 5) * 100}%` : '0%' }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
