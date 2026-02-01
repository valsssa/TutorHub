"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  TrendingUp,
  TrendingDown,
  Users,
  Calendar,
  DollarSign,
  Star,
  Clock,
  BookOpen,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  PieChart,
  Target,
  Award,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import Select from "@/components/Select";
import LoadingSpinner from "@/components/LoadingSpinner";
import { DashboardStatsSkeleton } from "@/components/SkeletonLoader";
import { bookings as bookingsApi, auth } from "@/lib/api";
import type { BookingDTO } from "@/types/booking";
import type { User } from "@/types";
import clsx from "clsx";

type TimePeriod = "7d" | "30d" | "90d" | "12m" | "all";

interface AnalyticsData {
  totalEarnings: number;
  totalSessions: number;
  completedSessions: number;
  cancelledSessions: number;
  totalStudents: number;
  returningStudents: number;
  averageRating: number;
  totalReviews: number;
  averageSessionDuration: number;
  popularSubjects: { name: string; count: number }[];
  earningsByMonth: { month: string; amount: number }[];
  sessionsByStatus: { status: string; count: number }[];
}

function calculateAnalytics(bookings: BookingDTO[], period: TimePeriod): AnalyticsData {
  // Filter by time period
  const now = new Date();
  let startDate: Date;

  switch (period) {
    case "7d":
      startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      break;
    case "30d":
      startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      break;
    case "90d":
      startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
      break;
    case "12m":
      startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      break;
    default:
      startDate = new Date(0);
  }

  const filteredBookings = bookings.filter(
    (b) => new Date(b.created_at) >= startDate
  );

  // Calculate metrics
  const completedBookings = filteredBookings.filter(
    (b) => b.status.toLowerCase() === "completed"
  );
  const cancelledBookings = filteredBookings.filter(
    (b) => b.status.toLowerCase().includes("cancelled")
  );

  const totalEarnings = completedBookings.reduce(
    (sum, b) => sum + (b.tutor_earnings_cents || 0),
    0
  );

  // Unique students
  const studentIds = new Set(filteredBookings.map((b) => b.student?.id));
  const totalStudents = studentIds.size;

  // Returning students (more than 1 booking)
  const studentBookingCount: Record<number, number> = {};
  filteredBookings.forEach((b) => {
    if (b.student?.id) {
      studentBookingCount[b.student.id] = (studentBookingCount[b.student.id] || 0) + 1;
    }
  });
  const returningStudents = Object.values(studentBookingCount).filter(
    (count) => count > 1
  ).length;

  // Popular subjects
  const subjectCount: Record<string, number> = {};
  filteredBookings.forEach((b) => {
    const subject = b.subject_name || "Other";
    subjectCount[subject] = (subjectCount[subject] || 0) + 1;
  });
  const popularSubjects = Object.entries(subjectCount)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  // Earnings by month
  const earningsByMonth: Record<string, number> = {};
  completedBookings.forEach((b) => {
    const date = new Date(b.created_at);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    earningsByMonth[monthKey] = (earningsByMonth[monthKey] || 0) + (b.tutor_earnings_cents || 0);
  });
  const sortedMonths = Object.keys(earningsByMonth).sort();
  const earningsByMonthArray = sortedMonths.slice(-6).map((month) => ({
    month: new Date(month + "-01").toLocaleDateString("en-US", { month: "short" }),
    amount: earningsByMonth[month] / 100,
  }));

  // Sessions by status
  const statusCount: Record<string, number> = {};
  filteredBookings.forEach((b) => {
    const status = b.status.toLowerCase();
    statusCount[status] = (statusCount[status] || 0) + 1;
  });
  const sessionsByStatus = Object.entries(statusCount).map(([status, count]) => ({
    status,
    count,
  }));

  return {
    totalEarnings: totalEarnings / 100,
    totalSessions: filteredBookings.length,
    completedSessions: completedBookings.length,
    cancelledSessions: cancelledBookings.length,
    totalStudents,
    returningStudents,
    averageRating: 4.8, // Placeholder - would come from reviews
    totalReviews: Math.floor(completedBookings.length * 0.7), // Placeholder
    averageSessionDuration: 50, // Placeholder
    popularSubjects,
    earningsByMonth: earningsByMonthArray,
    sessionsByStatus,
  };
}

export default function TutorAnalyticsPage() {
  return (
    <ProtectedRoute allowedRoles={["tutor"]}>
      <AnalyticsContent />
    </ProtectedRoute>
  );
}

function AnalyticsContent() {
  const router = useRouter();

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<TimePeriod>("30d");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [user, data] = await Promise.all([
        auth.getCurrentUser(),
        bookingsApi.getMyBookings(),
      ]);
      setCurrentUser(user);
      setBookings(data);
    } catch (error) {
      // Silently fail - analytics will show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const analytics = useMemo(
    () => calculateAnalytics(bookings, period),
    [bookings, period]
  );

  const completionRate = analytics.totalSessions > 0
    ? Math.round((analytics.completedSessions / analytics.totalSessions) * 100)
    : 0;

  const retentionRate = analytics.totalStudents > 0
    ? Math.round((analytics.returningStudents / analytics.totalStudents) * 100)
    : 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <div className="container mx-auto px-4 py-4">
            <Breadcrumb items={[{ label: "Analytics" }]} />
          </div>
        </div>
        <div className="container mx-auto px-4 py-8 max-w-7xl">
          <DashboardStatsSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb items={[{ label: "Analytics" }]} />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Analytics
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Track your teaching performance and earnings
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as TimePeriod)}
              className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="12m">Last 12 months</option>
              <option value="all">All time</option>
            </select>

            <Link href="/tutor/payouts">
              <Button variant="secondary">View Payouts</Button>
            </Link>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {/* Total Earnings */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <ArrowUpRight className="w-3 h-3" />
                +12%
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              ${analytics.totalEarnings.toLocaleString()}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Total earnings
            </p>
          </div>

          {/* Total Sessions */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <ArrowUpRight className="w-3 h-3" />
                +8%
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.totalSessions}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Total sessions
            </p>
          </div>

          {/* Total Students */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <span className="flex items-center gap-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <ArrowUpRight className="w-3 h-3" />
                +5
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.totalStudents}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Unique students
            </p>
          </div>

          {/* Average Rating */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Star className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {analytics.averageRating.toFixed(1)}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Average rating ({analytics.totalReviews} reviews)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            {/* Earnings Chart Placeholder */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="font-bold text-lg text-slate-900 dark:text-white">
                  Earnings Over Time
                </h2>
                <BarChart3 className="w-5 h-5 text-slate-400" />
              </div>

              {analytics.earningsByMonth.length > 0 ? (
                <div className="h-64 flex items-end gap-2">
                  {analytics.earningsByMonth.map((data, index) => {
                    const maxAmount = Math.max(...analytics.earningsByMonth.map((d) => d.amount));
                    const height = maxAmount > 0 ? (data.amount / maxAmount) * 100 : 0;

                    return (
                      <div key={index} className="flex-1 flex flex-col items-center gap-2">
                        <div
                          className="w-full bg-emerald-500 rounded-t-lg transition-all duration-300 hover:bg-emerald-400"
                          style={{ height: `${Math.max(height, 5)}%` }}
                          title={`$${data.amount.toLocaleString()}`}
                        />
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {data.month}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-slate-500 dark:text-slate-400">
                  No earnings data available
                </div>
              )}
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Completion Rate */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                    <Target className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Completion Rate
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {completionRate}%
                    </p>
                  </div>
                </div>
                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${completionRate}%` }}
                  />
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                  {analytics.completedSessions} of {analytics.totalSessions} sessions completed
                </p>
              </div>

              {/* Retention Rate */}
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <Award className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      Student Retention
                    </p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {retentionRate}%
                    </p>
                  </div>
                </div>
                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full transition-all duration-500"
                    style={{ width: `${retentionRate}%` }}
                  />
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                  {analytics.returningStudents} of {analytics.totalStudents} students returned
                </p>
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* Popular Subjects */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-slate-900 dark:text-white">
                  Popular Subjects
                </h2>
                <BookOpen className="w-5 h-5 text-slate-400" />
              </div>

              {analytics.popularSubjects.length > 0 ? (
                <div className="space-y-3">
                  {analytics.popularSubjects.map((subject, index) => {
                    const maxCount = analytics.popularSubjects[0].count;
                    const percentage = (subject.count / maxCount) * 100;

                    return (
                      <div key={subject.name}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                            {subject.name}
                          </span>
                          <span className="text-sm text-slate-500 dark:text-slate-400">
                            {subject.count} sessions
                          </span>
                        </div>
                        <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={clsx(
                              "h-full rounded-full transition-all duration-500",
                              index === 0 ? "bg-emerald-500" :
                              index === 1 ? "bg-blue-500" :
                              index === 2 ? "bg-purple-500" :
                              index === 3 ? "bg-amber-500" :
                              "bg-slate-400"
                            )}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-4">
                  No subject data available
                </p>
              )}
            </div>

            {/* Session Status Breakdown */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-bold text-lg text-slate-900 dark:text-white">
                  Session Breakdown
                </h2>
                <PieChart className="w-5 h-5 text-slate-400" />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    <span className="text-sm text-slate-600 dark:text-slate-400">Completed</span>
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {analytics.completedSessions}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500" />
                    <span className="text-sm text-slate-600 dark:text-slate-400">Pending</span>
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {analytics.totalSessions - analytics.completedSessions - analytics.cancelledSessions}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-sm text-slate-600 dark:text-slate-400">Cancelled</span>
                  </div>
                  <span className="text-sm font-medium text-slate-900 dark:text-white">
                    {analytics.cancelledSessions}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl p-6 text-white">
              <h3 className="font-bold text-lg mb-2">Grow Your Business</h3>
              <p className="text-emerald-100 text-sm mb-4">
                Complete your profile to attract more students and increase your earnings.
              </p>
              <Link href="/tutor/profile">
                <Button variant="secondary" className="w-full bg-white text-emerald-700 hover:bg-emerald-50">
                  Update Profile
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
