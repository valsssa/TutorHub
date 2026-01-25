"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, TrendingUp, Calendar, DollarSign, Clock, Download } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth, bookings } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { User } from "@/types";
import { BookingDTO } from "@/types/booking";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import AppShell from "@/components/AppShell";

export default function TutorEarningsPage() {
  return (
    <ProtectedRoute requiredRole="tutor" showNavbar={false}>
      <TutorEarningsContent />
    </ProtectedRoute>
  );
}

function TutorEarningsContent() {
  const router = useRouter();
  const { showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [bookingsData, setBookingsData] = useState<BookingDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<"all" | "month" | "week">("month");

  useEffect(() => {
    const loadEarningsData = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        if (!authUtils.isTutor(currentUser)) {
          router.replace("/unauthorized");
          return;
        }

        // Load all bookings for earnings calculation
        const bookingData = await bookings.list({
          role: "tutor",
          page: 1,
          page_size: 1000, // Get all bookings for accurate earnings
        });
        setBookingsData(bookingData.bookings || []);
      } catch (error) {
        console.error("Failed to load earnings data:", error);
        showError("Failed to load earnings data");
      } finally {
        setLoading(false);
      }
    };

    loadEarningsData();
  }, [router, showError]);

  // Filter bookings by period
  const filteredBookings = useMemo(() => {
    const now = new Date();
    let cutoffDate: Date;

    switch (selectedPeriod) {
      case "week":
        cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case "month":
        cutoffDate = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      default:
        return bookingsData;
    }

    return bookingsData.filter((b) => new Date(b.created_at) >= cutoffDate);
  }, [bookingsData, selectedPeriod]);

  // Calculate earnings from completed bookings
  const completedBookings = useMemo(
    () =>
      filteredBookings.filter(
        (b) => b.status === "COMPLETED" || b.status === "completed"
      ),
    [filteredBookings]
  );

  // Calculate earnings metrics
  const totalEarnings = useMemo(
    () =>
      completedBookings.reduce(
        (sum, b) => sum + b.tutor_earnings_cents / 100,
        0
      ),
    [completedBookings]
  );

  const totalSessions = completedBookings.length;

  const averageEarningsPerSession = useMemo(
    () => (totalSessions > 0 ? totalEarnings / totalSessions : 0),
    [totalEarnings, totalSessions]
  );

  // Calculate previous period for comparison
  const previousPeriodEarnings = useMemo(() => {
    const now = new Date();
    let currentPeriodStart: Date;
    let previousPeriodStart: Date;
    let previousPeriodEnd: Date;

    switch (selectedPeriod) {
      case "week":
        currentPeriodStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        previousPeriodStart = new Date(
          currentPeriodStart.getTime() - 7 * 24 * 60 * 60 * 1000
        );
        previousPeriodEnd = currentPeriodStart;
        break;
      case "month":
        currentPeriodStart = new Date(now.getFullYear(), now.getMonth(), 1);
        previousPeriodStart = new Date(
          now.getFullYear(),
          now.getMonth() - 1,
          1
        );
        previousPeriodEnd = currentPeriodStart;
        break;
      default:
        // For "all", compare with last month
        const lastMonthStart = new Date(
          now.getFullYear(),
          now.getMonth() - 1,
          1
        );
        const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 1);
        return bookingsData
          .filter((b) => {
            const bookingDate = new Date(b.created_at);
            return (
              (b.status === "COMPLETED" || b.status === "completed") &&
              bookingDate >= lastMonthStart &&
              bookingDate < lastMonthEnd
            );
          })
          .reduce((sum, b) => sum + b.tutor_earnings_cents / 100, 0);
    }

    return bookingsData
      .filter((b) => {
        const bookingDate = new Date(b.created_at);
        return (
          (b.status === "COMPLETED" || b.status === "completed") &&
          bookingDate >= previousPeriodStart &&
          bookingDate < previousPeriodEnd
        );
      })
      .reduce((sum, b) => sum + b.tutor_earnings_cents / 100, 0);
  }, [bookingsData, selectedPeriod]);

  const earningsChange = useMemo(() => {
    if (previousPeriodEarnings === 0) return totalEarnings > 0 ? 100 : 0;
    return ((totalEarnings - previousPeriodEarnings) / previousPeriodEarnings) * 100;
  }, [totalEarnings, previousPeriodEarnings]);

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Earnings
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              Track your earnings and payment history
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => {
                // TODO: Implement export functionality
                showError("Export feature coming soon");
              }}
              className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Download size={16} /> Export
            </button>
          </div>
        </div>

        {/* Period Selector */}
        <div className="flex gap-2 mb-6">
          {(["week", "month", "all"] as const).map((period) => (
            <button
              key={period}
              onClick={() => setSelectedPeriod(period)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedPeriod === period
                  ? "bg-emerald-600 text-white"
                  : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
              }`}
            >
              {period === "week"
                ? "This Week"
                : period === "month"
                ? "This Month"
                : "All Time"}
            </button>
          ))}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Total Earnings */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-emerald-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Total Earnings
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                {formatCurrency(totalEarnings)}
              </div>
              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                <span className="flex items-center">
                  <ArrowRight
                    size={12}
                    className={`rotate-[-45deg] ${
                      earningsChange < 0 ? "rotate-[45deg]" : ""
                    }`}
                  />{" "}
                  {earningsChange >= 0 ? "+" : ""}
                  {earningsChange.toFixed(1)}%
                </span>
                <span className="text-slate-400 dark:text-slate-500 font-normal">
                  vs{" "}
                  {selectedPeriod === "week"
                    ? "last week"
                    : selectedPeriod === "month"
                    ? "last month"
                    : "last month"}
                </span>
              </div>
            </div>
          </div>

          {/* Total Sessions */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-blue-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Completed Sessions
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                {totalSessions}
              </div>
              <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-medium">
                <Clock size={12} />
                <span className="text-slate-400 dark:text-slate-500 font-normal">
                  {selectedPeriod === "week"
                    ? "this week"
                    : selectedPeriod === "month"
                    ? "this month"
                    : "total"}
                </span>
              </div>
            </div>
          </div>

          {/* Average per Session */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-purple-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Average per Session
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                {formatCurrency(averageEarningsPerSession)}
              </div>
              <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 font-medium">
                <TrendingUp size={12} />
                <span className="text-slate-400 dark:text-slate-500 font-normal">
                  per completed lesson
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Earnings History */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
            <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
              <DollarSign size={20} className="text-emerald-500" /> Earnings
              History
            </h3>
            <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded text-xs font-bold">
              {completedBookings.length} Sessions
            </span>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {completedBookings.length === 0 ? (
              <div className="p-12 text-center text-slate-500 dark:text-slate-400">
                <Calendar size={48} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg font-medium mb-2">No earnings yet</p>
                <p className="text-sm">
                  Complete sessions to start earning. Your earnings will appear
                  here once sessions are completed.
                </p>
              </div>
            ) : (
              completedBookings
                .sort(
                  (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime()
                )
                .map((booking) => (
                  <div
                    key={booking.id}
                    className="p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                        <DollarSign
                          size={20}
                          className="text-emerald-600 dark:text-emerald-400"
                        />
                      </div>
                      <div>
                        <div className="text-base font-bold text-slate-900 dark:text-white mb-0.5">
                          {booking.student?.name || "Student"}
                        </div>
                        <div className="text-sm text-slate-500 dark:text-slate-400 flex flex-wrap items-center gap-x-3 gap-y-1">
                          <span className="bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs font-medium text-slate-700 dark:text-slate-300">
                            {booking.subject_name || "Session"}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar size={12} />
                            {formatDate(booking.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-slate-900 dark:text-white mb-0.5">
                        {formatCurrency(booking.tutor_earnings_cents / 100)}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {formatCurrency(booking.rate_cents / 100)} lesson rate
                      </div>
                    </div>
                  </div>
                ))
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
