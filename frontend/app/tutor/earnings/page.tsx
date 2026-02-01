"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronLeft,
  BarChart2,
  DollarSign,
  ArrowRight,
  Download,
  CreditCard,
  HelpCircle,
  Edit,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth, bookings } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { User } from "@/types";
import { BookingDTO } from "@/types/booking";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import AppShell from "@/components/AppShell";
import { LazyEarningsChart } from "@/components/charts";

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
  const [transactionsPage, setTransactionsPage] = useState(1);
  const [timeseriesPeriod, setTimeseriesPeriod] = useState<"day" | "month">("month");
  const [timeseriesMonths, setTimeseriesMonths] = useState(6);

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
        showError("Failed to load earnings data");
      } finally {
        setLoading(false);
      }
    };

    loadEarningsData();
  }, [router, showError]);

  // Calculate earnings from completed bookings (using four-field system with fallback)
  const completedBookings = useMemo(
    () =>
      bookingsData.filter((b) => {
        const sessionState = (b.session_state || "").toUpperCase();
        const sessionOutcome = (b.session_outcome || "").toUpperCase();
        return sessionState === "ENDED" && sessionOutcome === "COMPLETED" ||
          b.status === "COMPLETED" || b.status === "completed";
      }),
    [bookingsData]
  );

  // Calculate earnings summary
  const earningsSummary = useMemo(() => {
    const grossEarnings = completedBookings.reduce(
      (sum, b) => sum + b.rate_cents / 100,
      0
    );
    const platformFees = completedBookings.reduce(
      (sum, b) => sum + b.platform_fee_cents / 100,
      0
    );
    const netEarnings = completedBookings.reduce(
      (sum, b) => sum + b.tutor_earnings_cents / 100,
      0
    );
    return {
      gross_earnings_cents: grossEarnings * 100,
      platform_fees_cents: platformFees * 100,
      net_earnings_cents: netEarnings * 100,
    };
  }, [completedBookings]);

  // Transform timeseries data for chart
  const chartData = useMemo(() => {
    const now = new Date();
    const data: { name: string; earnings: number }[] = [];
    // Use completedBookings which already filters for completed sessions
    const completed = completedBookings;

    if (timeseriesPeriod === "month") {
      for (let i = timeseriesMonths - 1; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        const monthStart = new Date(date.getFullYear(), date.getMonth(), 1);
        const monthEnd = new Date(date.getFullYear(), date.getMonth() + 1, 0);

        const monthEarnings = completed
          .filter((b) => {
            // Use end_at (when lesson completed) for accurate earnings date
            const bookingDate = new Date(b.end_at || b.start_at || b.created_at);
            return bookingDate >= monthStart && bookingDate <= monthEnd;
          })
          .reduce((sum, b) => sum + b.tutor_earnings_cents / 100, 0);

        data.push({
          name: date.toLocaleDateString("en-US", { month: "short", year: "numeric" }),
          earnings: monthEarnings,
        });
      }
    } else {
      // Daily view for last 30 days
      for (let i = 29; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59);

        const dayEarnings = completed
          .filter((b) => {
            // Use end_at (when lesson completed) for accurate earnings date
            const bookingDate = new Date(b.end_at || b.start_at || b.created_at);
            return bookingDate >= dayStart && bookingDate <= dayEnd;
          })
          .reduce((sum, b) => sum + b.tutor_earnings_cents / 100, 0);

        data.push({
          name: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
          earnings: dayEarnings,
        });
      }
    }

    return data;
  }, [completedBookings, timeseriesPeriod, timeseriesMonths]);

  // Transform transactions for display (paginated)
  const transactionsPerPage = 10;
  const transactions = useMemo(() => {
    const sorted = [...completedBookings].sort(
      (a, b) =>
        new Date(b.end_at || b.start_at || b.created_at).getTime() -
        new Date(a.end_at || a.start_at || a.created_at).getTime()
    );
    const start = (transactionsPage - 1) * transactionsPerPage;
    const end = start + transactionsPerPage;
    return sorted.slice(start, end).map((tx) => ({
      id: tx.id,
      description: `${tx.subject_name || "Session"} with ${tx.student?.name || "Student"}`,
      date: tx.end_at || tx.start_at || tx.created_at,
      amount: tx.tutor_earnings_cents / 100,
      status: "Completed",
    }));
  }, [completedBookings, transactionsPage]);

  const totalPages = Math.ceil(completedBookings.length / transactionsPerPage);

  const availableBalance = earningsSummary.net_earnings_cents / 100;
  const totalEarnings = earningsSummary.gross_earnings_cents / 100;

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
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
        >
          <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          Back to Dashboard
        </button>

        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
          Earnings & Payouts
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">
          Manage your income, view analytics, and configure payout methods.
        </p>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Analytics & Summary */}
          <div className="lg:col-span-2 space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1">
                  Available Balance
                </div>
                <div className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                  {loading
                    ? "..."
                    : `$${availableBalance.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}`}
                </div>
                <button className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors shadow-sm">
                  Withdraw Funds
                </button>
              </div>
              <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
                <div className="text-sm text-slate-500 dark:text-slate-400 font-medium mb-1">
                  Total Earnings (Lifetime)
                </div>
                <div className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                  {loading
                    ? "..."
                    : `$${totalEarnings.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}`}
                </div>
                {earningsSummary && (
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Platform fees: $
                    {(earningsSummary.platform_fees_cents / 100).toLocaleString("en-US", {
                      minimumFractionDigits: 2,
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Revenue Analytics Chart */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                  <BarChart2 size={20} className="text-emerald-500" /> Earnings Analytics
                </h3>
                <div className="flex gap-2">
                  <select
                    value={timeseriesPeriod}
                    onChange={(e) => setTimeseriesPeriod(e.target.value as "day" | "month")}
                    className="bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-sm px-3 py-1 text-slate-600 dark:text-slate-300 focus:ring-0"
                  >
                    <option value="month">Monthly</option>
                    <option value="day">Daily</option>
                  </select>
                  <select
                    value={timeseriesMonths}
                    onChange={(e) => setTimeseriesMonths(Number(e.target.value))}
                    className="bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-sm px-3 py-1 text-slate-600 dark:text-slate-300 focus:ring-0"
                  >
                    <option value={3}>Last 3 Months</option>
                    <option value={6}>Last 6 Months</option>
                    <option value={12}>Last Year</option>
                  </select>
                </div>
              </div>
              <div className="h-80 w-full">
                {loading ? (
                  <div className="h-full flex items-center justify-center text-slate-400">
                    Loading earnings data...
                  </div>
                ) : (
                  <LazyEarningsChart data={chartData} />
                )}
              </div>
            </div>

            {/* Transaction History */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                  Recent Transactions
                </h3>
                <button
                  onClick={() => showError("Export feature coming soon")}
                  className="text-sm font-medium text-emerald-600 hover:text-emerald-500 transition-colors flex items-center gap-1"
                >
                  <Download size={16} /> Export CSV
                </button>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading ? (
                  <div className="p-8 text-center text-slate-400">Loading transactions...</div>
                ) : transactions.length === 0 ? (
                  <div className="p-8 text-center text-slate-400">No transactions found</div>
                ) : (
                  transactions.map((tx) => (
                    <div
                      key={tx.id}
                      className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            tx.amount > 0
                              ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30"
                              : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          <DollarSign size={18} />
                        </div>
                        <div>
                          <div className="font-medium text-slate-900 dark:text-white text-sm">
                            {tx.description}
                          </div>
                          <div className="text-xs text-slate-500">
                            {new Date(tx.date).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className={`font-bold text-sm ${
                            tx.amount > 0
                              ? "text-emerald-600 dark:text-emerald-400"
                              : "text-red-600 dark:text-red-400"
                          }`}
                        >
                          {tx.amount > 0 ? "+" : ""}${Math.abs(tx.amount).toFixed(2)}
                        </div>
                        <div className="text-xs text-slate-500">{tx.status}</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
              {totalPages > 1 && (
                <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    Page {transactionsPage} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setTransactionsPage((p) => Math.max(1, p - 1))}
                      disabled={transactionsPage === 1}
                      className="px-3 py-1 text-sm border border-slate-300 dark:border-slate-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setTransactionsPage((p) => Math.min(totalPages, p + 1))}
                      disabled={transactionsPage >= totalPages}
                      className="px-3 py-1 text-sm border border-slate-300 dark:border-slate-700 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50 dark:hover:bg-slate-800"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Settings & Info */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-lg text-slate-900 dark:text-white">
                  Payout Method
                </h3>
                <button
                  onClick={() => router.push("/tutor/earnings/edit-payout")}
                  className="p-2 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                  title="Edit payout method"
                >
                  <Edit size={18} />
                </button>
              </div>
              <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 mb-4">
                <div className="w-10 h-10 bg-white dark:bg-slate-900 rounded-lg flex items-center justify-center border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200">
                  <CreditCard size={20} />
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900 dark:text-white">
                    Visa ending in 4242
                  </div>
                  <div className="text-xs text-slate-500">Instant payout available</div>
                </div>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 px-2 py-1 rounded">
                  Primary
                </span>
              </div>
              <button
                onClick={() => router.push("/tutor/earnings/edit-payout")}
                className="w-full py-2.5 border border-slate-300 dark:border-slate-600 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
              >
                Manage Payout Methods
              </button>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-2xl border border-blue-100 dark:border-blue-800/50">
              <h3 className="font-bold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                <HelpCircle size={18} /> Tax Information
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-200 mb-4 leading-relaxed">
                Ensure your tax information is up to date to avoid payout delays. You may need to
                submit a W-9 form if your earnings exceed $600 this year.
              </p>
              <button
                onClick={() => showError("Tax info update coming soon")}
                className="text-sm font-bold text-blue-700 dark:text-blue-300 hover:underline"
              >
                Update Tax Info
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
