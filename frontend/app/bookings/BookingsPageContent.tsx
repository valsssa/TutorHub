"use client";

/**
 * Bookings page content - displays and manages user bookings
 * Uses new BookingDTO schema and booking cards
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { FiCalendar, FiClock, FiTrendingUp, FiXCircle } from "react-icons/fi";
import { auth, bookings } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { User } from "@/types";
import { BookingDTO, BookingListResponse } from "@/types/booking";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import AppShell from "@/components/AppShell";
import BookingCardStudent from "@/components/bookings/BookingCardStudent";
import BookingCardTutor from "@/components/bookings/BookingCardTutor";
import RescheduleBookingModal from "@/components/modals/RescheduleBookingModal";
import ViewNotesModal from "@/components/modals/ViewNotesModal";
import CancelBookingModal from "@/components/modals/CancelBookingModal";

type StatusFilter = "upcoming" | "pending" | "completed" | "cancelled";

export default function BookingsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [bookingsList, setBookingsList] = useState<BookingDTO[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [rescheduleBooking, setRescheduleBooking] = useState<BookingDTO | null>(null);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [notesBooking, setNotesBooking] = useState<BookingDTO | null>(null);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [cancelBooking, setCancelBooking] = useState<BookingDTO | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);

  const statusParam = searchParams?.get("status") as StatusFilter | null;
  const [selectedTab, setSelectedTab] = useState<StatusFilter>(
    statusParam && ["upcoming", "pending", "completed", "cancelled"].includes(statusParam)
      ? statusParam
      : "upcoming"
  );

  useEffect(() => {
    if (statusParam && ["upcoming", "pending", "completed", "cancelled"].includes(statusParam)) {
      setSelectedTab(statusParam);
    }
  }, [statusParam]);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [currentUser, bookingsData] = await Promise.all([
        auth.getCurrentUser(),
        bookings.list({
          status: selectedTab,
          role: undefined, // Auto-detected by backend based on user role
          page,
          page_size: 20,
        }),
      ]);
      setUser(currentUser);
      setBookingsList(bookingsData.bookings || []);
      setTotal(bookingsData.total || 0);
    } catch (error) {
      showError("Failed to load bookings");
      setBookingsList([]);
    } finally {
      setLoading(false);
    }
  }, [selectedTab, page, showError]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Student action handlers
  const handleCancelBooking = useCallback(
    (bookingId: number) => {
      const booking = bookingsList.find((b) => b.id === bookingId);
      if (booking) {
        setCancelBooking(booking);
        setShowCancelModal(true);
      }
    },
    [bookingsList]
  );

  const handleConfirmCancel = useCallback(
    async (reason?: string) => {
      if (!cancelBooking) return;

      try {
        await bookings.cancel(cancelBooking.id, { reason });
        showSuccess("Booking cancelled successfully");
        setShowCancelModal(false);
        setCancelBooking(null);
        loadData();
      } catch (error) {
        showError("Failed to cancel booking");
        throw error; // Re-throw so modal can handle it
      }
    },
    [cancelBooking, loadData, showError, showSuccess]
  );

  const handleReschedule = useCallback(
    (bookingId: number) => {
      const booking = bookingsList.find((b) => b.id === bookingId);
      if (booking) {
        setRescheduleBooking(booking);
        setShowRescheduleModal(true);
      }
    },
    [bookingsList]
  );

  const handleConfirmReschedule = useCallback(
    async (newStartTime: string) => {
      if (!rescheduleBooking) return;

      try {
        await bookings.reschedule(rescheduleBooking.id, { new_start_at: newStartTime });
        showSuccess("Booking rescheduled successfully");
        setShowRescheduleModal(false);
        setRescheduleBooking(null);
        loadData();
      } catch (error) {
        showError("Failed to reschedule booking");
        throw error; // Re-throw so modal can handle it
      }
    },
    [rescheduleBooking, loadData, showSuccess, showError]
  );

  const handleMarkTutorNoShow = useCallback(
    async (bookingId: number) => {
      const confirmed = confirm("Are you sure you want to report the tutor as no-show?");
      if (!confirmed) return;

      const notes = prompt("Please provide additional details (optional):");
      if (notes === null) return;

      try {
        await bookings.markTutorNoShow(bookingId, notes || undefined);
        showSuccess("Tutor no-show reported");
        loadData();
      } catch (error) {
        showError("Failed to report no-show");
      }
    },
    [loadData, showError, showSuccess]
  );

  // Tutor action handlers
  const handleConfirmBooking = useCallback(
    async (bookingId: number) => {
      const notes = prompt("Add notes for the student (optional):");
      if (notes === null) return;

      try {
        await bookings.confirm(bookingId, notes || undefined);
        showSuccess("Booking confirmed successfully");
        loadData();
      } catch (error) {
        showError("Failed to confirm booking");
      }
    },
    [loadData, showError, showSuccess]
  );

  const handleDeclineBooking = useCallback(
    async (bookingId: number) => {
      const reason = prompt("Please provide a reason for declining:");
      if (!reason) {
        showError("Reason is required to decline a booking");
        return;
      }

      try {
        await bookings.decline(bookingId, reason);
        showSuccess("Booking declined");
        loadData();
      } catch (error) {
        showError("Failed to decline booking");
      }
    },
    [loadData, showError, showSuccess]
  );

  const handleMarkStudentNoShow = useCallback(
    async (bookingId: number) => {
      const confirmed = confirm("Are you sure you want to mark the student as no-show?");
      if (!confirmed) return;

      const notes = prompt("Please provide additional details (optional):");
      if (notes === null) return;

      try {
        await bookings.markStudentNoShow(bookingId, notes || undefined);
        showSuccess("Student no-show reported");
        loadData();
      } catch (error) {
        showError("Failed to report no-show");
      }
    },
    [loadData, showError, showSuccess]
  );

  const handleAddNotes = useCallback(
    (bookingId: number) => {
      const booking = bookingsList.find((b) => b.id === bookingId);
      if (booking) {
        setNotesBooking(booking);
        setShowNotesModal(true);
      }
    },
    [bookingsList]
  );

  const handleTabChange = useCallback(
    (tab: StatusFilter) => {
      setSelectedTab(tab);
      setPage(1);
      router.push(`/bookings?status=${tab}`, { scroll: false });
    },
    [router]
  );

  // Tab configuration with icons
  const tabs = [
    { 
      key: "upcoming" as StatusFilter, 
      label: "Upcoming", 
      icon: FiClock,
      gradient: "from-blue-600 via-indigo-500 to-purple-600"
    },
    { 
      key: "pending" as StatusFilter, 
      label: "Pending", 
      icon: FiClock,
      gradient: "from-yellow-600 via-orange-500 to-red-600"
    },
    { 
      key: "completed" as StatusFilter, 
      label: "Completed", 
      icon: FiTrendingUp,
      gradient: "from-emerald-600 via-teal-500 to-green-600"
    },
    { 
      key: "cancelled" as StatusFilter, 
      label: "Cancelled", 
      icon: FiXCircle,
      gradient: "from-gray-600 via-slate-500 to-zinc-600"
    },
  ];

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  const isTutor = authUtils.isTutor(user);
  const selectedTabConfig = tabs.find(t => t.key === selectedTab);

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header Card with Gradient */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`bg-gradient-to-r ${selectedTabConfig?.gradient || "from-blue-600 via-indigo-500 to-purple-600"} rounded-2xl shadow-lg p-6 md:p-8 text-white`}
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2 flex items-center gap-3">
                <FiCalendar className="w-8 h-8" />
                My Bookings
              </h1>
              <p className="text-white/90 text-sm md:text-base">
                {isTutor ? "Manage your tutoring sessions" : "Track your learning sessions"}
              </p>
            </div>
            {total > 0 && (
              <div className="bg-white/20 backdrop-blur-sm rounded-xl px-6 py-4 text-center">
                <p className="text-white/80 text-sm mb-1">Total {selectedTab}</p>
                <p className="text-3xl font-bold">{total}</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden"
        >
          <div className="flex gap-1 p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = selectedTab === tab.key;
              return (
                <button
                  key={tab.key}
                  onClick={() => handleTabChange(tab.key)}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium text-sm transition-all ${
                    isActive
                      ? "bg-gradient-to-r " + tab.gradient + " text-white shadow-md"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "" : ""}`} />
                  <span>{tab.label}</span>
                  {isActive && total > 0 && (
                    <span className="bg-white/20 backdrop-blur-sm px-2 py-0.5 rounded-full text-xs font-bold">
                      {total}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Bookings List */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner />
          </div>
        ) : bookingsList.length > 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="space-y-4"
          >
            {bookingsList.map((booking, index) => (
              <motion.div
                key={booking.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                {isTutor ? (
                  <BookingCardTutor
                    booking={booking}
                    onConfirm={handleConfirmBooking}
                    onDecline={handleDeclineBooking}
                    onCancel={handleCancelBooking}
                    onMarkNoShow={handleMarkStudentNoShow}
                    onAddNotes={handleAddNotes}
                  />
                ) : (
                  <BookingCardStudent
                    booking={booking}
                    onCancel={handleCancelBooking}
                    onReschedule={handleReschedule}
                    onMarkNoShow={handleMarkTutorNoShow}
                  />
                )}
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-12 text-center"
          >
            <div className="max-w-md mx-auto">
              <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center">
                <FiCalendar className="w-10 h-10 text-slate-400 dark:text-slate-500" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                No {selectedTab} bookings
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                {authUtils.isStudent(user)
                  ? "Book a tutor to get started with your learning journey"
                  : "Your tutoring sessions will appear here"}
              </p>
              {authUtils.isStudent(user) && (
                <Button
                  variant="primary"
                  onClick={() => router.push("/tutors")}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
                >
                  Browse Tutors
                </Button>
              )}
            </div>
          </motion.div>
        )}

        {/* Pagination */}
        {total > 20 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex justify-center items-center gap-4 pt-4"
          >
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Previous
            </Button>
            <span className="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-400">
              Page {page} of {Math.ceil(total / 20)}
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / 20)}
              className="dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Next
            </Button>
          </motion.div>
        )}

      {/* Reschedule Modal */}
      <RescheduleBookingModal
        booking={rescheduleBooking}
        isOpen={showRescheduleModal}
        onClose={() => {
          setShowRescheduleModal(false);
          setRescheduleBooking(null);
        }}
        onConfirm={handleConfirmReschedule}
      />

      {/* View Notes Modal */}
      <ViewNotesModal
        booking={notesBooking}
        isOpen={showNotesModal}
        onClose={() => {
          setShowNotesModal(false);
          setNotesBooking(null);
        }}
        userRole={user?.role || "student"}
      />

      {/* Cancel Booking Modal */}
      <CancelBookingModal
        isOpen={showCancelModal}
        onClose={() => {
          setShowCancelModal(false);
          setCancelBooking(null);
        }}
        onConfirm={handleConfirmCancel}
        bookingId={cancelBooking?.id}
        tutorName={cancelBooking?.tutor?.name}
      />
      </div>
    </AppShell>
  );
}
