"use client";

/**
 * Bookings page content - displays and manages user bookings
 * Uses new BookingDTO schema and booking cards
 */

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { FiCalendar } from "react-icons/fi";
import { auth, bookings } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { User } from "@/types";
import { BookingDTO, BookingListResponse } from "@/types/booking";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
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

  // Tab configuration
  const tabs = [
    { key: "upcoming" as StatusFilter, label: "Upcoming", count: 0 },
    { key: "pending" as StatusFilter, label: "Pending", count: 0 },
    { key: "completed" as StatusFilter, label: "Completed", count: 0 },
    { key: "cancelled" as StatusFilter, label: "Cancelled", count: 0 },
  ];

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const isTutor = authUtils.isTutor(user);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Bookings</h1>
        <p className="text-gray-600 mt-2">
          {isTutor ? "Manage your tutoring sessions" : "Track your learning sessions"}
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-8">
        <div className="border-b border-gray-200">
          <nav className="flex gap-8">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => {
                  setSelectedTab(tab.key);
                  setPage(1);
                }}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  selectedTab === tab.key
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                {tab.label}
                {total > 0 && selectedTab === tab.key && (
                  <span className="ml-2 py-0.5 px-2 rounded-full text-xs bg-primary-100 text-primary-600">
                    {total}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Bookings List */}
      <div className="space-y-4">
        {bookingsList.map((booking) =>
          isTutor ? (
            <BookingCardTutor
              key={booking.id}
              booking={booking}
              onConfirm={handleConfirmBooking}
              onDecline={handleDeclineBooking}
              onCancel={handleCancelBooking}
              onMarkNoShow={handleMarkStudentNoShow}
              onAddNotes={handleAddNotes}
            />
          ) : (
            <BookingCardStudent
              key={booking.id}
              booking={booking}
              onCancel={handleCancelBooking}
              onReschedule={handleReschedule}
              onMarkNoShow={handleMarkTutorNoShow}
            />
          )
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="mt-8 flex justify-center gap-2">
          <Button
            variant="outline"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="px-4 py-2">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <Button
            variant="outline"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(total / 20)}
          >
            Next
          </Button>
        </div>
      )}

      {/* Empty State */}
      {bookingsList.length === 0 && !loading && (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <FiCalendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            No {selectedTab} bookings
          </h3>
          <p className="text-gray-600 mb-6">
            {authUtils.isStudent(user)
              ? "Book a tutor to get started with your learning journey"
              : "Your tutoring sessions will appear here"}
          </p>
        </div>
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
  );
}
