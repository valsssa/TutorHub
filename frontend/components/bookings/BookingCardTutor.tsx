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
  const isPending = ["PENDING", "pending"].includes(booking.status);
  const isUpcoming = ["PENDING", "CONFIRMED", "pending", "confirmed"].includes(
    booking.status
  );
  const isCompleted = ["COMPLETED", "completed"].includes(booking.status);

  // Format date and time in tutor timezone
  const startDate = new Date(booking.start_at);
  const endDate = new Date(booking.end_at);
  const duration = Math.round(
    (endDate.getTime() - startDate.getTime()) / (1000 * 60)
  );

  // Format earnings (tutor receives 80% after platform fee)
  const earningsDisplay = `$${(booking.tutor_earnings_cents / 100).toFixed(2)}`;
  const totalDisplay = `$${(booking.rate_cents / 100).toFixed(2)}`;

  // Calculate hours until session
  const now = new Date();
  const hoursUntil = Math.round(
    (startDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  );
  const minutesSinceStart = Math.round(
    (now.getTime() - startDate.getTime()) / (1000 * 60)
  );
  const canMarkNoShow = minutesSinceStart >= 10 && minutesSinceStart <= 24 * 60;

  // Status badge color
  const statusColors: Record<string, string> = {
    PENDING: "bg-yellow-100 text-yellow-800",
    pending: "bg-yellow-100 text-yellow-800",
    CONFIRMED: "bg-green-100 text-green-800",
    confirmed: "bg-green-100 text-green-800",
    COMPLETED: "bg-blue-100 text-blue-800",
    completed: "bg-blue-100 text-blue-800",
    CANCELLED_BY_STUDENT: "bg-gray-100 text-gray-800",
    CANCELLED_BY_TUTOR: "bg-red-100 text-red-800",
    cancelled: "bg-gray-100 text-gray-800",
    NO_SHOW_STUDENT: "bg-orange-100 text-orange-800",
    NO_SHOW_TUTOR: "bg-red-100 text-red-800",
  };

  // Lesson type badge
  const lessonTypeBadge = {
    TRIAL: "bg-purple-100 text-purple-800",
    REGULAR: "bg-blue-100 text-blue-800",
    PACKAGE: "bg-indigo-100 text-indigo-800",
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow ${
        isPending ? "border-l-4 border-yellow-500" : ""
      }`}
    >
      {/* Header: Student Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Student Avatar */}
          <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center overflow-hidden">
            {booking.student.avatar_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={booking.student.avatar_url}
                alt={booking.student.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <FiUser className="w-6 h-6 text-gray-400" />
            )}
          </div>

          {/* Student Name and Level */}
          <div>
            <h3 className="font-semibold text-lg text-gray-900">
              {booking.student.name}
            </h3>
            {booking.student.level && (
              <span className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                Level: {booking.student.level}
              </span>
            )}
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

      {/* Pending Alert */}
      {isPending && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 flex items-center gap-2">
          <FiAlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0" />
          <span className="text-sm text-yellow-800 font-medium">
            Awaiting your confirmation
          </span>
        </div>
      )}

      {/* Lesson Details */}
      <div className="space-y-3 mb-4">
        {/* Date and Time */}
        <div className="flex items-center gap-2 text-gray-700">
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

        <div className="flex items-center gap-2 text-gray-700">
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
            <span className="text-sm text-gray-500">
              ({duration} min • {booking.tutor_tz})
            </span>
          </span>
        </div>

        {/* Earnings */}
        <div className="flex items-center gap-2 text-gray-700">
          <FiDollarSign className="w-5 h-5" />
          <div>
            <span className="font-semibold text-green-600">
              {earningsDisplay}
            </span>
            <span className="text-sm text-gray-500 ml-2">
              (from {totalDisplay} total)
            </span>
          </div>
        </div>

        {/* Subject/Topic */}
        {(booking.subject_name || booking.topic) && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Subject:</span>{" "}
            {booking.subject_name || booking.topic}
          </div>
        )}

        {/* Student Notes */}
        {booking.notes_student && (
          <div className="text-sm bg-blue-50 p-3 rounded">
            <span className="font-medium text-blue-700">Student notes:</span>
            <p className="text-blue-600 mt-1">{booking.notes_student}</p>
          </div>
        )}

        {/* Tutor Notes */}
        {booking.notes_tutor && (
          <div className="text-sm bg-gray-50 p-3 rounded">
            <span className="font-medium text-gray-700">Your notes:</span>
            <p className="text-gray-600 mt-1">{booking.notes_tutor}</p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        {/* Confirm Button (for pending bookings) */}
        {isPending && onConfirm && (
          <Button variant="primary" onClick={() => onConfirm(booking.id)}>
            <FiCheck className="w-4 h-4 mr-2" />
            Confirm
          </Button>
        )}

        {/* Decline Button (for pending bookings) */}
        {isPending && onDecline && (
          <Button variant="outline" onClick={() => onDecline(booking.id)}>
            <FiX className="w-4 h-4 mr-1" />
            Decline
          </Button>
        )}

        {/* Cancel Button (for confirmed bookings) */}
        {booking.status === "CONFIRMED" && onCancel && (
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
      {booking.status === "CONFIRMED" && hoursUntil < 12 && hoursUntil > 0 && (
        <div className="mt-3 text-xs text-orange-600 bg-orange-50 p-2 rounded">
          ⚠ Cancelling within 12h will result in a penalty strike
        </div>
      )}
    </div>
  );
}
