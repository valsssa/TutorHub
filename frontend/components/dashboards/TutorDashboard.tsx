"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  FiCalendar,
  FiUser,
  FiClock,
  FiDollarSign,
  FiUsers,
  FiStar,
  FiVideo,
  FiMessageSquare,
  FiFileText,
  FiPlus,
  FiSettings,
  FiArrowUpRight,
} from "react-icons/fi";
import { User, TutorProfile } from "@/types";
import { BookingDTO } from "@/types/booking";
import AppShell from "@/components/AppShell";
import Badge from "@/components/Badge";

interface TutorDashboardProps {
  user: User;
  bookings: BookingDTO[];
  profile: TutorProfile | null;
  onAvatarChange: (url: string | null) => void;
  onProfileUpdate: (profile: TutorProfile) => void;
}

export default function TutorDashboard({
  user,
  bookings,
  profile,
}: TutorDashboardProps) {
  const router = useRouter();

  // Memoize filtered bookings
  const pendingBookings = useMemo(
    () =>
      bookings.filter(
        (b) => b.status === "PENDING" || b.status === "pending"
      ),
    [bookings]
  );
  const confirmedBookings = useMemo(
    () =>
      bookings.filter(
        (b) => b.status === "CONFIRMED" || b.status === "confirmed"
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

  // Memoize earnings calculations
  const totalEarnings = useMemo(
    () =>
      completedBookings.reduce(
        (sum, b) => sum + b.tutor_earnings_cents / 100,
        0
      ),
    [completedBookings]
  );

  // Get unique students count
  const totalStudents = useMemo(() => {
    const studentIds = new Set(bookings.map((b) => b.student?.id));
    return studentIds.size;
  }, [bookings]);

  // Get all upcoming sessions (confirmed + pending) sorted by time
  const upcomingSessions = useMemo(
    () =>
      [...confirmedBookings, ...pendingBookings]
        .sort(
          (a, b) =>
            new Date(a.start_at).getTime() - new Date(b.start_at).getTime()
        ),
    [confirmedBookings, pendingBookings]
  );

  // Helper for relative date labels
  const getRelativeDateLabel = (dateStr: string): string => {
    const date = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    const sessionDate = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate()
    );

    if (sessionDate.getTime() === today.getTime()) return "Today";
    if (sessionDate.getTime() === tomorrow.getTime()) return "Tomorrow";

    const diffTime = sessionDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays > 1 && diffDays < 7) return `In ${diffDays} days`;

    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  // Format time range
  const formatTimeRange = (startAt: string): string => {
    const date = new Date(startAt);
    const start = date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    const end = new Date(date.getTime() + 50 * 60000).toLocaleTimeString(
      "en-US",
      { hour: "2-digit", minute: "2-digit", hour12: false }
    );
    return `${start} – ${end}`;
  };

  // Determine verification status
  const getVerificationStatus = (): "verified" | "pending" | "unverified" => {
    if (!profile) return "unverified";
    if (profile.is_approved) return "verified";
    if (
      profile.profile_status === "pending_approval" ||
      profile.profile_status === "under_review"
    )
      return "pending";
    return "unverified";
  };

  const verificationStatus = getVerificationStatus();

  if (!profile) {
    return (
      <AppShell user={user}>
        <div className="container mx-auto px-4 py-16 max-w-4xl">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-12 text-center">
            <div className="w-20 h-20 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiUser className="w-10 h-10 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
              Welcome to TutorHub!
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400 mb-8 max-w-md mx-auto">
              Complete your tutor profile to start accepting bookings and
              connect with eager students.
            </p>
            <button
              onClick={() => router.push("/tutor/profile")}
              className="px-8 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 transition-all"
            >
              Complete Your Profile
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Tutor Command Center
            </h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <p className="text-lg text-slate-700 dark:text-slate-300 font-medium">
                Welcome, {profile.title}
              </p>

              {verificationStatus === "verified" && (
                <Badge variant="verified">Verified Tutor</Badge>
              )}
              {verificationStatus === "pending" && (
                <Badge variant="pending">Verification Pending</Badge>
              )}
              {verificationStatus === "unverified" && (
                <span className="text-xs bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 px-2 py-0.5 rounded font-medium">
                  Unverified
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              You have {upcomingSessions.length} upcoming sessions.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/tutor/profile")}
              className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-700 dark:text-slate-300"
            >
              Edit Profile
            </button>
            <button
              onClick={() => router.push("/tutor/availability")}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-500 shadow-lg shadow-emerald-500/20 transition-colors flex items-center gap-2"
            >
              <FiCalendar size={16} /> Update Schedule
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Earnings */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-emerald-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Total Earnings
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                ${totalEarnings.toLocaleString()}
              </div>
              <div className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                <span className="flex items-center">
                  <FiArrowUpRight size={12} /> {completedBookings.length}{" "}
                  sessions
                </span>
              </div>
            </div>
          </div>

          {/* Hours */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-blue-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Hours Taught
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                {profile.total_sessions || completedBookings.length}h
              </div>
              <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 font-medium">
                <span className="flex items-center">
                  <FiArrowUpRight size={12} /> {confirmedBookings.length}{" "}
                  upcoming
                </span>
              </div>
            </div>
          </div>

          {/* Active Students */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-purple-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Active Students
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                {totalStudents}
              </div>
              <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400 font-medium">
                <span>{pendingBookings.length} pending</span>
              </div>
            </div>
          </div>

          {/* Rating */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm relative overflow-hidden group">
            <div className="absolute right-0 top-0 w-24 h-24 bg-amber-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
            <div className="relative z-10">
              <div className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">
                Overall Rating
              </div>
              <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                {profile.total_reviews > 0
                  ? Number(profile.average_rating).toFixed(1)
                  : "—"}
                {profile.total_reviews > 0 && (
                  <FiStar className="text-amber-500 fill-amber-500" size={24} />
                )}
              </div>
              <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 font-medium">
                <span>{profile.total_reviews} reviews</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Left Column */}
          <div className="xl:col-span-2 space-y-8">
            {/* Upcoming Sessions List */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                  <FiVideo size={20} className="text-emerald-500" /> Upcoming
                  Sessions
                </h3>
                <button
                  onClick={() => router.push("/bookings")}
                  className="text-sm font-bold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300 transition-colors"
                >
                  See all
                </button>
              </div>

              <div className="space-y-4">
                {upcomingSessions.length === 0 ? (
                  <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                    <FiCalendar
                      size={32}
                      className="mx-auto mb-3 opacity-50"
                    />
                    <p>No upcoming sessions.</p>
                    <button
                      onClick={() => router.push("/tutor/availability")}
                      className="mt-3 text-emerald-600 dark:text-emerald-400 hover:underline text-sm font-medium"
                    >
                      Set up your availability →
                    </button>
                  </div>
                ) : (
                  upcomingSessions.map((session) => {
                    const studentName =
                      session.student?.name || "Student";
                    const isPending = session.status === "PENDING" || session.status === "pending";
                    const isConfirmed = session.status === "CONFIRMED" || session.status === "confirmed";
                    return (
                      <div
                        key={session.id}
                        className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:shadow-md transition-all border border-transparent hover:border-emerald-100 dark:hover:border-emerald-900/30 group gap-4"
                      >
                        <div className="flex items-center gap-4">
                          {/* Avatar */}
                          <div className="w-12 h-12 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-200 font-bold text-xl shadow-sm border border-slate-300 dark:border-slate-600">
                            {studentName.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-slate-900 dark:text-white text-base">
                                {studentName}
                              </h4>
                              {isPending && (
                                <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded font-medium">
                                  Pending
                                </span>
                              )}
                              {isConfirmed && (
                                <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded font-medium">
                                  Confirmed
                                </span>
                              )}
                            </div>
                            <p className="text-slate-500 dark:text-slate-400 text-sm">
                              {getRelativeDateLabel(session.start_at)},{" "}
                              {formatTimeRange(session.start_at)}
                            </p>
                            {session.subject_name && (
                              <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                                {session.subject_name}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-slate-400 justify-end">
                          {isPending && (
                            <button
                              onClick={() => router.push(`/bookings?status=pending`)}
                              className="px-3 py-1.5 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-500 font-medium"
                            >
                              Review
                            </button>
                          )}
                          <button
                            className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm"
                            title="Lesson Notes"
                          >
                            <FiFileText size={20} />
                          </button>
                          {session.join_url && isConfirmed && (
                            <a
                              href={session.join_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm"
                              title="Start Video Call"
                            >
                              <FiVideo size={20} />
                            </a>
                          )}
                          <button
                            onClick={() => router.push("/messages")}
                            className="p-2 hover:bg-white dark:hover:bg-slate-700 rounded-lg hover:text-emerald-600 transition-colors shadow-sm"
                            title="Message"
                          >
                            <FiMessageSquare size={20} />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Earnings Summary */}
            {completedBookings.length > 0 && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center gap-2">
                    <FiDollarSign size={20} className="text-emerald-500" />{" "}
                    Earnings Summary
                  </h3>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl">
                    <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                      ${totalEarnings.toFixed(0)}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Total Earned
                    </p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {completedBookings.length}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Completed
                    </p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-xl">
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      $
                      {completedBookings.length > 0
                        ? (totalEarnings / completedBookings.length).toFixed(0)
                        : 0}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                      Avg/Session
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Quick Schedule Widget */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <FiClock size={20} className="text-emerald-500" /> Quick
                Schedule
              </h3>

              <div className="space-y-3">
                <button
                  onClick={() => router.push("/tutor/availability")}
                  className="w-full py-3.5 px-4 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 hover:bg-emerald-500 transition-all flex items-center justify-center gap-2"
                >
                  <FiCalendar size={18} /> Manage Availability
                </button>

                <button
                  onClick={() => router.push("/bookings")}
                  className="w-full py-3 px-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                >
                  <FiCalendar size={18} /> View Calendar
                </button>

                <button
                  onClick={() => router.push("/tutor/profile")}
                  className="w-full py-3 px-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                >
                  <FiSettings size={18} /> Edit Profile
                </button>
              </div>
            </div>

            {/* Pending Requests */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
              <div className="p-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="font-bold text-slate-900 dark:text-white text-sm uppercase tracking-wide">
                  Pending Requests
                </h3>
              </div>
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {pendingBookings.length === 0 ? (
                  <div className="p-6 text-center text-slate-500 dark:text-slate-400">
                    <p className="text-sm">No pending requests</p>
                  </div>
                ) : (
                  pendingBookings.slice(0, 3).map((booking) => {
                    const studentName =
                      booking.student?.name || "Student";
                    return (
                      <div
                        key={booking.id}
                        className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 text-white flex items-center justify-center text-xs font-bold">
                              {studentName.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="text-sm font-semibold text-slate-900 dark:text-white">
                                {studentName}
                              </div>
                              <div className="text-xs text-slate-500 dark:text-slate-400">
                                {booking.subject_name || "Session"} •{" "}
                                {new Date(booking.start_at).toLocaleDateString(
                                  "en-US",
                                  { month: "short", day: "numeric" }
                                )}
                              </div>
                            </div>
                          </div>
                          <span className="text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded">
                            Pending
                          </span>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() =>
                              router.push(`/bookings?status=pending`)
                            }
                            className="flex-1 py-1.5 text-xs bg-emerald-600 text-white rounded hover:bg-emerald-500 font-medium"
                          >
                            Review
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
              {pendingBookings.length > 3 && (
                <div className="p-3 border-t border-slate-200 dark:border-slate-800 text-center">
                  <button
                    onClick={() => router.push("/bookings?status=pending")}
                    className="text-sm text-emerald-600 dark:text-emerald-400 hover:underline font-medium"
                  >
                    View all {pendingBookings.length} requests →
                  </button>
                </div>
              )}
            </div>

            {/* Profile Stats */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
              <h3 className="font-bold text-lg text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <FiUsers size={20} className="text-emerald-500" /> Profile Stats
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Hourly Rate
                  </span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    ${profile.hourly_rate}/hr
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Experience
                  </span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {profile.experience_years} years
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    Status
                  </span>
                  <span
                    className={`text-sm font-bold ${
                      profile.is_approved
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-amber-600 dark:text-amber-400"
                    }`}
                  >
                    {profile.is_approved ? "✓ Approved" : "Pending Review"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
