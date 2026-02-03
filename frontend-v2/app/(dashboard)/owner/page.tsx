'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
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
} from 'lucide-react';
import { useAuth } from '@/lib/hooks';
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

interface AdminUserProps {
  name: string;
  email: string;
  role: string;
  lastActive: string;
}

function AdminUserRow({ name, email, role, lastActive }: AdminUserProps) {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-slate-600 to-slate-800 flex items-center justify-center">
          <span className="text-sm font-semibold text-white">
            {name.split(' ').map(n => n[0]).join('')}
          </span>
        </div>
        <div>
          <p className="font-medium text-slate-900 dark:text-white">{name}</p>
          <p className="text-sm text-slate-500">{email}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <Badge variant="primary">{role}</Badge>
        <span className="text-sm text-slate-500">{lastActive}</span>
      </div>
    </div>
  );
}

export default function OwnerDashboard() {
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1000);
    return () => clearTimeout(timer);
  }, []);

  const mockMetrics = {
    totalRevenue: '$847,294',
    revenueChange: '+23.5% from last month',
    platformGrowth: '+18.2%',
    growthChange: '+4.1% from last quarter',
    activeSubscriptions: '2,847',
    subscriptionChange: '+156 this month',
    activeUsers: '12,459',
    userChange: '+892 this week',
  };

  const mockSystemHealth = [
    { name: 'API Server', status: 'healthy' as const, latency: '45ms' },
    { name: 'Database', status: 'healthy' as const, latency: '12ms' },
    { name: 'Redis Cache', status: 'healthy' as const, latency: '3ms' },
    { name: 'Payment Gateway', status: 'healthy' as const, latency: '89ms' },
    { name: 'Email Service', status: 'warning' as const, latency: '250ms' },
    { name: 'Storage (MinIO)', status: 'healthy' as const, latency: '28ms' },
  ];

  const mockAdmins = [
    {
      name: 'Sarah Johnson',
      email: 'sarah@edustream.com',
      role: 'Super Admin',
      lastActive: '2 min ago',
    },
    {
      name: 'Michael Chen',
      email: 'michael@edustream.com',
      role: 'Admin',
      lastActive: '1 hour ago',
    },
    {
      name: 'Emily Davis',
      email: 'emily@edustream.com',
      role: 'Support Admin',
      lastActive: '3 hours ago',
    },
  ];

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

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <MetricCard
          label="Total Revenue"
          value={mockMetrics.totalRevenue}
          change={mockMetrics.revenueChange}
          changeType="positive"
          icon={DollarSign}
          loading={isLoading}
        />
        <MetricCard
          label="Platform Growth"
          value={mockMetrics.platformGrowth}
          change={mockMetrics.growthChange}
          changeType="positive"
          icon={TrendingUp}
          loading={isLoading}
        />
        <MetricCard
          label="Active Subscriptions"
          value={mockMetrics.activeSubscriptions}
          change={mockMetrics.subscriptionChange}
          changeType="positive"
          icon={Users}
          loading={isLoading}
        />
        <MetricCard
          label="Active Users"
          value={mockMetrics.activeUsers}
          change={mockMetrics.userChange}
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
                Financial Overview
              </CardTitle>
              <CardDescription>Revenue trends and projections</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-64 w-full rounded-xl" />
              ) : (
                <div className="h-64 flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-700">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-500 dark:text-slate-400">
                      Revenue Chart Placeholder
                    </p>
                    <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
                      Integration with charting library pending
                    </p>
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
                System Health
              </CardTitle>
              <CardDescription>Real-time service status</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5, 6].map((i) => (
                    <Skeleton key={i} className="h-14 w-full rounded-xl" />
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {mockSystemHealth.map((service) => (
                    <SystemHealthItem
                      key={service.name}
                      name={service.name}
                      status={service.status}
                      latency={service.latency}
                    />
                  ))}
                </div>
              )}
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
                  Admin Management
                </CardTitle>
                <CardDescription className="mt-1">
                  Platform administrators and their activity
                </CardDescription>
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link href="/owner/admins">
                  <UserCog className="h-4 w-4 mr-2" />
                  Manage
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full rounded-xl" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {mockAdmins.map((admin) => (
                  <AdminUserRow
                    key={admin.email}
                    name={admin.name}
                    email={admin.email}
                    role={admin.role}
                    lastActive={admin.lastActive}
                  />
                ))}
              </div>
            )}
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
                <Link href="/owner/analytics">
                  <BarChart3 className="h-6 w-6 text-primary-500" />
                  <span className="font-medium">Analytics</span>
                  <span className="text-xs text-slate-500">
                    Usage and metrics
                  </span>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
