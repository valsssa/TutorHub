'use client';

import Link from 'next/link';
import {
  Calendar,
  Clock,
  DollarSign,
  Star,
  CalendarCheck,
  Settings,
  TrendingUp,
  User,
} from 'lucide-react';
import { useAuth } from '@/lib/hooks';
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

function StatCard({
  label,
  value,
  icon: Icon,
  trend,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
            <Icon className="h-5 w-5 text-primary-600" />
          </div>
          <div className="flex-1">
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {value}
            </p>
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

const mockPendingRequests = [
  {
    id: 1,
    studentName: 'Alex Johnson',
    subject: 'Mathematics',
    requestedTime: 'Tomorrow, 3:00 PM',
    duration: '1 hour',
  },
  {
    id: 2,
    studentName: 'Sarah Williams',
    subject: 'Physics',
    requestedTime: 'Feb 5, 10:00 AM',
    duration: '1.5 hours',
  },
  {
    id: 3,
    studentName: 'Michael Chen',
    subject: 'Chemistry',
    requestedTime: 'Feb 6, 2:00 PM',
    duration: '1 hour',
  },
];

const mockTodaySchedule = [
  {
    id: 1,
    studentName: 'Emma Davis',
    subject: 'Calculus',
    time: '9:00 AM - 10:00 AM',
    status: 'upcoming',
  },
  {
    id: 2,
    studentName: 'James Wilson',
    subject: 'Linear Algebra',
    time: '11:00 AM - 12:00 PM',
    status: 'upcoming',
  },
  {
    id: 3,
    studentName: 'Olivia Brown',
    subject: 'Statistics',
    time: '2:00 PM - 3:30 PM',
    status: 'upcoming',
  },
];

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

export default function TutorDashboard() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

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
        <Link href="/tutor/availability">
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Manage Availability
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Upcoming Sessions"
          value={8}
          icon={Calendar}
        />
        <StatCard
          label="Completed This Month"
          value={24}
          icon={CalendarCheck}
          trend="+12%"
        />
        <StatCard
          label="Earnings This Month"
          value="$1,250"
          icon={DollarSign}
          trend="+8%"
        />
        <StatCard
          label="Average Rating"
          value="4.9"
          icon={Star}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Pending Booking Requests</CardTitle>
              <Badge variant="warning">{mockPendingRequests.length} pending</Badge>
            </CardHeader>
            <CardContent>
              {mockPendingRequests.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No pending requests</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {mockPendingRequests.map((request) => (
                    <div
                      key={request.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-full bg-primary-100 dark:bg-primary-900/30">
                            <User className="h-4 w-4 text-primary-600" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900 dark:text-white">
                              {request.studentName}
                            </p>
                            <p className="text-sm text-slate-500">
                              {request.subject} - {request.duration}
                            </p>
                            <p className="text-xs text-slate-400 mt-1">
                              <Clock className="h-3 w-3 inline mr-1" />
                              {request.requestedTime}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">
                            Decline
                          </Button>
                          <Button size="sm">Accept</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Today&apos;s Schedule</CardTitle>
              <Link
                href="/tutor/schedule"
                className="text-sm text-primary-600 hover:underline"
              >
                View full schedule
              </Link>
            </CardHeader>
            <CardContent>
              {mockTodaySchedule.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No sessions scheduled for today</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {mockTodaySchedule.map((session) => (
                    <div
                      key={session.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-3">
                        <div className="text-center min-w-[60px]">
                          <p className="text-xs text-slate-500">
                            {session.time.split(' - ')[0]}
                          </p>
                        </div>
                        <div className="h-8 w-px bg-slate-200 dark:bg-slate-700" />
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {session.subject}
                          </p>
                          <p className="text-sm text-slate-500">
                            with {session.studentName}
                          </p>
                        </div>
                      </div>
                      <Badge variant="primary">Upcoming</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link href="/tutor/schedule" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <Calendar className="h-4 w-4 mr-3" />
                  View Schedule
                </Button>
              </Link>
              <Link href="/tutor/availability" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-3" />
                  Manage Availability
                </Button>
              </Link>
              <Link href="/tutor/earnings" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <TrendingUp className="h-4 w-4 mr-3" />
                  View Earnings
                </Button>
              </Link>
              <Link href="/messages" className="block">
                <Button variant="ghost" className="w-full justify-start">
                  <User className="h-4 w-4 mr-3" />
                  Messages
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Response Rate</span>
                    <span className="font-medium text-slate-900 dark:text-white">98%</span>
                  </div>
                  <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: '98%' }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Completion Rate</span>
                    <span className="font-medium text-slate-900 dark:text-white">95%</span>
                  </div>
                  <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: '95%' }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-500">Student Satisfaction</span>
                    <span className="font-medium text-slate-900 dark:text-white">4.9/5</span>
                  </div>
                  <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full"
                      style={{ width: '98%' }}
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
