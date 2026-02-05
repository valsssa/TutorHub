'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Users,
  GraduationCap,
  Calendar,
  DollarSign,
  UserCheck,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ShieldAlert,
  RefreshCw,
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
import {
  useAuth,
  useAdminDashboardStats,
  useAdminRecentActivities,
  usePendingTutors,
  useApproveTutor,
  useRejectTutor,
} from '@/lib/hooks';
import type { AdminActivityItem, PendingTutorProfile } from '@/types/admin';

function StatCard({
  label,
  value,
  icon: Icon,
  isLoading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="flex-1">
              <Skeleton className="h-7 w-16" />
              <Skeleton className="h-4 w-24 mt-1" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

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
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityIcon({ type }: { type: AdminActivityItem['type'] }) {
  switch (type) {
    case 'info':
      return <Users className="h-4 w-4 text-blue-500" />;
    case 'success':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'warning':
      return <AlertCircle className="h-4 w-4 text-amber-500" />;
    case 'error':
      return <XCircle className="h-4 w-4 text-red-500" />;
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

function UnauthorizedView() {
  const router = useRouter();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
      <div className="p-4 rounded-full bg-red-100 dark:bg-red-900/30">
        <ShieldAlert className="h-12 w-12 text-red-600" />
      </div>
      <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
        Access Denied
      </h1>
      <p className="text-slate-500 text-center max-w-md">
        You do not have permission to view the admin dashboard.
        This page is only accessible to administrators.
      </p>
      <Button onClick={() => router.push('/')}>
        Return to Home
      </Button>
    </div>
  );
}

function PendingTutorCard({
  tutor,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: {
  tutor: PendingTutorProfile;
  onApprove: () => void;
  onReject: () => void;
  isApproving: boolean;
  isRejecting: boolean;
}) {
  const tutorName = tutor.user
    ? `${tutor.user.first_name} ${tutor.user.last_name}`
    : `Tutor #${tutor.id}`;
  const tutorEmail = tutor.user?.email || 'Unknown email';
  const subjects = tutor.subjects?.map(s => s.name).join(', ') || 'No subjects';
  const createdAt = new Date(tutor.created_at);
  const timeAgo = formatTimeAgo(createdAt);

  return (
    <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex-1">
          <p className="font-medium text-slate-900 dark:text-white">
            {tutorName}
          </p>
          <p className="text-sm text-slate-500">{tutorEmail}</p>
          <div className="flex items-center gap-2 mt-1">
            <Badge variant="primary">{subjects}</Badge>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {timeAgo}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={onReject}
            disabled={isApproving || isRejecting}
          >
            {isRejecting ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <XCircle className="h-4 w-4 mr-1" />
            )}
            Reject
          </Button>
          <Button
            size="sm"
            onClick={onApprove}
            disabled={isApproving || isRejecting}
          >
            {isApproving ? (
              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-1" />
            )}
            Approve
          </Button>
        </div>
      </div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) {
    const mins = Math.floor(diffInSeconds / 60);
    return `${mins} minute${mins !== 1 ? 's' : ''} ago`;
  }
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  }
  const days = Math.floor(diffInSeconds / 86400);
  return `${days} day${days !== 1 ? 's' : ''} ago`;
}

export default function AdminDashboard() {
  const router = useRouter();
  const { user, isLoading: isAuthLoading } = useAuth();
  const [rejectingTutorId, setRejectingTutorId] = useState<number | null>(null);

  // Fetch data using hooks
  const { data: stats, isLoading: isStatsLoading, error: statsError } = useAdminDashboardStats();
  const { data: activities, isLoading: isActivitiesLoading } = useAdminRecentActivities(10);
  const { data: pendingTutorsData, isLoading: isPendingLoading } = usePendingTutors({ page_size: 5 });

  const approveMutation = useApproveTutor();
  const rejectMutation = useRejectTutor();

  // Check authentication and role
  if (isAuthLoading) {
    return <LoadingSkeleton />;
  }

  if (!user || (user.role !== 'admin' && user.role !== 'owner')) {
    return <UnauthorizedView />;
  }

  const handleApproveTutor = async (tutorId: number) => {
    try {
      await approveMutation.mutateAsync(tutorId);
    } catch (error) {
      console.error('Failed to approve tutor:', error);
    }
  };

  const handleRejectTutor = async (tutorId: number) => {
    const reason = window.prompt('Please provide a reason for rejection (min 10 characters):');
    if (!reason || reason.length < 10) {
      alert('Rejection reason must be at least 10 characters.');
      return;
    }

    setRejectingTutorId(tutorId);
    try {
      await rejectMutation.mutateAsync({
        tutorId,
        data: { rejection_reason: reason },
      });
    } catch (error) {
      console.error('Failed to reject tutor:', error);
    } finally {
      setRejectingTutorId(null);
    }
  };

  const pendingTutors = pendingTutorsData?.items || [];
  const pendingCount = pendingTutorsData?.total || 0;

  // Show error state if stats failed to load
  if (statsError) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Admin Dashboard
            </h1>
            <p className="text-slate-500">Platform overview and management</p>
          </div>
        </div>

        <Card>
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Failed to Load Dashboard
            </h2>
            <p className="text-slate-500 mb-4">
              There was an error loading the dashboard statistics. Please try again.
            </p>
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Page
            </Button>
          </CardContent>
        </Card>
      </div>
    );
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
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Users"
          value={stats?.totalUsers.toLocaleString() || '0'}
          icon={Users}
          isLoading={isStatsLoading}
        />
        <StatCard
          label="Active Tutors"
          value={stats?.activeTutors || 0}
          icon={GraduationCap}
          isLoading={isStatsLoading}
        />
        <StatCard
          label="Total Sessions"
          value={stats?.totalSessions.toLocaleString() || '0'}
          icon={Calendar}
          isLoading={isStatsLoading}
        />
        <StatCard
          label="Revenue"
          value={`$${(stats?.revenue || 0).toLocaleString()}`}
          icon={DollarSign}
          isLoading={isStatsLoading}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Pending Tutor Approvals</CardTitle>
              {pendingCount > 0 && (
                <Badge variant="warning">{pendingCount} pending</Badge>
              )}
            </CardHeader>
            <CardContent>
              {isPendingLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 rounded-xl" />
                  ))}
                </div>
              ) : pendingTutors.length === 0 ? (
                <div className="text-center py-8">
                  <UserCheck className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No pending approvals</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingTutors.map((tutor) => (
                    <PendingTutorCard
                      key={tutor.id}
                      tutor={tutor}
                      onApprove={() => handleApproveTutor(tutor.id)}
                      onReject={() => handleRejectTutor(tutor.id)}
                      isApproving={approveMutation.isPending && approveMutation.variables === tutor.id}
                      isRejecting={rejectingTutorId === tutor.id}
                    />
                  ))}
                </div>
              )}
              {pendingCount > 5 && (
                <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                  <p className="text-sm text-slate-500 text-center">
                    Showing 5 of {pendingCount} pending tutors
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              {isActivitiesLoading ? (
                <div className="space-y-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <Skeleton className="h-8 w-8 rounded-lg" />
                      <div className="flex-1">
                        <Skeleton className="h-4 w-full" />
                        <Skeleton className="h-3 w-20 mt-1" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : !activities || activities.length === 0 ? (
                <div className="text-center py-8">
                  <Clock className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No recent activity</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activities.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-3 pb-3 border-b border-slate-100 dark:border-slate-800 last:border-0 last:pb-0"
                    >
                      <div className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800">
                        <ActivityIcon type={item.type} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-700 dark:text-slate-300 truncate">
                          <span className="font-medium">{item.user}</span> {item.action}
                        </p>
                        <p className="text-xs text-slate-400">{item.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => router.push('/admin/users')}
              >
                <Users className="h-4 w-4 mr-3" />
                Manage Users
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => router.push('/admin/tutors')}
              >
                <GraduationCap className="h-4 w-4 mr-3" />
                Review Tutors
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start"
                onClick={() => router.push('/settings')}
              >
                <Settings className="h-4 w-4 mr-3" />
                System Settings
              </Button>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Platform Health</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Satisfaction Rate
                </span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {isStatsLoading ? (
                    <Skeleton className="h-5 w-12" />
                  ) : (
                    `${stats?.satisfaction || 0}/5`
                  )}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  Completion Rate
                </span>
                <span className="font-semibold text-slate-900 dark:text-white">
                  {isStatsLoading ? (
                    <Skeleton className="h-5 w-12" />
                  ) : (
                    `${stats?.completionRate || 0}%`
                  )}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
