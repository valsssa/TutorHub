"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  Calendar,
  Clock,
  User,
  MessageSquare,
  Video,
  MapPin,
  DollarSign,
  Star,
  AlertCircle,
  CheckCircle,
  XCircle,
  ExternalLink,
  Copy,
  Check,
  CalendarPlus,
  FileText,
  Flag,
  RefreshCw,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import StatusBadge from "@/components/StatusBadge";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import Modal from "@/components/Modal";
import TextArea from "@/components/TextArea";
import { bookings, auth } from "@/lib/api";
import { resolveAssetUrl } from "@/lib/media";
import { authUtils } from "@/lib/auth";
import { useToast } from "@/components/ToastContainer";
import type { BookingDTO, User as UserType } from "@/types";

export default function BookingDetailPage() {
  return (
    <ProtectedRoute>
      <BookingDetailContent />
    </ProtectedRoute>
  );
}

function BookingDetailContent() {
  const params = useParams();
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const bookingId = params?.id ? Number(params.id) : null;

  const [booking, setBooking] = useState<BookingDTO | null>(null);
  const [user, setUser] = useState<UserType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Modal states
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const loadBooking = useCallback(async () => {
    if (!bookingId) return;

    setLoading(true);
    setError(null);

    try {
      const [bookingData, userData] = await Promise.all([
        bookings.get(bookingId),
        auth.getCurrentUser(),
      ]);
      setBooking(bookingData);
      setUser(userData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load booking details");
    } finally {
      setLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    loadBooking();
  }, [loadBooking]);

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(String(bookingId));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const handleCancel = async () => {
    if (!booking) return;

    setActionLoading(true);
    try {
      await bookings.cancel(booking.id, cancelReason || undefined);
      showSuccess("Booking cancelled successfully");
      setShowCancelModal(false);
      loadBooking();
    } catch (err: any) {
      showError(err?.response?.data?.detail || "Failed to cancel booking");
    } finally {
      setActionLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!booking) return;

    setActionLoading(true);
    try {
      await bookings.confirm(booking.id);
      showSuccess("Booking confirmed!");
      loadBooking();
    } catch (err: any) {
      showError(err?.response?.data?.detail || "Failed to confirm booking");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDecline = async () => {
    if (!booking) return;

    setActionLoading(true);
    try {
      await bookings.decline(booking.id, cancelReason || undefined);
      showSuccess("Booking declined");
      setShowCancelModal(false);
      loadBooking();
    } catch (err: any) {
      showError(err?.response?.data?.detail || "Failed to decline booking");
    } finally {
      setActionLoading(false);
    }
  };

  // Determine user role in this booking
  const isStudent = user && authUtils.isStudent(user);
  const isTutor = user && authUtils.isTutor(user);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Error state
  if (error || !booking) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4">
        <div className="container mx-auto max-w-4xl">
          <EmptyState
            variant="error"
            title="Booking Not Found"
            description={error || "We couldn't find this booking."}
            action={{
              label: "Go to Bookings",
              onClick: () => router.push("/bookings"),
            }}
          />
        </div>
      </div>
    );
  }

  // Parse dates
  const startDate = new Date(booking.start_at);
  const endDate = new Date(booking.end_at);
  const now = new Date();
  const isUpcoming = startDate > now;
  const isInProgress = now >= startDate && now <= endDate;
  const isPast = now > endDate;

  // Determine what actions are available
  const canCancel =
    booking.session_state === "REQUESTED" ||
    (booking.session_state === "SCHEDULED" && isUpcoming);

  const canReschedule =
    booking.session_state === "SCHEDULED" && isUpcoming;

  const canJoin =
    booking.session_state === "SCHEDULED" &&
    booking.join_url &&
    (isUpcoming || isInProgress);

  const canAcceptDecline =
    isTutor && booking.session_state === "REQUESTED";

  const canReview =
    isStudent &&
    booking.session_state === "ENDED" &&
    booking.session_outcome === "COMPLETED";

  const canDispute =
    booking.session_state === "ENDED" &&
    booking.dispute_state === "NONE" &&
    isPast;

  // Format times
  const formatDate = (date: Date) =>
    date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  const formatTime = (date: Date) =>
    date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });

  const formatPrice = (cents: number, currency: string) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(cents / 100);

  // Time until session
  const getTimeUntil = () => {
    const diff = startDate.getTime() - now.getTime();
    if (diff < 0) return null;

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (days > 0) return `${days} day${days > 1 ? "s" : ""} away`;
    if (hours > 0) return `${hours} hour${hours > 1 ? "s" : ""} away`;
    return `${minutes} minute${minutes > 1 ? "s" : ""} away`;
  };

  const timeUntil = getTimeUntil();

  // Counterparty info
  const counterparty = isStudent ? booking.tutor : booking.student;
  const counterpartyRole = isStudent ? "Tutor" : "Student";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-12">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Bookings", href: "/bookings" },
              { label: `Booking #${bookingId}` },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Status Banner */}
        {isInProgress && (
          <div className="mb-6 p-4 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center gap-3 animate-pulse">
            <Video className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span className="font-medium text-emerald-800 dark:text-emerald-200">
              Session in progress
            </span>
            {booking.join_url && (
              <a
                href={booking.join_url}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-auto"
              >
                <Button variant="primary" size="sm">
                  Join Now
                  <ExternalLink className="w-4 h-4 ml-1" />
                </Button>
              </a>
            )}
          </div>
        )}

        {timeUntil && booking.session_state === "SCHEDULED" && (
          <div className="mb-6 p-4 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center gap-3">
            <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <span className="font-medium text-blue-800 dark:text-blue-200">
              Session starts {timeUntil}
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Booking Summary Card */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                      {booking.subject_name || "Lesson"}
                    </h1>
                    <StatusBadge status={booking.session_state} type="session" />
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                    <span>Booking #{bookingId}</span>
                    <button
                      onClick={handleCopyId}
                      className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded transition-colors"
                    >
                      {copied ? (
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {booking.session_outcome && (
                  <StatusBadge
                    status={booking.session_outcome}
                    type="outcome"
                    variant="pill"
                  />
                )}
              </div>

              {/* Date & Time */}
              <div className="flex items-start gap-4 mb-6 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <div className="w-14 h-14 bg-white dark:bg-slate-800 rounded-xl flex flex-col items-center justify-center border border-slate-200 dark:border-slate-700 shrink-0">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">
                    {startDate.toLocaleDateString("en-US", { month: "short" })}
                  </span>
                  <span className="text-xl font-bold text-slate-900 dark:text-white">
                    {startDate.getDate()}
                  </span>
                </div>
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">
                    {formatDate(startDate)}
                  </div>
                  <div className="text-slate-600 dark:text-slate-400">
                    {formatTime(startDate)} - {formatTime(endDate)}
                  </div>
                  <div className="text-sm text-slate-500 dark:text-slate-500 mt-1">
                    Timezone: {booking.student_tz || "UTC"}
                  </div>
                </div>
              </div>

              {/* Topic/Notes */}
              {(booking.topic || booking.notes_student) && (
                <div className="mb-6">
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-2">
                    Lesson Topic
                  </h3>
                  <p className="text-slate-900 dark:text-white">
                    {booking.topic || booking.notes_student}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-wrap gap-3">
                {canJoin && booking.join_url && (
                  <a
                    href={booking.join_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Button variant="primary">
                      <Video className="w-4 h-4 mr-2" />
                      Join Session
                    </Button>
                  </a>
                )}

                {canAcceptDecline && (
                  <>
                    <Button
                      variant="primary"
                      onClick={handleAccept}
                      isLoading={actionLoading}
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Accept
                    </Button>
                    <Button
                      variant="danger"
                      onClick={() => setShowCancelModal(true)}
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Decline
                    </Button>
                  </>
                )}

                {canReschedule && (
                  <Button
                    variant="secondary"
                    onClick={() => setShowRescheduleModal(true)}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Reschedule
                  </Button>
                )}

                {canCancel && !canAcceptDecline && (
                  <Button
                    variant="ghost"
                    onClick={() => setShowCancelModal(true)}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Cancel Booking
                  </Button>
                )}

                {canReview && (
                  <Link href={`/bookings/${bookingId}/review`}>
                    <Button variant="secondary">
                      <Star className="w-4 h-4 mr-2" />
                      Leave Review
                    </Button>
                  </Link>
                )}

                {canDispute && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      /* TODO: Implement dispute flow */
                    }}
                  >
                    <Flag className="w-4 h-4 mr-2" />
                    Report Issue
                  </Button>
                )}

                <Link href={`/messages`}>
                  <Button variant="ghost">
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Message {counterpartyRole}
                  </Button>
                </Link>
              </div>
            </div>

            {/* Payment Details */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                Payment Details
              </h2>

              <div className="space-y-3">
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Lesson Rate</span>
                  <span>{formatPrice(booking.rate_cents, booking.currency)}</span>
                </div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Platform Fee ({booking.platform_fee_pct}%)</span>
                  <span>
                    {formatPrice(booking.platform_fee_cents, booking.currency)}
                  </span>
                </div>
                <div className="flex justify-between font-bold text-slate-900 dark:text-white pt-3 border-t border-slate-200 dark:border-slate-700">
                  <span>Total</span>
                  <span>
                    {formatPrice(
                      booking.rate_cents + booking.platform_fee_cents,
                      booking.currency
                    )}
                  </span>
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Payment Status
                </span>
                <StatusBadge
                  status={booking.payment_state}
                  type="payment"
                  size="sm"
                />
              </div>

              {booking.dispute_state !== "NONE" && (
                <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                  <span className="text-sm text-amber-800 dark:text-amber-200">
                    Dispute Status:{" "}
                    <StatusBadge
                      status={booking.dispute_state}
                      type="dispute"
                      size="sm"
                      variant="subtle"
                    />
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Counterparty Card */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4">
                Your {counterpartyRole}
              </h3>

              <div className="flex items-center gap-4 mb-4">
                {counterparty.avatar_url ? (
                  <Image
                    src={resolveAssetUrl(counterparty.avatar_url)}
                    alt={counterparty.name}
                    width={56}
                    height={56}
                    className="w-14 h-14 rounded-full object-cover"
                    unoptimized
                  />
                ) : (
                  <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                    <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                      {counterparty.name?.charAt(0).toUpperCase() || "?"}
                    </span>
                  </div>
                )}
                <div>
                  <div className="font-bold text-slate-900 dark:text-white">
                    {counterparty.name}
                  </div>
                  {isStudent && booking.tutor.rating_avg && (
                    <div className="flex items-center gap-1 text-sm text-slate-500">
                      <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                      <span>{Number(booking.tutor.rating_avg).toFixed(1)}</span>
                    </div>
                  )}
                </div>
              </div>

              {isStudent && (
                <Link href={`/tutors/${booking.tutor.id}`}>
                  <Button variant="secondary" className="w-full" size="sm">
                    View Profile
                  </Button>
                </Link>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800">
              <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-4">
                Quick Actions
              </h3>

              <div className="space-y-2">
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left">
                  <CalendarPlus className="w-5 h-5 text-slate-400" />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Add to Calendar
                  </span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left">
                  <FileText className="w-5 h-5 text-slate-400" />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    View Receipt
                  </span>
                </button>
              </div>
            </div>

            {/* Cancellation Policy */}
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4">
              <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Cancellation Policy
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Free cancellation up to 24 hours before the session. Late
                cancellations may result in partial charges.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cancel Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title={canAcceptDecline ? "Decline Booking" : "Cancel Booking"}
        footer={
          <div className="flex gap-3">
            <Button
              variant="ghost"
              onClick={() => setShowCancelModal(false)}
              className="flex-1"
            >
              Keep Booking
            </Button>
            <Button
              variant="danger"
              onClick={canAcceptDecline ? handleDecline : handleCancel}
              isLoading={actionLoading}
              className="flex-1"
            >
              {canAcceptDecline ? "Decline" : "Cancel Booking"}
            </Button>
          </div>
        }
      >
        <div className="space-y-4">
          <p className="text-slate-600 dark:text-slate-400">
            {canAcceptDecline
              ? "Are you sure you want to decline this booking request?"
              : "Are you sure you want to cancel this booking? This action cannot be undone."}
          </p>

          <TextArea
            label="Reason (optional)"
            placeholder="Let them know why you're cancelling..."
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
            maxLength={500}
            showCounter
          />

          {!canAcceptDecline && (
            <div className="p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Based on our cancellation policy, you may receive a full refund
                for this cancellation.
              </p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
