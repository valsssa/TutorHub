'use client'

import React, { useState, useEffect } from 'react'
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

  // State to track client-side hydration and store formatted values
  const [isMounted, setIsMounted] = useState(false)
  const [formattedTime, setFormattedTime] = useState<string | null>(null)
  const [formattedDate, setFormattedDate] = useState<string | null>(null)

  // Only format dates on the client to avoid hydration mismatch
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Format dates when mounted and timezone is loaded
  useEffect(() => {
    if (!isMounted) return
    if (!isLoaded && !userTimezoneProp) return

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
    setFormattedTime(timeString)

    // Format date if requested
    if (showDate) {
      const dateString = dateObj.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        timeZone: userTimezone,
      })
      setFormattedDate(dateString)
    } else {
      setFormattedDate(null)
    }
  }, [isMounted, isLoaded, userTimezoneProp, date, otherTimezone, otherLabel, userTimezone, showDate])

  // Show loading state during SSR and initial hydration
  if (!isMounted || (!isLoaded && !userTimezoneProp) || formattedTime === null) {
    return <span className={`text-slate-400 ${className}`}>--:-- --</span>
  }

  return (
    <span className={className}>
      {showDate && formattedDate && <span className="font-medium">{formattedDate}, </span>}
      {formattedTime}
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

  // State to track client-side hydration and store formatted value
  const [isMounted, setIsMounted] = useState(false)
  const [formattedRange, setFormattedRange] = useState<string | null>(null)

  // Only format dates on the client to avoid hydration mismatch
  useEffect(() => {
    setIsMounted(true)
  }, [])

  // Format time range when mounted and timezone is loaded
  useEffect(() => {
    if (!isMounted) return
    if (!isLoaded && !userTimezoneProp) return

    const startTime = formatTimeInTimezone(startDate, userTimezone)
    const endTime = formatTimeInTimezone(endDate, userTimezone)
    const abbr = getTimezoneOffset(userTimezone)

    setFormattedRange(`${startTime} - ${endTime} ${abbr}`)
  }, [isMounted, isLoaded, userTimezoneProp, startDate, endDate, userTimezone])

  // Show loading state during SSR and initial hydration
  if (!isMounted || (!isLoaded && !userTimezoneProp) || formattedRange === null) {
    return <span className={`text-slate-400 ${className}`}>--:-- - --:-- --</span>
  }

  return (
    <span className={className}>
      {formattedRange}
    </span>
  )
}
