'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Users,
  GraduationCap,
  Calendar,
  DollarSign,
  UserCheck,
  ClipboardList,
  BarChart3,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Skeleton,
} from '@/components/ui';

interface PendingTutor {
  id: number;
  name: string;
  email: string;
  subject: string;
  submittedAt: string;
}

interface ActivityItem {
  id: number;
  type: 'user_registered' | 'booking_completed' | 'tutor_approved' | 'payment_received';
  description: string;
  timestamp: string;
}

const mockPendingTutors: PendingTutor[] = [
  {
    id: 1,
    name: 'Sarah Johnson',
    email: 'sarah.j@email.com',
    subject: 'Mathematics',
    submittedAt: '2 hours ago',
  },
  {
    id: 2,
    name: 'Michael Chen',
    email: 'michael.c@email.com',
    subject: 'Physics',
    submittedAt: '5 hours ago',
  },
  {
    id: 3,
    name: 'Emily Rodriguez',
    email: 'emily.r@email.com',
    subject: 'English Literature',
    submittedAt: '1 day ago',
  },
];

const mockActivity: ActivityItem[] = [
  {
    id: 1,
    type: 'user_registered',
    description: 'New student registered: John Doe',
    timestamp: '5 minutes ago',
  },
  {
    id: 2,
    type: 'booking_completed',
    description: 'Session completed: Math tutoring with Sarah J.',
    timestamp: '1 hour ago',
  },
  {
    id: 3,
    type: 'tutor_approved',
    description: 'Tutor approved: David Kim',
    timestamp: '2 hours ago',
  },
  {
    id: 4,
    type: 'payment_received',
    description: 'Payment received: $75.00 for Chemistry session',
    timestamp: '3 hours ago',
  },
  {
    id: 5,
    type: 'user_registered',
    description: 'New student registered: Lisa Wang',
    timestamp: '4 hours ago',
  },
];

const mockStats = {
  totalUsers: 1247,
  activeTutors: 89,
  totalBookings: 3421,
  revenueThisMonth: 24850,
};

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

function ActivityIcon({ type }: { type: ActivityItem['type'] }) {
  switch (type) {
    case 'user_registered':
      return <Users className="h-4 w-4 text-blue-500" />;
    case 'booking_completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'tutor_approved':
      return <UserCheck className="h-4 w-4 text-purple-500" />;
    case 'payment_received':
      return <DollarSign className="h-4 w-4 text-emerald-500" />;
    default:
      return <AlertCircle className="h-4 w-4 text-slate-400" />;
  }
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-2xl" />
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Skeleton className="h-80 rounded-2xl" />
        </div>
        <div>
          <Skeleton className="h-80 rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [isLoading, setIsLoading] = useState(false);
  const [pendingTutors] = useState<PendingTutor[]>(mockPendingTutors);
  const [activity] = useState<ActivityItem[]>(mockActivity);
  const [stats] = useState(mockStats);

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Admin Dashboard
          </h1>
          <p className="text-slate-500">Platform overview and management</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" asChild>
            <Link href="/admin/reports">
              <BarChart3 className="h-4 w-4 mr-2" />
              View Reports
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Users"
          value={stats.totalUsers.toLocaleString()}
          icon={Users}
          trend="+12%"
        />
        <StatCard
          label="Active Tutors"
          value={stats.activeTutors}
          icon={GraduationCap}
          trend="+5%"
        />
        <StatCard
          label="Total Bookings"
          value={stats.totalBookings.toLocaleString()}
          icon={Calendar}
          trend="+18%"
        />
        <StatCard
          label="Revenue (Month)"
          value={`$${stats.revenueThisMonth.toLocaleString()}`}
          icon={DollarSign}
          trend="+23%"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Pending Tutor Approvals</CardTitle>
              <Badge variant="warning">{pendingTutors.length} pending</Badge>
            </CardHeader>
            <CardContent>
              {pendingTutors.length === 0 ? (
                <div className="text-center py-8">
                  <UserCheck className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No pending approvals</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingTutors.map((tutor) => (
                    <div
                      key={tutor.id}
                      className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex-1">
                          <p className="font-medium text-slate-900 dark:text-white">
                            {tutor.name}
                          </p>
                          <p className="text-sm text-slate-500">{tutor.email}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="primary">{tutor.subject}</Badge>
                            <span className="text-xs text-slate-400 flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {tutor.submittedAt}
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">
                            <XCircle className="h-4 w-4 mr-1" />
                            Reject
                          </Button>
                          <Button size="sm">
                            <CheckCircle className="h-4 w-4 mr-1" />
                            Approve
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {pendingTutors.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                  <Button variant="link" asChild className="w-full">
                    <Link href="/admin/tutors/pending">View all pending approvals</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <Link
                href="/admin/activity"
                className="text-sm text-primary-600 hover:underline"
              >
                View all
              </Link>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {activity.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-start gap-3 pb-3 border-b border-slate-100 dark:border-slate-800 last:border-0 last:pb-0"
                  >
                    <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                      <ActivityIcon type={item.type} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700 dark:text-slate-300 truncate">
                        {item.description}
                      </p>
                      <p className="text-xs text-slate-400">{item.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/admin/users">
                  <Users className="h-4 w-4 mr-3" />
                  Manage Users
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/admin/tutors">
                  <GraduationCap className="h-4 w-4 mr-3" />
                  Review Tutors
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/admin/reports">
                  <ClipboardList className="h-4 w-4 mr-3" />
                  View Reports
                </Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start">
                <Link href="/admin/settings">
                  <Settings className="h-4 w-4 mr-3" />
                  System Settings
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
