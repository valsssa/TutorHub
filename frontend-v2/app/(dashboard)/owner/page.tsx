'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  DollarSign,
  TrendingUp,
  Users,
  Activity,
  Server,
  Shield,
  FileText,
  Settings,
  BarChart3,
  UserCog,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAuth, useOwnerDashboard } from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
  Button,
  Badge,
  Skeleton,
} from '@/components/ui';
import type { MarketplaceHealth, CommissionTierBreakdown } from '@/types/owner';

interface MetricCardProps {
  label: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  loading?: boolean;
}

function MetricCard({
  label,
  value,
  change,
  changeType = 'neutral',
  icon: Icon,
  loading,
}: MetricCardProps) {
  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-32" />
              <Skeleton className="h-3 w-20" />
            </div>
            <Skeleton className="h-12 w-12 rounded-xl" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const changeColors = {
    positive: 'text-green-600 dark:text-green-400',
    negative: 'text-red-600 dark:text-red-400',
    neutral: 'text-slate-500',
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              {label}
            </p>
            <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
              {value}
            </p>
            {change && (
              <p className={`mt-1 text-sm ${changeColors[changeType]}`}>
                {change}
              </p>
            )}
          </div>
          <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 shadow-lg">
            <Icon className="h-6 w-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface SystemHealthItemProps {
  name: string;
  status: 'healthy' | 'warning' | 'critical';
  latency?: string;
}

function SystemHealthItem({ name, status, latency }: SystemHealthItemProps) {
  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: 'text-green-500',
      bg: 'bg-green-100 dark:bg-green-900/30',
      badge: 'success' as const,
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-amber-500',
      bg: 'bg-amber-100 dark:bg-amber-900/30',
      badge: 'warning' as const,
    },
    critical: {
      icon: XCircle,
      color: 'text-red-500',
      bg: 'bg-red-100 dark:bg-red-900/30',
      badge: 'danger' as const,
    },
  };

  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${config.bg}`}>
          <StatusIcon className={`h-4 w-4 ${config.color}`} />
        </div>
        <span className="font-medium text-slate-700 dark:text-slate-200">
          {name}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {latency && (
          <span className="text-sm text-slate-500">{latency}</span>
        )}
        <Badge variant={config.badge}>
          {status.charAt(0).toUpperCase() + status.slice(1)}
        </Badge>
      </div>
    </div>
  );
}

function HealthMetricsDisplay({
  health,
  loading,
}: {
  health?: MarketplaceHealth;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-14 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (!health) return null;

  const healthIndicators = [
    {
      name: 'Tutor Rating',
      status: health.average_tutor_rating >= 4 ? 'healthy' : health.average_tutor_rating >= 3 ? 'warning' : 'critical',
      latency: `${health.average_tutor_rating.toFixed(1)}/5`,
    },
    {
      name: 'Tutors Active',
      status: health.tutors_with_bookings_pct >= 50 ? 'healthy' : health.tutors_with_bookings_pct >= 25 ? 'warning' : 'critical',
      latency: `${health.tutors_with_bookings_pct.toFixed(1)}%`,
    },
    {
      name: 'Repeat Rate',
      status: health.repeat_booking_rate >= 30 ? 'healthy' : health.repeat_booking_rate >= 15 ? 'warning' : 'critical',
      latency: `${health.repeat_booking_rate.toFixed(1)}%`,
    },
    {
      name: 'Cancellation Rate',
      status: health.cancellation_rate <= 10 ? 'healthy' : health.cancellation_rate <= 20 ? 'warning' : 'critical',
      latency: `${health.cancellation_rate.toFixed(1)}%`,
    },
    {
      name: 'No-Show Rate',
      status: health.no_show_rate <= 5 ? 'healthy' : health.no_show_rate <= 10 ? 'warning' : 'critical',
      latency: `${health.no_show_rate.toFixed(1)}%`,
    },
    {
      name: 'Response Time',
      status: (health.average_response_time_hours ?? 24) <= 4 ? 'healthy' : (health.average_response_time_hours ?? 24) <= 12 ? 'warning' : 'critical',
      latency: health.average_response_time_hours ? `${health.average_response_time_hours.toFixed(1)}h` : 'N/A',
    },
  ] as const;

  return (
    <div className="space-y-3">
      {healthIndicators.map((indicator) => (
        <SystemHealthItem
          key={indicator.name}
          name={indicator.name}
          status={indicator.status}
          latency={indicator.latency}
        />
      ))}
    </div>
  );
}

function CommissionTiersChart({
  tiers,
  loading,
}: {
  tiers?: CommissionTierBreakdown;
  loading: boolean;
}) {
  if (loading) {
    return <Skeleton className="h-64 w-full rounded-xl" />;
  }

  if (!tiers) return null;

  const chartData = [
    { name: 'Standard (20%)', tutors: tiers.standard_tutors, fill: '#64748b' },
    { name: 'Silver (15%)', tutors: tiers.silver_tutors, fill: '#94a3b8' },
    { name: 'Gold (10%)', tutors: tiers.gold_tutors, fill: '#fbbf24' },
  ];

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
          <XAxis type="number" className="text-xs" />
          <YAxis type="category" dataKey="name" width={100} className="text-xs" />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--slate-800)',
              border: 'none',
              borderRadius: '8px',
              color: 'white',
            }}
          />
          <Bar dataKey="tutors" name="Tutors" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function formatCurrency(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num);
}

export default function OwnerDashboard() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [periodDays, setPeriodDays] = useState(30);

  const {
    data: dashboard,
    isLoading: dashboardLoading,
    error,
    refetch,
  } = useOwnerDashboard({ period_days: periodDays });

  // Role-based access check
  useEffect(() => {
    if (!authLoading && user && user.role !== 'owner') {
      router.push('/');
    }
  }, [user, authLoading, router]);

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="space-y-8">
        <div className="flex items-center justify-center h-64">
          <Skeleton className="h-8 w-48" />
        </div>
      </div>
    );
  }

  // Unauthorized access
  if (!user || user.role !== 'owner') {
    return (
      <div className="flex items-center justify-center h-64">
        <Card>
          <CardContent className="p-8 text-center">
            <Shield className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              Access Denied
            </h2>
            <p className="text-slate-500">
              This page is only accessible to platform owners.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isLoading = dashboardLoading;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Owner Dashboard
            </h1>
            <Badge variant="primary" className="text-xs">
              Executive View
            </Badge>
          </div>
          <p className="text-slate-500 mt-1">
            Welcome back, {user?.first_name}. Here is your business overview.
          </p>
        </div>
        <div className="flex gap-3">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" asChild>
            <Link href="/owner/reports">
              <FileText className="h-4 w-4 mr-2" />
              Reports
            </Link>
          </Button>
          <Button asChild>
            <Link href="/owner/settings">
              <Settings className="h-4 w-4 mr-2" />
              Platform Settings
            </Link>
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
          <CardContent className="p-4">
            <p className="text-red-600 dark:text-red-400">
              Failed to load dashboard data. Please try again.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <MetricCard
          label="Total Revenue (GMV)"
          value={dashboard ? formatCurrency(dashboard.revenue.total_gmv_cents) : '-'}
          change={dashboard ? `Platform fees: ${formatCurrency(dashboard.revenue.total_platform_fees_cents)}` : undefined}
          changeType="positive"
          icon={DollarSign}
          loading={isLoading}
        />
        <MetricCard
          label="Completion Rate"
          value={dashboard ? `${dashboard.growth.completion_rate.toFixed(1)}%` : '-'}
          change={dashboard ? `${dashboard.growth.completed_bookings} completed sessions` : undefined}
          changeType="positive"
          icon={TrendingUp}
          loading={isLoading}
        />
        <MetricCard
          label="Total Users"
          value={dashboard ? formatNumber(dashboard.growth.total_users) : '-'}
          change={dashboard ? `+${dashboard.growth.new_users_period} in last ${periodDays} days` : undefined}
          changeType="positive"
          icon={Users}
          loading={isLoading}
        />
        <MetricCard
          label="Active Tutors"
          value={dashboard ? formatNumber(dashboard.growth.approved_tutors) : '-'}
          change={dashboard ? `${dashboard.growth.total_students} students` : undefined}
          changeType="positive"
          icon={Activity}
          loading={isLoading}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-primary-500" />
                Commission Tier Distribution
              </CardTitle>
              <CardDescription>
                Tutor distribution across commission tiers ({dashboard?.commission_tiers.total_tutors || 0} total)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <CommissionTiersChart
                tiers={dashboard?.commission_tiers}
                loading={isLoading}
              />
              {dashboard && (
                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
                    <p className="text-2xl font-bold text-slate-600">{dashboard.commission_tiers.standard_tutors}</p>
                    <p className="text-xs text-slate-500">Standard (20%)</p>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-200 dark:bg-slate-700">
                    <p className="text-2xl font-bold text-slate-500">{dashboard.commission_tiers.silver_tutors}</p>
                    <p className="text-xs text-slate-500">Silver (15%)</p>
                  </div>
                  <div className="p-3 rounded-lg bg-amber-100 dark:bg-amber-900/30">
                    <p className="text-2xl font-bold text-amber-600">{dashboard.commission_tiers.gold_tutors}</p>
                    <p className="text-xs text-slate-500">Gold (10%)</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5 text-primary-500" />
                Marketplace Health
              </CardTitle>
              <CardDescription>Key performance indicators</CardDescription>
            </CardHeader>
            <CardContent>
              <HealthMetricsDisplay
                health={dashboard?.health}
                loading={isLoading}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between w-full">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary-500" />
                  Revenue Breakdown
                </CardTitle>
                <CardDescription className="mt-1">
                  Platform earnings for the last {periodDays} days
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-xl" />
                ))}
              </div>
            ) : dashboard ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
                  <div>
                    <p className="text-sm text-slate-500">Gross Merchandise Value</p>
                    <p className="text-lg font-bold text-slate-900 dark:text-white">
                      {formatCurrency(dashboard.revenue.total_gmv_cents)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-slate-400" />
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-green-50 dark:bg-green-900/20">
                  <div>
                    <p className="text-sm text-green-600">Platform Fees</p>
                    <p className="text-lg font-bold text-green-700 dark:text-green-400">
                      {formatCurrency(dashboard.revenue.total_platform_fees_cents)}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-green-400" />
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20">
                  <div>
                    <p className="text-sm text-blue-600">Tutor Payouts</p>
                    <p className="text-lg font-bold text-blue-700 dark:text-blue-400">
                      {formatCurrency(dashboard.revenue.total_tutor_payouts_cents)}
                    </p>
                  </div>
                  <Users className="h-8 w-8 text-blue-400" />
                </div>
                <div className="flex items-center justify-between p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20">
                  <div>
                    <p className="text-sm text-purple-600">Average Booking Value</p>
                    <p className="text-lg font-bold text-purple-700 dark:text-purple-400">
                      {formatCurrency(dashboard.revenue.average_booking_value_cents)}
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-purple-400" />
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common owner operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="h-auto py-6 flex-col gap-2"
                asChild
              >
                <Link href="/owner/reports/financial">
                  <FileText className="h-6 w-6 text-primary-500" />
                  <span className="font-medium">Financial Reports</span>
                  <span className="text-xs text-slate-500">
                    Revenue, expenses, profit
                  </span>
                </Link>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-6 flex-col gap-2"
                asChild
              >
                <Link href="/owner/admins">
                  <UserCog className="h-6 w-6 text-primary-500" />
                  <span className="font-medium">Manage Admins</span>
                  <span className="text-xs text-slate-500">
                    Roles and permissions
                  </span>
                </Link>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-6 flex-col gap-2"
                asChild
              >
                <Link href="/owner/settings">
                  <Settings className="h-6 w-6 text-primary-500" />
                  <span className="font-medium">System Config</span>
                  <span className="text-xs text-slate-500">
                    Platform settings
                  </span>
                </Link>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-6 flex-col gap-2"
                asChild
              >
                <Link href="/admin">
                  <BarChart3 className="h-6 w-6 text-primary-500" />
                  <span className="font-medium">Admin Panel</span>
                  <span className="text-xs text-slate-500">
                    User management
                  </span>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {dashboard && (
        <p className="text-xs text-slate-400 text-center">
          Last updated: {new Date(dashboard.generated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}
