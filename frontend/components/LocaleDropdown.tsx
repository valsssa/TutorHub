'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FiGlobe, FiChevronDown, FiCheck } from 'react-icons/fi'
import { LANGUAGES, CURRENCIES, localeUtils } from '@/lib/locale'
import { useToast } from './ToastContainer'
import { useLocale } from '@/contexts/LocaleContext'

export default function LocaleDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const { showSuccess } = useToast()
  const { locale, currency, setLocale: setGlobalLocale, setCurrency: setGlobalCurrency } = useLocale()

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  const handleLanguageChange = (code: string) => {
    const language = localeUtils.getLanguage(code)
    if (!language) return

    setGlobalLocale(code)
    showSuccess(`Language changed to ${language.nativeLabel} ${language.flag}`)
    setIsOpen(false)
  }

  const handleCurrencyChange = (code: string) => {
    const curr = localeUtils.getCurrency(code)
    if (!curr) return

    setGlobalCurrency(code)
    showSuccess(`Currency changed to ${code} (${curr.symbol})`)
    setIsOpen(false)
  }

  const currentLanguage = localeUtils.getLanguage(locale)
  const currentCurrency = localeUtils.getCurrency(currency)

  return (
    <div className="relative z-[10000]" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-3 py-2 text-text-secondary hover:text-brand-rose transition-colors rounded-lg hover:bg-gray-50"
        aria-label="Language and currency"
        aria-expanded={isOpen}
      >
        <FiGlobe className="w-5 h-5" />
        <span className="hidden sm:inline text-sm font-medium">
          {locale.toUpperCase()} · {currency}
        </span>
        <FiChevronDown className="w-4 h-4" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-floating border border-gray-100 py-2 z-[10001]"
            role="menu"
          >
            {/* Language Section */}
            <div className="mb-1 px-3 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wide">
              🌐 Language
            </div>
            <div className="max-h-48 overflow-y-auto">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className="w-full text-left px-3 py-2 hover:bg-sky-50 transition-colors flex items-center justify-between group"
                  role="menuitem"
                >
                  <span className="flex items-center gap-2 text-sm">
                    <span>{lang.flag}</span>
                    <span className="font-medium text-text-primary">
                      {lang.nativeLabel}
                    </span>
                  </span>
                  {locale === lang.code && (
                    <FiCheck className="w-4 h-4 text-brand-rose" />
                  )}
                </button>
              ))}
            </div>

            {/* Divider */}
            <hr className="my-2 border-slate-100" />

            {/* Currency Section */}
            <div className="mb-1 px-3 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wide">
              💰 Currency
            </div>
            <div className="max-h-48 overflow-y-auto">
              {CURRENCIES.map((curr) => (
                <button
                  key={curr.code}
                  onClick={() => handleCurrencyChange(curr.code)}
                  className="w-full text-left px-3 py-2 hover:bg-sky-50 transition-colors flex items-center justify-between group"
                  role="menuitem"
                >
                  <span className="text-sm font-medium text-text-primary">
                    {curr.code}
                  </span>
                  <span className="flex items-center gap-2">
                    <span className="text-slate-500 text-sm">{curr.symbol}</span>
                    {currency === curr.code && (
                      <FiCheck className="w-4 h-4 text-brand-rose" />
                    )}
                  </span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
