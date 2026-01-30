"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  DollarSign,
  Download,
  Filter,
  Calendar,
  CreditCard,
  Building,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowUpRight,
  ChevronDown,
  Search,
  FileText,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import Input from "@/components/Input";
import Select from "@/components/Select";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import { useToast } from "@/components/ToastContainer";
import { bookings as bookingsApi, auth } from "@/lib/api";
import type { BookingDTO } from "@/types/booking";
import type { User } from "@/types";
import clsx from "clsx";

interface Payout {
  id: string;
  amount: number;
  currency: string;
  status: "pending" | "processing" | "completed" | "failed";
  method: "bank_transfer" | "stripe" | "paypal";
  created_at: string;
  completed_at?: string;
  bookings: number[];
  description: string;
}

// Generate mock payouts from bookings
function generatePayouts(bookings: BookingDTO[]): Payout[] {
  const completedBookings = bookings.filter(
    (b) => b.status.toLowerCase() === "completed"
  );

  if (completedBookings.length === 0) return [];

  // Group bookings by week for payouts
  const weeklyPayouts: Record<string, BookingDTO[]> = {};

  completedBookings.forEach((booking) => {
    const date = new Date(booking.created_at);
    const weekStart = new Date(date);
    weekStart.setDate(date.getDate() - date.getDay());
    const weekKey = weekStart.toISOString().split("T")[0];

    if (!weeklyPayouts[weekKey]) {
      weeklyPayouts[weekKey] = [];
    }
    weeklyPayouts[weekKey].push(booking);
  });

  return Object.entries(weeklyPayouts)
    .map(([weekKey, weekBookings], index) => {
      const totalEarnings = weekBookings.reduce(
        (sum, b) => sum + (b.tutor_earnings_cents || 0),
        0
      );

      const isPast = new Date(weekKey) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

      return {
        id: `payout-${index + 1}`,
        amount: totalEarnings / 100,
        currency: weekBookings[0]?.currency || "USD",
        status: isPast ? "completed" : "pending",
        method: "bank_transfer" as const,
        created_at: weekKey,
        completed_at: isPast ? new Date(new Date(weekKey).getTime() + 3 * 24 * 60 * 60 * 1000).toISOString() : undefined,
        bookings: weekBookings.map((b) => b.id),
        description: `Weekly payout for ${weekBookings.length} session(s)`,
      };
    })
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
}

const STATUS_CONFIG = {
  pending: {
    label: "Pending",
    icon: Clock,
    className: "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
  },
  processing: {
    label: "Processing",
    icon: Clock,
    className: "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300",
  },
  completed: {
    label: "Completed",
    icon: CheckCircle,
    className: "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300",
  },
  failed: {
    label: "Failed",
    icon: AlertCircle,
    className: "bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300",
  },
};

export default function PayoutsPage() {
  return (
    <ProtectedRoute allowedRoles={["tutor"]}>
      <PayoutsContent />
    </ProtectedRoute>
  );
}

function PayoutsContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [bookings, setBookings] = useState<BookingDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

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
      console.error("Failed to load payouts:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const payouts = useMemo(() => generatePayouts(bookings), [bookings]);

  const filteredPayouts = useMemo(() => {
    return payouts.filter((payout) => {
      if (statusFilter !== "all" && payout.status !== statusFilter) return false;
      if (searchQuery && !payout.description.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [payouts, statusFilter, searchQuery]);

  const totalEarnings = useMemo(() => {
    return payouts
      .filter((p) => p.status === "completed")
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payouts]);

  const pendingAmount = useMemo(() => {
    return payouts
      .filter((p) => p.status === "pending" || p.status === "processing")
      .reduce((sum, p) => sum + p.amount, 0);
  }, [payouts]);

  const handleExport = () => {
    // Create CSV content
    const headers = ["Date", "Description", "Amount", "Status", "Method"];
    const rows = filteredPayouts.map((p) => [
      new Date(p.created_at).toLocaleDateString(),
      p.description,
      `$${p.amount.toFixed(2)}`,
      p.status,
      p.method.replace("_", " "),
    ]);

    const csvContent = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `payouts-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    showSuccess("Payout history exported successfully");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Dashboard", href: "/dashboard" },
              { label: "Payouts" },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Payouts
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Track your earnings and payout history
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/tutor/analytics">
              <Button variant="secondary">View Analytics</Button>
            </Link>
            <Button onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {/* Total Earnings */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Total Paid Out
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              ${totalEarnings.toLocaleString()}
            </p>
          </div>

          {/* Pending */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                <Clock className="w-5 h-5 text-amber-600 dark:text-amber-400" />
              </div>
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Pending
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              ${pendingAmount.toLocaleString()}
            </p>
          </div>

          {/* Payout Method */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <Building className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Payout Method
              </span>
            </div>
            <p className="text-lg font-medium text-slate-900 dark:text-white">
              Bank Transfer
            </p>
            <button className="text-sm text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium mt-1">
              Update method
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search payouts..."
              className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Payouts List */}
        {filteredPayouts.length === 0 ? (
          <EmptyState
            variant="no-data"
            title="No payouts yet"
            description="Complete sessions to start earning and receiving payouts."
            action={{
              label: "View Schedule",
              onClick: () => router.push("/tutor/schedule"),
            }}
          />
        ) : (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {filteredPayouts.map((payout) => {
                const statusConfig = STATUS_CONFIG[payout.status];
                const StatusIcon = statusConfig.icon;

                return (
                  <div
                    key={payout.id}
                    className="p-5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                          <DollarSign className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900 dark:text-white">
                            {payout.description}
                          </p>
                          <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-slate-500 dark:text-slate-400">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-4 h-4" />
                              {new Date(payout.created_at).toLocaleDateString("en-US", {
                                month: "short",
                                day: "numeric",
                                year: "numeric",
                              })}
                            </span>
                            <span className="flex items-center gap-1">
                              <CreditCard className="w-4 h-4" />
                              {payout.method.replace("_", " ")}
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText className="w-4 h-4" />
                              {payout.bookings.length} session(s)
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 sm:justify-end">
                        <span
                          className={clsx(
                            "inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium",
                            statusConfig.className
                          )}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {statusConfig.label}
                        </span>
                        <span className="text-lg font-bold text-slate-900 dark:text-white">
                          ${payout.amount.toFixed(2)}
                        </span>
                      </div>
                    </div>

                    {payout.status === "completed" && payout.completed_at && (
                      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3 ml-16">
                        Completed on{" "}
                        {new Date(payout.completed_at).toLocaleDateString("en-US", {
                          month: "long",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Payout Schedule Info */}
        <div className="mt-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-5">
          <h3 className="font-medium text-blue-800 dark:text-blue-200 mb-2">
            Payout Schedule
          </h3>
          <p className="text-sm text-blue-700 dark:text-blue-300">
            Payouts are processed weekly on Mondays. Funds typically arrive within 2-3 business days
            depending on your bank. Minimum payout amount is $10.
          </p>
        </div>
      </div>
    </div>
  );
}
