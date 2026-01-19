"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  FiCalendar,
  FiClock,
  FiVideo,
  FiStar,
  FiSearch,
} from "react-icons/fi";
import { User } from "@/types";
import { BookingDTO } from "@/types/booking";
import AppShell from "@/components/AppShell";

interface StudentDashboardProps {
  user: User;
  bookings: BookingDTO[];
  onAvatarChange: (url: string | null) => void;
}

// Subject icon helper
function getSubjectIcon(subjectName?: string | null): string {
  if (!subjectName) return "📚";
  const lower = subjectName.toLowerCase();
  if (lower.includes("math")) return "∫";
  if (lower.includes("physics")) return "⚛";
  if (lower.includes("chemistry")) return "🧪";
  if (lower.includes("programming") || lower.includes("code") || lower.includes("computer"))
    return "💻";
  if (lower.includes("english") || lower.includes("language")) return "📝";
  if (lower.includes("music")) return "🎵";
  if (lower.includes("art")) return "🎨";
  if (lower.includes("history")) return "📜";
  if (lower.includes("biology")) return "🧬";
  return "📚";
}

export default function StudentDashboard({
  user,
  bookings,
}: StudentDashboardProps) {
  const router = useRouter();

  // Filter bookings by status
  const upcomingBookings = useMemo(
    () =>
      bookings.filter(
        (b) =>
          b.status === "CONFIRMED" ||
          b.status === "confirmed" ||
          b.status === "PENDING" ||
          b.status === "pending"
      ),
    [bookings]
  );

  const completedBookings = useMemo(
    () =>
      bookings.filter(
        (b) => b.status === "COMPLETED" || b.status === "completed"
      ),
    [bookings]
  );

  // Check if a session is joinable (within 15 minutes of start time)
  const isJoinable = (startAt: string): boolean => {
    const now = new Date();
    const start = new Date(startAt);
    const diff = start.getTime() - now.getTime();
    // Joinable if within 15 minutes before or during the session
    return diff <= 15 * 60 * 1000 && diff >= -60 * 60 * 1000;
  };

  const getUserDisplayName = (): string => {
    if (user.first_name) {
      return user.first_name;
    }
    return user.email.split("@")[0];
  };

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <h1 className="text-3xl font-bold mb-2 text-slate-900 dark:text-white">
          Student Dashboard
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">
          Welcome back, {getUserDisplayName()}
        </p>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <button
            onClick={() => router.push("/tutors")}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex items-center gap-4 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all hover:shadow-lg group"
          >
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <FiSearch size={24} />
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                Find a Tutor
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Browse expert tutors and book sessions
              </p>
            </div>
          </button>

          <button
            onClick={() => router.push("/bookings")}
            className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex items-center gap-4 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 transition-all hover:shadow-lg group"
          >
            <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <FiCalendar size={24} />
            </div>
            <div className="text-left">
              <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                View All Sessions
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Manage your upcoming and past sessions
              </p>
            </div>
          </button>
        </div>

        {/* Sessions Section */}
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
          <FiCalendar size={20} /> Your Sessions
        </h2>
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
          {bookings.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400">
              <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <FiCalendar size={28} className="text-slate-400" />
              </div>
              <p className="mb-4">No sessions booked yet.</p>
              <button
                onClick={() => router.push("/tutors")}
                className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 dark:hover:text-emerald-300 font-medium hover:underline transition-all"
              >
                Find a tutor to get started →
              </button>
            </div>
          ) : (
            bookings.map((booking, idx) => {
              const isUpcoming =
                booking.status === "CONFIRMED" ||
                booking.status === "confirmed" ||
                booking.status === "PENDING" ||
                booking.status === "pending";
              const isCompleted =
                booking.status === "COMPLETED" || booking.status === "completed";
              const canJoin =
                isUpcoming &&
                (booking.status === "CONFIRMED" || booking.status === "confirmed") &&
                isJoinable(booking.start_at);

              return (
                <div
                  key={booking.id}
                  className={`p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    idx !== bookings.length - 1
                      ? "border-b border-slate-200 dark:border-slate-800"
                      : ""
                  }`}
                >
                  <div className="flex items-center gap-4">
                    {/* Subject Icon */}
                    <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 text-lg">
                      {getSubjectIcon(booking.subject_name)}
                    </div>
                    {/* Session Info */}
                    <div>
                      <h4 className="font-semibold text-slate-900 dark:text-white">
                        {booking.subject_name || booking.topic || "Session"} with{" "}
                        {booking.tutor?.name || "Tutor"}
                      </h4>
                      <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <FiCalendar size={14} />
                          {new Date(booking.start_at).toLocaleDateString("en-US", {
                            weekday: "short",
                            month: "short",
                            day: "numeric",
                          })}
                        </span>
                        <span className="flex items-center gap-1">
                          <FiClock size={14} />
                          {new Date(booking.start_at).toLocaleTimeString("en-US", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    {canJoin && booking.join_url ? (
                      <a
                        href={booking.join_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(5,150,105,0.4)] hover:-translate-y-0.5"
                      >
                        <FiVideo size={18} /> Join Classroom
                      </a>
                    ) : isCompleted ? (
                      <button
                        onClick={() =>
                          router.push(`/bookings/${booking.id}/review`)
                        }
                        className="w-full md:w-auto border border-emerald-500/50 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 px-6 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        <FiStar size={18} /> Rate & Review
                      </button>
                    ) : (
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                          booking.status === "CONFIRMED" ||
                          booking.status === "confirmed"
                            ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                            : booking.status === "PENDING" ||
                              booking.status === "pending"
                            ? "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400"
                            : booking.status === "COMPLETED" ||
                              booking.status === "completed"
                            ? "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                        }`}
                      >
                        {booking.status.charAt(0).toUpperCase() +
                          booking.status.slice(1).toLowerCase()}
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Stats Summary */}
        {bookings.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-8">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {upcomingBookings.length}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Upcoming Sessions
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-slate-900 dark:text-white">
                {completedBookings.length}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Completed Lessons
              </p>
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center col-span-2 md:col-span-1">
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {bookings.length}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Total Sessions
              </p>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
