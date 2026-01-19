"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  FiBook,
  FiCalendar,
  FiUsers,
  FiStar,
  FiAward,
  FiTarget,
} from "react-icons/fi";
import { User } from "@/types";
import { BookingDTO } from "@/types/booking";
import Button from "@/components/Button";
import StatCard from "@/components/StatCard";
import ProgressBar from "@/components/ProgressBar";
import AppShell from "@/components/AppShell";

interface StudentDashboardProps {
  user: User;
  bookings: BookingDTO[];
  onAvatarChange: (url: string | null) => void;
}

export default function StudentDashboard({
  user,
  bookings,
  onAvatarChange,
}: StudentDashboardProps) {
  const router = useRouter();

  // Memoize filtered bookings to prevent unnecessary recalculations
  const upcomingBookings = useMemo(() => bookings.filter((b) => b.status === "CONFIRMED" || b.status === "confirmed"), [bookings]);
  const pendingBookings = useMemo(() => bookings.filter((b) => b.status === "PENDING" || b.status === "pending"), [bookings]);
  const completedBookings = useMemo(() => bookings.filter((b) => b.status === "COMPLETED" || b.status === "completed"), [bookings]);

  // Calculate learning streak (mock for now)
  const learningStreak = 3
  const profileCompletion = user.avatar_url ? 80 : 60

  const getTimeGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return '☀️ Good morning'
    if (hour < 18) return '👋 Good afternoon'
    return '🌙 Good evening'
  }

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Hero Banner */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-brand-rose via-pink-500 to-purple-500 rounded-2xl shadow-warm p-6 md:p-8 text-white"
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                {getTimeGreeting()}! Ready to learn? 🚀
              </h1>
              <p className="text-white/90 text-sm md:text-base">
                {upcomingBookings.length > 0
                  ? `You have ${upcomingBookings.length} upcoming ${upcomingBookings.length === 1 ? 'session' : 'sessions'} 📚`
                  : "Find an amazing tutor to start your journey 🌱"}
              </p>
            </div>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard
            label="Upcoming Sessions"
            value={upcomingBookings.length}
            icon={FiCalendar}
            color="blue"
            onClick={() => router.push('/bookings')}
          />
          <StatCard
            label="Completed Lessons"
            value={completedBookings.length}
            icon={FiStar}
            color="green"
            delta={completedBookings.length > 0 ? { value: '+2 this week', trend: 'up' } : undefined}
          />
          <StatCard
            label="Learning Streak 🔥"
            value={`${learningStreak} days`}
            icon={FiAward}
            color="amber"
          />
        </div>

        {/* Progress Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-2xl shadow-soft p-6"
        >
          <h2 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
            <FiTarget className="text-brand-rose" />
            Your Progress
          </h2>

          <div className="space-y-4">
            <ProgressBar
              value={profileCompletion}
              label="Profile Completion"
              color="rose"
              icon="👤"
            />

            {completedBookings.length > 0 && (
              <div className="pt-4 border-t border-gray-100">
                <p className="text-sm text-text-secondary mb-2">
                  💪 Keep it up! Students who practice 3× a week improve 2× faster
                </p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-brand-rose to-pink-600 rounded-2xl shadow-floating p-6 text-white cursor-pointer hover:scale-105 transition-transform"
            onClick={() => router.push("/tutors")}
          >
            <FiUsers className="w-12 h-12 mb-4 opacity-90" />
            <h3 className="text-2xl font-bold mb-2">Find Your Tutor 🎯</h3>
            <p className="mb-4 opacity-90 text-sm">
              Browse expert tutors and book your perfect match
            </p>
            <div className="inline-flex items-center gap-2 text-sm font-semibold">
              Explore now →
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-sky-500 to-blue-600 rounded-2xl shadow-floating p-6 text-white cursor-pointer hover:scale-105 transition-transform"
            onClick={() => router.push("/bookings")}
          >
            <FiCalendar className="w-12 h-12 mb-4 opacity-90" />
            <h3 className="text-2xl font-bold mb-2">Your Sessions 📅</h3>
            <p className="mb-4 opacity-90 text-sm">
              Manage upcoming and past learning sessions
            </p>
            <div className="inline-flex items-center gap-2 text-sm font-semibold">
              View bookings →
            </div>
          </motion.div>
        </div>

        {/* Recent Bookings */}
        {bookings.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl shadow-soft p-6"
          >
            <h2 className="text-lg font-bold text-text-primary mb-4 flex items-center gap-2">
              <FiBook className="text-brand-rose" />
              Recent Activity
            </h2>
            <div className="space-y-3">
              {bookings.slice(0, 5).map((booking, index) => (
                <motion.div
                  key={booking.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.05 }}
                  className="flex items-center justify-between p-4 border border-gray-100 rounded-xl hover:border-brand-rose hover:shadow-md transition-all cursor-pointer"
                  onClick={() => router.push('/bookings')}
                >
                  <div className="flex-1">
                    <p className="font-semibold text-text-primary">
                      {booking.topic || "Session"}
                    </p>
                    <p className="text-sm text-text-secondary mt-1">
                      {new Date(booking.start_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric'
                      })} at {new Date(booking.start_at).toLocaleTimeString('en-US', {
                        hour: 'numeric', minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      booking.status === "confirmed"
                        ? "bg-green-100 text-green-700"
                        : booking.status === "pending"
                          ? "bg-amber-100 text-amber-700"
                          : booking.status === "completed"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {booking.status}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {bookings.length === 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-gradient-to-br from-rose-50 to-pink-50 rounded-2xl shadow-soft p-12 text-center border-2 border-rose-100"
          >
            <div className="w-20 h-20 bg-gradient-to-br from-rose-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <FiBook className="w-10 h-10 text-brand-rose" />
            </div>
            <h3 className="text-2xl font-bold text-text-primary mb-3">
              No sessions yet 🌱
            </h3>
            <p className="text-text-secondary mb-6 max-w-md mx-auto">
              Start your learning adventure by finding the perfect tutor for your goals
            </p>
            <Button
              variant="primary"
              onClick={() => router.push("/tutors")}
              className="bg-brand-rose hover:bg-primary-600 shadow-warm"
            >
              Find Your First Tutor →
            </Button>
          </motion.div>
        )}
      </div>
    </AppShell>
  );
}
