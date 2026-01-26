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

interface BookingCardStudentProps {
  booking: BookingDTO;
  onJoin?: (bookingId: number) => void;
  onCancel?: (bookingId: number) => void;
  onReschedule?: (bookingId: number) => void;
  onMarkNoShow?: (bookingId: number) => void;
}

export default function BookingCardStudent({
  booking,
  onJoin,
  onCancel,
  onReschedule,
  onMarkNoShow,
}: BookingCardStudentProps) {
  const isUpcoming = ["PENDING", "CONFIRMED", "pending", "confirmed"].includes(
    booking.status
  );
  const isCompleted = ["COMPLETED", "completed"].includes(booking.status);
  const isCancelled = booking.status.toLowerCase().includes("cancel");

  // Format date and time in student timezone
  const startDate = new Date(booking.start_at);
  const endDate = new Date(booking.end_at);
  const duration = Math.round(
    (endDate.getTime() - startDate.getTime()) / (1000 * 60)
  );

  // Format price
  const priceDisplay = `$${(booking.rate_cents / 100).toFixed(2)}`;

  // Calculate hours until session for policy hint
  const now = new Date();
  const hoursUntil = Math.round(
    (startDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  );
  const canCancelFree = hoursUntil >= 12;

  // Status badge color
  const statusColors: Record<string, string> = {
    PENDING: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300",
    pending: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300",
    CONFIRMED: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
    confirmed: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
    COMPLETED: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
    completed: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
    CANCELLED_BY_STUDENT: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
    CANCELLED_BY_TUTOR: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
    cancelled: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
    NO_SHOW_STUDENT: "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300",
    NO_SHOW_TUTOR: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
  };

  // Lesson type badge
  const lessonTypeBadge = {
    TRIAL: "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300",
    REGULAR: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
    PACKAGE: "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300",
  };

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

        {/* Status Badge */}
        <div className="flex flex-col gap-2 items-end">
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${
              statusColors[booking.status] || "bg-gray-100 text-gray-800"
            }`}
          >
            {booking.status.replace(/_/g, " ")}
          </span>
          {/* Lesson Type Badge */}
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${
              lessonTypeBadge[booking.lesson_type] || "bg-gray-100 text-gray-800"
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
            })}
          </span>
        </div>

        <div className="flex items-center gap-2 text-gray-700 dark:text-slate-300">
          <FiClock className="w-5 h-5" />
          <span>
            {startDate.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            })}{" "}
            - {endDate.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            })}{" "}
            <span className="text-sm text-gray-500 dark:text-slate-400">
              ({duration} min • {booking.student_tz})
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
            ? "✓ Free cancellation available (12+ hours before session)"
            : "⚠ No refund if cancelled now (less than 12 hours before)"}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        {/* Join Button */}
        {booking.status === "CONFIRMED" &&
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
        {isUpcoming && onReschedule && hoursUntil >= 12 && (
          <Button variant="secondary" onClick={() => onReschedule(booking.id)}>
            Reschedule
          </Button>
        )}

        {/* Cancel Button */}
        {isUpcoming && onCancel && (
          <Button variant="outline" onClick={() => onCancel(booking.id)}>
            <FiX className="w-4 h-4 mr-1" />
            Cancel
          </Button>
        )}

        {/* Mark Tutor No-Show */}
        {booking.status === "CONFIRMED" && hoursUntil < 0 && onMarkNoShow && (
          <Button
            variant="danger"
            onClick={() => onMarkNoShow(booking.id)}
            size="sm"
          >
            Report Tutor No-Show
          </Button>
        )}
      </div>
    </div>
  );
}
