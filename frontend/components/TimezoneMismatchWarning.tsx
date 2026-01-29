'use client'

import React from 'react'
import { FiAlertTriangle, FiGlobe } from 'react-icons/fi'
import { getTimezoneDisplayName } from '@/lib/timezone'

interface TimezoneMismatchWarningProps {
  /** User's timezone */
  userTimezone: string
  /** Other party's timezone (tutor or student) */
  otherTimezone: string
  /** Label for the other party (e.g., "tutor", "student") */
  otherLabel: string
  /** Optional: approximate hour difference */
  hoursDifference?: number
  /** Variant: inline (small) or banner (prominent) */
  variant?: 'inline' | 'banner'
  /** Custom className for styling */
  className?: string
}

/**
 * Timezone mismatch warning component.
 *
 * Displays a warning when the user's timezone differs from the other
 * party's timezone in a booking context.
 *
 * Usage:
 * ```tsx
 * <TimezoneMismatchWarning
 *   userTimezone="America/New_York"
 *   otherTimezone="America/Los_Angeles"
 *   otherLabel="tutor"
 *   variant="banner"
 * />
 * ```
 */
export default function TimezoneMismatchWarning({
  userTimezone,
  otherTimezone,
  otherLabel,
  hoursDifference,
  variant = 'inline',
  className = '',
}: TimezoneMismatchWarningProps) {
  // Don't show if timezones match
  if (userTimezone === otherTimezone) {
    return null
  }

  const userTzDisplay = getTimezoneDisplayName(userTimezone)
  const otherTzDisplay = getTimezoneDisplayName(otherTimezone)

  if (variant === 'banner') {
    return (
      <div
        className={`flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg ${className}`}
      >
        <FiAlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-medium text-amber-800 dark:text-amber-200">
            Different Timezone
          </h4>
          <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
            You are in <strong>{userTzDisplay}</strong>, but the {otherLabel} is in{' '}
            <strong>{otherTzDisplay}</strong>.
            {hoursDifference && hoursDifference > 0 && (
              <> That&apos;s about {hoursDifference} hour{hoursDifference !== 1 ? 's' : ''} difference.</>
            )}
          </p>
          <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
            Times shown are converted to your timezone. Please double-check the booking time is convenient for both parties.
          </p>
        </div>
      </div>
    )
  }

  // Inline variant - smaller, less prominent
  return (
    <div
      className={`inline-flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400 ${className}`}
    >
      <FiGlobe className="w-3 h-3" />
      <span>
        {otherLabel.charAt(0).toUpperCase() + otherLabel.slice(1)} is in {otherTzDisplay}
        {hoursDifference && hoursDifference > 0 && (
          <span className="text-amber-500"> ({hoursDifference}h diff)</span>
        )}
      </span>
    </div>
  )
}

/**
 * Hook to check for timezone mismatch
 */
export function useTimezoneMismatch(
  userTimezone: string,
  otherTimezone: string | undefined
): { hasMismatch: boolean; hoursDifference: number } {
  if (!userTimezone || !otherTimezone || userTimezone === otherTimezone) {
    return { hasMismatch: false, hoursDifference: 0 }
  }

  // Calculate approximate hour difference
  try {
    const now = new Date()
    const userTime = new Date(now.toLocaleString('en-US', { timeZone: userTimezone }))
    const otherTime = new Date(now.toLocaleString('en-US', { timeZone: otherTimezone }))
    const hoursDifference = Math.abs(
      Math.round((userTime.getTime() - otherTime.getTime()) / (1000 * 60 * 60))
    )

    return { hasMismatch: true, hoursDifference }
  } catch {
    return { hasMismatch: true, hoursDifference: 0 }
  }
}
