/**
 * Shared utilities for booking card components
 *
 * Consolidates duplicate logic from BookingCardStudent and BookingCardTutor
 * to eliminate ~200 lines of duplication.
 *
 * Updated for four-field status system: session_state, session_outcome, payment_state, dispute_state
 */

import type { Booking } from "@/types";
import type { SessionState, SessionOutcome, PaymentState, DisputeState } from "@/types/booking";

/**
 * Session state badge color mappings
 */
export const SESSION_STATE_COLORS: Record<SessionState | string, string> = {
  REQUESTED: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300",
  SCHEDULED: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
  ACTIVE: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
  ENDED: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
  CANCELLED: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
  EXPIRED: "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300",
};

/**
 * Session outcome badge color mappings
 */
export const SESSION_OUTCOME_COLORS: Record<SessionOutcome | string, string> = {
  COMPLETED: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
  NOT_HELD: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
  NO_SHOW_STUDENT: "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300",
  NO_SHOW_TUTOR: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
};

/**
 * Payment state badge color mappings
 */
export const PAYMENT_STATE_COLORS: Record<PaymentState | string, string> = {
  PENDING: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300",
  AUTHORIZED: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
  CAPTURED: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
  VOIDED: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
  REFUNDED: "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300",
  PARTIALLY_REFUNDED: "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300",
};

/**
 * Dispute state badge color mappings
 */
export const DISPUTE_STATE_COLORS: Record<DisputeState | string, string> = {
  NONE: "",
  OPEN: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
  RESOLVED_UPHELD: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
  RESOLVED_REFUNDED: "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300",
};

/**
 * Legacy status badge color mappings (for backward compatibility)
 */
export const BOOKING_STATUS_COLORS: Record<string, string> = {
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
  // New session states mapped to status colors
  REQUESTED: "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300",
  SCHEDULED: "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300",
  ACTIVE: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
  ENDED: "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300",
  CANCELLED: "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300",
  EXPIRED: "bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-300",
};

/**
 * Lesson type badge color mappings
 */
export const LESSON_TYPE_BADGES: Record<string, string> = {
  TRIAL: "bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300",
  REGULAR: "bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300",
  PACKAGE: "bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300",
};

/**
 * Calculate booking timing information
 */
export interface BookingTiming {
  startDate: Date;
  endDate: Date;
  duration: number; // minutes
  hoursUntil: number;
  canCancelFree: boolean;
}

export function calculateBookingTiming(
  booking: Booking,
  userTimezone?: string
): BookingTiming {
  const now = new Date();
  const startDate = new Date(booking.start_at);
  const endDate = new Date(booking.end_at);

  const duration = Math.round(
    (endDate.getTime() - startDate.getTime()) / (1000 * 60)
  );

  const hoursUntilStart = Math.round(
    (startDate.getTime() - now.getTime()) / (1000 * 60 * 60)
  );

  const canCancelFree = hoursUntilStart >= 24;

  return {
    startDate,
    endDate,
    duration,
    hoursUntilStart,
    canCancelFree,
  };
}

/**
 * Format price for display
 */
export function formatBookingPrice(rateCents: number): string {
  return `$${(rateCents / 100).toFixed(2)}`;
}

/**
 * Get display timezone (user preference or tutor's timezone)
 */
export function getDisplayTimezone(
  booking: Booking,
  userTimezone?: string
): string {
  return userTimezone || booking.tutor_tz || "UTC";
}

/**
 * Format date and time for display
 */
export function formatBookingDateTime(
  date: Date,
  timezone: string
): { date: string; time: string } {
  const dateStr = date.toLocaleDateString("en-US", {
    timeZone: timezone,
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const timeStr = date.toLocaleTimeString("en-US", {
    timeZone: timezone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  return { date: dateStr, time: timeStr };
}

/**
 * Get human-readable label for session state
 */
export function getSessionStateLabel(state: SessionState | string): string {
  const labels: Record<string, string> = {
    REQUESTED: "Pending",
    SCHEDULED: "Scheduled",
    ACTIVE: "In Progress",
    ENDED: "Ended",
    CANCELLED: "Cancelled",
    EXPIRED: "Expired",
  };
  return labels[state] || state;
}

/**
 * Get human-readable label for session outcome
 */
export function getSessionOutcomeLabel(outcome: SessionOutcome | string | null): string {
  if (!outcome) return "";
  const labels: Record<string, string> = {
    COMPLETED: "Completed",
    NOT_HELD: "Not Held",
    NO_SHOW_STUDENT: "Student No-Show",
    NO_SHOW_TUTOR: "Tutor No-Show",
  };
  return labels[outcome] || outcome;
}

/**
 * Get human-readable label for payment state
 */
export function getPaymentStateLabel(state: PaymentState | string): string {
  const labels: Record<string, string> = {
    PENDING: "Pending",
    AUTHORIZED: "Authorized",
    CAPTURED: "Paid",
    VOIDED: "Voided",
    REFUNDED: "Refunded",
    PARTIALLY_REFUNDED: "Partial Refund",
  };
  return labels[state] || state;
}

/**
 * Get human-readable label for dispute state
 */
export function getDisputeStateLabel(state: DisputeState | string): string {
  const labels: Record<string, string> = {
    NONE: "",
    OPEN: "Dispute Open",
    RESOLVED_UPHELD: "Dispute Upheld",
    RESOLVED_REFUNDED: "Dispute Refunded",
  };
  return labels[state] || state;
}

/**
 * Check if booking is in an upcoming/active state
 */
export function isUpcomingBooking(sessionState: SessionState | string): boolean {
  return ["REQUESTED", "SCHEDULED", "ACTIVE"].includes(sessionState);
}

/**
 * Check if booking can be cancelled
 */
export function isCancellableBooking(sessionState: SessionState | string): boolean {
  return ["REQUESTED", "SCHEDULED"].includes(sessionState);
}

/**
 * Check if booking is in a terminal state
 */
export function isTerminalBooking(sessionState: SessionState | string): boolean {
  return ["ENDED", "CANCELLED", "EXPIRED"].includes(sessionState);
}

/**
 * Check if booking has an open dispute
 */
export function hasOpenDispute(disputeState: DisputeState | string): boolean {
  return disputeState === "OPEN";
}

/**
 * Get the primary status color for a booking based on session_state
 */
export function getBookingStatusColor(booking: Booking): string {
  // Check for dispute first
  if (booking.dispute_state === "OPEN") {
    return DISPUTE_STATE_COLORS.OPEN;
  }

  // Use session state for primary color
  const sessionState = booking.session_state || booking.status;
  return SESSION_STATE_COLORS[sessionState] || BOOKING_STATUS_COLORS[sessionState] || "";
}

/**
 * Check if user's timezone differs from tutor/student timezone
 * Returns warning info if timezones differ significantly
 */
export interface TimezoneMismatchInfo {
  hasMismatch: boolean;
  userTimezone: string;
  otherTimezone: string;
  otherLabel: string;
  hoursDifference: number;
}

export function checkTimezoneMismatch(
  userTimezone: string,
  tutorTimezone: string,
  studentTimezone: string,
  userRole: "student" | "tutor"
): TimezoneMismatchInfo | null {
  const otherTimezone = userRole === "student" ? tutorTimezone : studentTimezone;
  const otherLabel = userRole === "student" ? "tutor" : "student";

  if (!userTimezone || !otherTimezone || userTimezone === otherTimezone) {
    return null;
  }

  // Calculate approximate hour difference
  // This is a simplified calculation - actual difference varies with DST
  const now = new Date();
  const userTime = new Date(now.toLocaleString("en-US", { timeZone: userTimezone }));
  const otherTime = new Date(now.toLocaleString("en-US", { timeZone: otherTimezone }));
  const hoursDifference = Math.abs((userTime.getTime() - otherTime.getTime()) / (1000 * 60 * 60));

  return {
    hasMismatch: true,
    userTimezone,
    otherTimezone,
    otherLabel,
    hoursDifference: Math.round(hoursDifference),
  };
}

/**
 * Format time showing both user's and other party's timezone
 */
export function formatDualTimezone(
  date: Date,
  userTimezone: string,
  otherTimezone: string,
  otherLabel: string
): string {
  const userTime = date.toLocaleTimeString("en-US", {
    timeZone: userTimezone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  const otherTime = date.toLocaleTimeString("en-US", {
    timeZone: otherTimezone,
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  const userAbbr = getTimezoneAbbreviation(userTimezone);
  const otherAbbr = getTimezoneAbbreviation(otherTimezone);

  if (userTimezone === otherTimezone) {
    return `${userTime} ${userAbbr}`;
  }

  return `${userTime} ${userAbbr} (${otherTime} ${otherAbbr} for ${otherLabel})`;
}

/**
 * Get timezone abbreviation (e.g., "EST", "PST")
 */
function getTimezoneAbbreviation(timezone: string): string {
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: timezone,
      timeZoneName: "short",
    });
    const parts = formatter.formatToParts(now);
    const timeZoneName = parts.find((part) => part.type === "timeZoneName");
    return timeZoneName?.value || "UTC";
  } catch {
    return "UTC";
  }
}
