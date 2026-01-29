/**
 * Booking card component for students.
 * Shows tutor information, lesson details, and action buttons.
 * Based on booking_detail.md specification.
 */

import React from "react";
import {
  FiCalendar,
  FiClock,
  FiDollarSign,
  FiVideo,
  FiX,
  FiStar,
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

interface BookingCardStudentProps {
  booking: BookingDTO;
  onJoin?: (bookingId: number) => void;
  onCancel?: (bookingId: number) => void;
  onReschedule?: (bookingId: number) => void;
  onMarkNoShow?: (bookingId: number) => void;
  onDispute?: (bookingId: number) => void;
}

export default function BookingCardStudent({
  booking,
  onJoin,
  onCancel,
  onReschedule,
  onMarkNoShow,
  onDispute,
}: BookingCardStudentProps) {
  const { userTimezone } = useTimezone();

  // Use new four-field status system with fallback to legacy
  const sessionState = booking.session_state || booking.status;
  const sessionOutcome = booking.session_outcome;
  const disputeState = booking.dispute_state || "NONE";

  const isUpcoming = isUpcomingBooking(sessionState);
  const canCancel = isCancellableBooking(sessionState);
  const isCompleted = sessionState === "ENDED" && sessionOutcome === "COMPLETED";
  const isCancelled = sessionState === "CANCELLED" || sessionState === "EXPIRED";
  const isActive = sessionState === "ACTIVE";
  const showDispute = hasOpenDispute(disputeState);

  // Use shared timing calculation and formatting utilities
  const timing = calculateBookingTiming(booking, userTimezone);
  const { startDate, endDate, duration, hoursUntil, canCancelFree } = timing;
  const displayTimezone = getDisplayTimezone(booking, userTimezone);
  const priceDisplay = formatBookingPrice(booking.rate_cents);

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 hover:shadow-md transition-all">
      {/* Header: Tutor Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Tutor Avatar */}
          <div className="w-12 h-12 rounded-full bg-gray-200 dark:bg-slate-700 flex items-center justify-center overflow-hidden">
            {booking.tutor.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={booking.tutor.avatar_url}
                alt={booking.tutor.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <FiUser className="w-6 h-6 text-gray-400 dark:text-slate-500" />
            )}
          </div>

          {/* Tutor Name and Title */}
          <div>
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
              {booking.tutor.name}
            </h3>
            {booking.tutor.title && (
              <p className="text-sm text-gray-600 dark:text-slate-400">{booking.tutor.title}</p>
            )}
            {/* Rating */}
            <div className="flex items-center gap-1 mt-1">
              <FiStar className="w-4 h-4 text-yellow-500 fill-current" />
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                {Number(booking.tutor.rating_avg).toFixed(1)}
              </span>
            </div>
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
              otherTimezone={booking.tutor_tz}
              otherLabel="tutor"
            />
            <span className="text-sm text-gray-500 dark:text-slate-400 ml-2">
              ({duration} min)
            </span>
          </span>
        </div>

        {/* Price */}
        <div className="flex items-center gap-2 text-gray-700 dark:text-slate-300">
          <FiDollarSign className="w-5 h-5" />
          <span className="font-semibold">{priceDisplay}</span>
          <span className="text-sm text-gray-500 dark:text-slate-400">{booking.currency}</span>
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
          <div className="text-sm bg-gray-50 dark:bg-slate-800 p-3 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="font-medium text-gray-700 dark:text-slate-300">Your notes:</span>
            <p className="text-gray-600 dark:text-slate-400 mt-1">{booking.notes_student}</p>
          </div>
        )}

        {/* Tutor Notes (if confirmed) */}
        {booking.notes_tutor && (
          <div className="text-sm bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
            <span className="font-medium text-blue-700 dark:text-blue-300">Tutor notes:</span>
            <p className="text-blue-600 dark:text-blue-400 mt-1">{booking.notes_tutor}</p>
          </div>
        )}
      </div>

      {/* Policy Hint */}
      {isUpcoming && (
        <div className={`text-xs bg-gray-50 dark:bg-slate-800 p-3 rounded-lg mb-4 border ${
          canCancelFree
            ? "text-green-700 dark:text-green-400 border-green-200 dark:border-green-800"
            : "text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-800"
        }`}>
          {canCancelFree
            ? "Free cancellation available (24+ hours before session)"
            : "No refund if cancelled now (less than 24 hours before)"}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        {/* Join Button - show when SCHEDULED or ACTIVE and within time window */}
        {(sessionState === "SCHEDULED" || sessionState === "ACTIVE") &&
          booking.join_url &&
          hoursUntil <= 1 &&
          hoursUntil >= -1 && (
            <Button
              variant="primary"
              onClick={() => {
                if (booking.join_url) {
                  window.open(booking.join_url, "_blank");
                }
              }}
            >
              <FiVideo className="w-4 h-4 mr-2" />
              Join Session
            </Button>
          )}

        {/* Reschedule Button */}
        {canCancel && onReschedule && hoursUntil >= 24 && (
          <Button variant="secondary" onClick={() => onReschedule(booking.id)}>
            Reschedule
          </Button>
        )}

        {/* Cancel Button */}
        {canCancel && onCancel && (
          <Button variant="outline" onClick={() => onCancel(booking.id)}>
            <FiX className="w-4 h-4 mr-1" />
            Cancel
          </Button>
        )}

        {/* Mark Tutor No-Show - available when SCHEDULED/ACTIVE and past start time */}
        {(sessionState === "SCHEDULED" || sessionState === "ACTIVE") && hoursUntil < 0 && onMarkNoShow && (
          <Button
            variant="danger"
            onClick={() => onMarkNoShow(booking.id)}
            size="sm"
          >
            Report Tutor No-Show
          </Button>
        )}

        {/* Open Dispute - available when session ended/cancelled and no open dispute */}
        {(sessionState === "ENDED" || sessionState === "CANCELLED") && disputeState === "NONE" && onDispute && (
          <Button
            variant="outline"
            onClick={() => onDispute(booking.id)}
            size="sm"
          >
            Open Dispute
          </Button>
        )}
      </div>
    </div>
  );
}
