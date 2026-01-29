/**
 * Booking card component for tutors.
 * Shows student information, lesson details, and tutor action buttons.
 * Based on booking_detail.md specification.
 */

import React from "react";
import {
  FiCalendar,
  FiClock,
  FiDollarSign,
  FiCheck,
  FiX,
  FiAlertCircle,
  FiUser,
} from "react-icons/fi";
import { BookingDTO } from "@/types/booking";
import Button from "@/components/Button";
import TimeDisplay from "@/components/TimeDisplay";
import { useTimezone } from "@/contexts/TimezoneContext";
import {
  BOOKING_STATUS_COLORS,
  LESSON_TYPE_BADGES,
  SESSION_STATE_COLORS,
  DISPUTE_STATE_COLORS,
  calculateBookingTiming,
  formatBookingPrice,
  getDisplayTimezone,
  getSessionStateLabel,
  getSessionOutcomeLabel,
  getDisputeStateLabel,
  isUpcomingBooking,
  isCancellableBooking,
  hasOpenDispute,
} from "@/lib/bookingUtils";

interface BookingCardTutorProps {
  booking: BookingDTO;
  onConfirm?: (bookingId: number) => void;
  onDecline?: (bookingId: number) => void;
  onCancel?: (bookingId: number) => void;
  onMarkNoShow?: (bookingId: number) => void;
  onAddNotes?: (bookingId: number) => void;
}

export default function BookingCardTutor({
  booking,
  onConfirm,
  onDecline,
  onCancel,
  onMarkNoShow,
  onAddNotes,
}: BookingCardTutorProps) {
  const { userTimezone } = useTimezone();

  // Use new four-field status system with fallback to legacy
  const sessionState = booking.session_state || booking.status;
  const sessionOutcome = booking.session_outcome;
  const disputeState = booking.dispute_state || "NONE";

  const isPending = sessionState === "REQUESTED";
  const isScheduled = sessionState === "SCHEDULED";
  const isActive = sessionState === "ACTIVE";
  const isUpcoming = isUpcomingBooking(sessionState);
  const canCancel = isCancellableBooking(sessionState);
  const isCompleted = sessionState === "ENDED" && sessionOutcome === "COMPLETED";

  // Use shared timing calculation and formatting utilities
  const timing = calculateBookingTiming(booking, userTimezone);
  const { startDate, endDate, duration, hoursUntil } = timing;
  const displayTimezone = getDisplayTimezone(booking, userTimezone);
  const totalDisplay = formatBookingPrice(booking.rate_cents);

  // Format earnings (tutor receives 80% after platform fee)
  const earningsDisplay = `$${(booking.tutor_earnings_cents / 100).toFixed(2)}`;

  // Calculate minutes since start for no-show logic
  const now = new Date();
  const minutesSinceStart = Math.round(
    (now.getTime() - startDate.getTime()) / (1000 * 60)
  );
  const canMarkNoShow = minutesSinceStart >= 10 && minutesSinceStart <= 24 * 60;

  return (
    <div
      className={`bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 hover:shadow-md transition-all ${
        isPending ? "border-l-4 border-yellow-500 dark:border-yellow-400" : ""
      }`}
    >
      {/* Header: Student Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Student Avatar */}
          <div className="w-12 h-12 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center overflow-hidden">
            {booking.student.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={booking.student.avatar_url}
                alt={booking.student.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <FiUser className="w-6 h-6 text-gray-400 dark:text-slate-500" />
            )}
          </div>

          {/* Student Name and Level */}
          <div>
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
              {booking.student.name}
            </h3>
            {booking.student.level && (
              <span className="text-sm text-gray-600 dark:text-slate-400 bg-gray-100 dark:bg-slate-800 px-2 py-1 rounded">
                Level: {booking.student.level}
              </span>
            )}
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-col gap-2 items-end">
          {/* Session State Badge */}
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              SESSION_STATE_COLORS[sessionState] || BOOKING_STATUS_COLORS[booking.status] || "bg-gray-100 text-gray-800"
            }`}
          >
            {getSessionStateLabel(sessionState)}
          </span>
          {/* Session Outcome Badge (if ended) */}
          {sessionOutcome && (
            <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
              {getSessionOutcomeLabel(sessionOutcome)}
            </span>
          )}
          {/* Dispute Badge (if has dispute) */}
          {disputeState !== "NONE" && (
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                DISPUTE_STATE_COLORS[disputeState] || "bg-gray-100 text-gray-800"
              }`}
            >
              {getDisputeStateLabel(disputeState)}
            </span>
          )}
          {/* Lesson Type Badge */}
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              LESSON_TYPE_BADGES[booking.lesson_type] || "bg-gray-100 text-gray-800"
            }`}
          >
            {booking.lesson_type}
          </span>
        </div>
      </div>

      {/* Pending Alert */}
      {isPending && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 mb-4 flex items-center gap-2">
          <FiAlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
          <span className="text-sm text-yellow-800 dark:text-yellow-300 font-medium">
            Awaiting your confirmation
          </span>
        </div>
      )}

      {/* Lesson Details */}
      <div className="space-y-3 mb-4">
        {/* Date and Time */}
        <div className="flex items-center gap-2 text-gray-700 dark:text-slate-300">
          <FiCalendar className="w-5 h-5" />
          <span className="font-medium">
            {startDate.toLocaleDateString("en-US", {
              weekday: "short",
              year: "numeric",
              month: "short",
              day: "numeric",
              timeZone: displayTimezone,
            })}
          </span>
        </div>

        <div className="flex items-center gap-2 text-gray-700 dark:text-slate-300">
          <FiClock className="w-5 h-5" />
          <span>
            <TimeDisplay
              date={booking.start_at}
              userTimezone={displayTimezone}
              otherTimezone={booking.student_tz}
              otherLabel="student"
            />
            <span className="text-sm text-gray-500 dark:text-slate-400 ml-2">
              ({duration} min)
            </span>
          </span>
        </div>

        {/* Earnings */}
        <div className="flex items-center gap-2 text-gray-700 dark:text-slate-300">
          <FiDollarSign className="w-5 h-5" />
          <div>
            <span className="font-semibold text-green-600 dark:text-green-400">
              {earningsDisplay}
            </span>
            <span className="text-sm text-gray-500 dark:text-slate-400 ml-2">
              (from {totalDisplay} total)
            </span>
          </div>
        </div>

        {/* Subject/Topic */}
        {(booking.subject_name || booking.topic) && (
          <div className="text-sm text-gray-600 dark:text-slate-400">
            <span className="font-medium">Subject:</span>{" "}
            {booking.subject_name || booking.topic}
          </div>
        )}

        {/* Student Notes */}
        {booking.notes_student && (
          <div className="text-sm bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
            <span className="font-medium text-blue-700 dark:text-blue-300">Student notes:</span>
            <p className="text-blue-600 dark:text-blue-400 mt-1">{booking.notes_student}</p>
          </div>
        )}

        {/* Tutor Notes */}
        {booking.notes_tutor && (
          <div className="text-sm bg-gray-50 dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="font-medium text-gray-700 dark:text-slate-300">Your notes:</span>
            <p className="text-gray-600 dark:text-slate-400 mt-1">{booking.notes_tutor}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        {/* Confirm Button (for REQUESTED bookings) */}
        {isPending && onConfirm && (
          <Button variant="primary" onClick={() => onConfirm(booking.id)}>
            <FiCheck className="w-4 h-4 mr-2" />
            Confirm
          </Button>
        )}

        {/* Decline Button (for REQUESTED bookings) */}
        {isPending && onDecline && (
          <Button variant="outline" onClick={() => onDecline(booking.id)}>
            <FiX className="w-4 h-4 mr-1" />
            Decline
          </Button>
        )}

        {/* Cancel Button (for SCHEDULED bookings) */}
        {isScheduled && onCancel && (
          <Button variant="outline" onClick={() => onCancel(booking.id)}>
            <FiX className="w-4 h-4 mr-1" />
            Cancel
          </Button>
        )}

        {/* Add Notes Button */}
        {isUpcoming && onAddNotes && (
          <Button variant="secondary" onClick={() => onAddNotes(booking.id)}>
            {booking.notes_tutor ? "Edit Notes" : "Add Notes"}
          </Button>
        )}

        {/* Mark Student No-Show */}
        {canMarkNoShow && onMarkNoShow && (
          <Button
            variant="danger"
            onClick={() => onMarkNoShow(booking.id)}
            size="sm"
          >
            Mark Student No-Show
          </Button>
        )}
      </div>

      {/* Cancellation Warning */}
      {isScheduled && hoursUntil < 24 && hoursUntil > 0 && (
        <div className="mt-3 text-xs text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg border border-orange-200 dark:border-orange-800">
          Cancelling within 24h will result in a penalty strike
        </div>
      )}
    </div>
  );
}
