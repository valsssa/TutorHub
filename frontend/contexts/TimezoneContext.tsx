'use client'

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { getBrowserTimezone, formatInUserTimezone, getTimezoneOffset } from '@/lib/timezone'
import Cookies from 'js-cookie'

interface TimezoneContextType {
  /** User's saved timezone preference */
  userTimezone: string
  /** Browser's detected timezone */
  browserTimezone: string
  /** Whether user timezone has been loaded from user data */
  isLoaded: boolean
  /** Set user's timezone preference */
  setUserTimezone: (tz: string) => void
  /** Format a date in the user's timezone */
  formatInUserTimezone: (date: Date | string) => string
  /** Get timezone abbreviation (e.g., "EST", "PST") */
  getAbbreviation: (timezone?: string) => string
}

const TimezoneContext = createContext<TimezoneContextType | undefined>(undefined)

const TIMEZONE_STORAGE_KEY = 'user_timezone'

export function TimezoneProvider({ children }: { children: ReactNode }) {
  const [userTimezone, setUserTimezoneState] = useState<string>('UTC')
  const [browserTimezone] = useState(() => getBrowserTimezone())
  const [isLoaded, setIsLoaded] = useState(false)

  // Load timezone from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(TIMEZONE_STORAGE_KEY)
    if (stored) {
      setUserTimezoneState(stored)
    } else {
      // Default to browser timezone if no stored preference
      setUserTimezoneState(browserTimezone)
    }
    setIsLoaded(true)
  }, [browserTimezone])

  const setUserTimezone = useCallback((tz: string) => {
    setUserTimezoneState(tz)
    localStorage.setItem(TIMEZONE_STORAGE_KEY, tz)
  }, [])

  const formatDate = useCallback(
    (date: Date | string): string => {
      return formatInUserTimezone(date, userTimezone)
    },
    [userTimezone]
  )

  const getAbbreviation = useCallback(
    (timezone?: string): string => {
      return getTimezoneOffset(timezone || userTimezone)
    },
    [userTimezone]
  )

  return (
    <TimezoneContext.Provider
      value={{
        userTimezone,
        browserTimezone,
        isLoaded,
        setUserTimezone,
        formatInUserTimezone: formatDate,
        getAbbreviation,
      }}
    >
      {children}
    </TimezoneContext.Provider>
  )
}

export function useTimezone() {
  const context = useContext(TimezoneContext)
  if (context === undefined) {
    throw new Error('useTimezone must be used within a TimezoneProvider')
  }
  return context
}
