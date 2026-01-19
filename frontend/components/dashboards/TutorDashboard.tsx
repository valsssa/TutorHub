"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  FiCalendar,
  FiUser,
  FiClock,
  FiDollarSign,
} from "react-icons/fi";
import { User, TutorProfile } from "@/types";
import { BookingDTO } from "@/types/booking";
import Button from "@/components/Button";
import AppShell from "@/components/AppShell";
import { useTutorPhoto } from "@/lib/useTutorPhoto";

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
  onAvatarChange,
  onProfileUpdate,
}: TutorDashboardProps) {
  const router = useRouter();
  const tutorPhotoController = useTutorPhoto({
    initialUrl: profile?.profile_photo_url ?? null,
    onUploaded: onProfileUpdate,
  });

  // Memoize filtered bookings
  const pendingBookings = useMemo(() => bookings.filter((b) => b.status === "PENDING" || b.status === "pending"), [bookings]);
  const confirmedBookings = useMemo(() => bookings.filter((b) => b.status === "CONFIRMED" || b.status === "confirmed"), [bookings]);
  const completedThisWeek = useMemo(() => {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    return bookings.filter(
      (b) => (b.status === "COMPLETED" || b.status === "completed") && new Date(b.start_at) >= oneWeekAgo
    );
  }, [bookings]);

  // Memoize earnings calculations
  const totalEarnings = useMemo(
    () =>
      bookings
        .filter((b) => b.status === "COMPLETED" || b.status === "completed")
        .reduce((sum, b) => sum + (b.tutor_earnings_cents / 100), 0),
    [bookings]
  );

  const weeklyEarnings = useMemo(
    () => completedThisWeek.reduce((sum, b) => sum + (b.tutor_earnings_cents / 100), 0),
    [completedThisWeek]
  );

  // Get upcoming sessions (next 3)
  const upcomingSessions = useMemo(
    () =>
      confirmedBookings
        .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
        .slice(0, 3),
    [confirmedBookings]
  );

  // Determine tutor state for smart UI adaptation
  const hasAvailability = profile?.availabilities && profile.availabilities.length > 0;
  const hasBookings = bookings.length > 0;
  const hasEarnings = totalEarnings > 0;
  const isNewTutor = !hasBookings && profile?.total_sessions === 0;

  if (!profile) {
    return (
      <AppShell user={user}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="bg-gradient-to-br from-primary-50 to-pink-50 rounded-2xl shadow-soft-lg p-12 text-center border-2 border-primary-100">
            <div className="w-24 h-24 bg-gradient-to-br from-primary-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiUser className="w-12 h-12 text-primary-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Welcome to TutorHub! 🎓
            </h2>
            <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
              Complete your tutor profile to start accepting bookings and connect with eager students
            </p>
            <Button
              variant="primary"
              size="lg"
              onClick={() => router.push("/tutor/profile")}
              className="shadow-lg hover:shadow-xl"
            >
              Complete Your Profile
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  // Determine primary action based on tutor state
  const getPrimaryAction = () => {
    if (pendingBookings.length > 0) {
      return {
        label: "Review Requests",
        onClick: () => router.push("/bookings?status=pending"),
        variant: "primary" as const,
      };
    }
    if (!hasAvailability) {
      return {
        label: "Add Availability",
        onClick: () => router.push("/tutor/availability"),
        variant: "primary" as const,
      };
    }
    if (confirmedBookings.length > 0) {
      return {
        label: "View Calendar",
        onClick: () => router.push("/bookings"),
        variant: "secondary" as const,
      };
    }
    return null;
  };

  const primaryAction = getPrimaryAction();

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Action-Focused Hero Banner */}
        <div className="bg-gradient-to-r from-primary-500 via-pink-500 to-purple-600 rounded-2xl shadow-soft-lg p-6 text-white animate-fadeIn">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex-1">
              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                Welcome back, {profile.title}! 👋
              </h1>
              <p className="text-white/90 text-sm md:text-base">
                {pendingBookings.length > 0
                  ? `${pendingBookings.length} new booking ${pendingBookings.length === 1 ? 'request' : 'requests'} waiting`
                  : confirmedBookings.length > 0
                    ? `${confirmedBookings.length} upcoming ${confirmedBookings.length === 1 ? 'session' : 'sessions'}`
                    : "Ready to start teaching?"}
              </p>
            </div>
            {primaryAction && (
              <Button
                variant="secondary"
                onClick={primaryAction.onClick}
                className={`font-medium px-6 py-3 rounded-lg shadow-md ${
                  primaryAction.variant === "primary"
                    ? "!bg-white !text-pink-600 hover:!bg-white/90"
                    : "!bg-white/20 !text-white hover:!bg-white/30 !border-white/30"
                }`}
              >
                {primaryAction.label}
              </Button>
            )}
          </div>
        </div>

        {/* Action Cards - Simplified with One CTA Each */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Pending Requests Card - Always Visible */}
          <div
            className={`bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-all cursor-pointer ${
              pendingBookings.length > 0 ? 'ring-2 ring-accent-500 bg-accent-50/30' : ''
            }`}
            onClick={() => router.push("/bookings?status=pending")}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-3 rounded-xl ${
                pendingBookings.length > 0
                  ? 'bg-accent-500 text-white'
                  : 'bg-gray-100 text-gray-400'
              }`}>
                <FiClock className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 text-lg">Pending Requests</h3>
                <p className="text-sm text-gray-600">
                  {pendingBookings.length === 0
                    ? "No new requests"
                    : `${pendingBookings.length} ${pendingBookings.length === 1 ? 'request' : 'requests'} waiting`}
                </p>
              </div>
              {pendingBookings.length > 0 && (
                <span className="text-3xl font-bold text-accent-600">
                  {pendingBookings.length}
                </span>
              )}
            </div>
            <Button
              variant={pendingBookings.length > 0 ? "primary" : "ghost"}
              size="sm"
              className={`w-full ${
                pendingBookings.length > 0
                  ? 'bg-accent-500 hover:bg-accent-600'
                  : 'border-2 border-gray-200'
              }`}
              onClick={(e) => {
                e.stopPropagation();
                router.push("/bookings?status=pending");
              }}
            >
              {pendingBookings.length > 0 ? 'Review Requests →' : 'View Requests'}
            </Button>
          </div>

          {/* Upcoming Sessions Card - Always Visible */}
          <div
            className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-all cursor-pointer"
            onClick={() => router.push("/bookings?status=confirmed")}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className={`p-3 rounded-xl ${
                confirmedBookings.length > 0
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-400'
              }`}>
                <FiCalendar className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-gray-900 text-lg">Upcoming Sessions</h3>
                <p className="text-sm text-gray-600">
                  {confirmedBookings.length === 0
                    ? "No upcoming lessons"
                    : `${confirmedBookings.length} ${confirmedBookings.length === 1 ? 'session' : 'sessions'} scheduled`}
                </p>
              </div>
              {confirmedBookings.length > 0 && (
                <span className="text-3xl font-bold text-blue-600">
                  {confirmedBookings.length}
                </span>
              )}
            </div>
            <Button
              variant={confirmedBookings.length > 0 ? "primary" : "ghost"}
              size="sm"
              className={`w-full ${
                confirmedBookings.length > 0
                  ? 'bg-blue-500 hover:bg-blue-600'
                  : 'border-2 border-gray-200'
              }`}
              onClick={(e) => {
                e.stopPropagation();
                if (confirmedBookings.length > 0) {
                  router.push("/bookings?status=confirmed");
                } else if (!hasAvailability) {
                  router.push("/tutor/availability");
                } else {
                  router.push("/bookings");
                }
              }}
            >
              {confirmedBookings.length > 0
                ? 'View Calendar →'
                : !hasAvailability
                  ? 'Add Availability →'
                  : 'Schedule Lesson'}
            </Button>
          </div>
        </div>

        {/* Profile & Earnings Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Card - Simplified */}
          <div className="bg-white rounded-2xl shadow-soft p-6">
            <h3 className="font-bold text-gray-900 text-lg mb-4 flex items-center gap-2">
              <FiUser className="text-primary-600" />
              Your Profile
            </h3>
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between p-3 bg-purple-50 rounded-xl">
                <span className="text-sm font-medium text-gray-700">Status</span>
                <span className={`text-sm font-bold ${
                  hasAvailability ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {hasAvailability ? '🟢 Visible' : '⚫ Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-xl">
                <span className="text-sm font-medium text-gray-700">Hourly Rate</span>
                <span className="text-sm font-bold text-gray-900">${profile.hourly_rate}/hr</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-xl">
                <span className="text-sm font-medium text-gray-700">Rating</span>
                <span className="text-sm font-bold text-gray-900">
                  {profile.total_reviews > 0
                    ? `⭐ ${Number(profile.average_rating).toFixed(1)} (${profile.total_reviews})`
                    : '—'}
                </span>
              </div>
            </div>
            <Button
              variant="primary"
              size="sm"
              className="w-full"
              onClick={() => router.push("/tutor/profile")}
            >
              Manage Profile →
            </Button>
          </div>

          {/* Weekly Earnings - Only Show if Has Data */}
          {(hasEarnings || weeklyEarnings > 0) && (
            <div className="lg:col-span-2 bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl shadow-soft-lg p-6 text-white">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <FiDollarSign className="w-6 h-6" />
                    <h3 className="text-lg font-bold">Weekly Earnings</h3>
                  </div>
                  <p className="text-4xl font-bold mb-2">${weeklyEarnings.toFixed(2)}</p>
                  <p className="text-purple-100 text-sm">
                    {completedThisWeek.length} session{completedThisWeek.length !== 1 ? 's' : ''} completed this week
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => router.push("/bookings?status=completed")}
                  className="bg-white/20 hover:bg-white/30 text-white border-white/30"
                >
                  View Details
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Upcoming Sessions Detail - Only Show If Has Sessions */}
        {upcomingSessions.length > 0 && (
          <div className="bg-white rounded-2xl shadow-soft p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <FiCalendar className="w-5 h-5 text-blue-600" />
                Next Sessions
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/bookings")}
                className="text-primary-600 hover:text-primary-700"
              >
                View All
              </Button>
            </div>

            <div className="space-y-4">
              {upcomingSessions.map((booking) => (
                <div
                  key={booking.id}
                  className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl border-l-4 border-blue-500 hover:shadow-md transition-all cursor-pointer"
                  onClick={() => router.push(`/bookings`)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <p className="font-semibold text-gray-900">
                      {booking.topic || "Session"}
                    </p>
                    <span className="text-sm font-bold text-blue-600">
                      ${(booking.tutor_earnings_cents / 100).toFixed(2)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                    <FiCalendar className="w-4 h-4" />
                    {new Date(booking.start_at).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <FiClock className="w-4 h-4" />
                    {new Date(booking.start_at).toLocaleTimeString("en-US", {
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
