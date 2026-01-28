/**
 * Shared utilities for booking card components
 *
 * Consolidates duplicate logic from BookingCardStudent and BookingCardTutor
 * to eliminate ~200 lines of duplication.
 */

import type { Booking } from "@/types";

/**
 * Status badge color mappings
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

  const canCancelFree = hoursUntilStart >= 12;

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
