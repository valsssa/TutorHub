'use client'

import React from 'react'
import { formatDualTimezone, formatTimeInTimezone, getTimezoneOffset } from '@/lib/timezone'
import { useTimezone } from '@/contexts/TimezoneContext'

interface TimeDisplayProps {
  /** The date/time to display (ISO string or Date object) */
  date: Date | string
  /**
   * Optional: Another party's timezone for dual display.
   * If provided, shows both timezones.
   */
  otherTimezone?: string
  /** Label for the other party (e.g., "tutor", "student") */
  otherLabel?: string
  /**
   * Override the user's timezone (useful for static rendering).
   * If not provided, uses the context's userTimezone.
   */
  userTimezone?: string
  /** Show date in addition to time */
  showDate?: boolean
  /** Custom className for styling */
  className?: string
}

/**
 * TimeDisplay component for consistent timezone-aware time formatting.
 *
 * Single timezone usage:
 * ```tsx
 * <TimeDisplay date={booking.start_at} />
 * // Output: "2:00 PM EST"
 * ```
 *
 * Dual timezone usage (for cross-timezone bookings):
 * ```tsx
 * <TimeDisplay
 *   date={booking.start_at}
 *   otherTimezone={booking.tutor_tz}
 *   otherLabel="tutor"
 * />
 * // Output: "2:00 PM EST (11:00 AM PST for tutor)"
 * ```
 */
export default function TimeDisplay({
  date,
  otherTimezone,
  otherLabel = 'other',
  userTimezone: userTimezoneProp,
  showDate = false,
  className = '',
}: TimeDisplayProps) {
  const { userTimezone: contextTimezone, isLoaded } = useTimezone()
  const userTimezone = userTimezoneProp || contextTimezone

  // Show loading state while timezone context loads
  if (!isLoaded && !userTimezoneProp) {
    return <span className={`text-slate-400 ${className}`}>--:-- --</span>
  }

  const dateObj = typeof date === 'string' ? new Date(date) : date

  // Format the time portion
  let timeString: string
  if (otherTimezone && otherTimezone !== userTimezone) {
    timeString = formatDualTimezone(dateObj, userTimezone, otherTimezone, otherLabel)
  } else {
    const time = formatTimeInTimezone(dateObj, userTimezone)
    const abbr = getTimezoneOffset(userTimezone)
    timeString = `${time} ${abbr}`
  }

  // Format date if requested
  let dateString = ''
  if (showDate) {
    dateString = dateObj.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      timeZone: userTimezone,
    })
  }

  return (
    <span className={className}>
      {showDate && <span className="font-medium">{dateString}, </span>}
      {timeString}
    </span>
  )
}

/**
 * Simple time range display component.
 * Shows: "2:00 PM - 3:00 PM EST"
 */
export function TimeRangeDisplay({
  startDate,
  endDate,
  userTimezone: userTimezoneProp,
  className = '',
}: {
  startDate: Date | string
  endDate: Date | string
  userTimezone?: string
  className?: string
}) {
  const { userTimezone: contextTimezone, isLoaded } = useTimezone()
  const userTimezone = userTimezoneProp || contextTimezone

  if (!isLoaded && !userTimezoneProp) {
    return <span className={`text-slate-400 ${className}`}>--:-- - --:-- --</span>
  }

  const startTime = formatTimeInTimezone(startDate, userTimezone)
  const endTime = formatTimeInTimezone(endDate, userTimezone)
  const abbr = getTimezoneOffset(userTimezone)

  return (
    <span className={className}>
      {startTime} - {endTime} {abbr}
    </span>
  )
}
