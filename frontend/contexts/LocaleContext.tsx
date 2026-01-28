'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { localeUtils } from '@/lib/locale'

interface LocaleContextType {
  locale: string
  currency: string
  setLocale: (locale: string) => void
  setCurrency: (currency: string) => void
  formatPrice: (amount: number) => string
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined)

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState(() => localeUtils.getDefaultLocale())
  const [currency, setCurrencyState] = useState(() => localeUtils.getDefaultCurrency())

  const setLocale = (newLocale: string) => {
    setLocaleState(newLocale)
    localeUtils.setLocale(newLocale)
  }

  const setCurrency = (newCurrency: string) => {
    setCurrencyState(newCurrency)
    localeUtils.setCurrency(newCurrency)
  }

  const formatPrice = (amount: number) => {
    return localeUtils.formatPrice(amount, currency)
  }

  return (
    <LocaleContext.Provider
      value={{
        locale,
        currency,
        setLocale,
        setCurrency,
        formatPrice,
      }}
    >
      {children}
    </LocaleContext.Provider>
  )
}

export function useLocale() {
  const context = useContext(LocaleContext)
  if (context === undefined) {
    throw new Error('useLocale must be used within a LocaleProvider')
  }
  return context
}
