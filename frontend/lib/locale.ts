import Cookies from 'js-cookie'

export interface Language {
  code: string
  label: string
  nativeLabel: string
  flag: string
}

export interface Currency {
  code: string
  symbol: string
  label: string
}

export const LANGUAGES: Language[] = [
  { code: 'en', label: 'English', nativeLabel: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'Spanish', nativeLabel: 'Español', flag: '🇪🇸' },
  { code: 'fr', label: 'French', nativeLabel: 'Français', flag: '🇫🇷' },
  { code: 'de', label: 'German', nativeLabel: 'Deutsch', flag: '🇩🇪' },
  { code: 'pl', label: 'Polish', nativeLabel: 'Polski', flag: '🇵🇱' },
  { code: 'ar', label: 'Arabic', nativeLabel: 'العربية', flag: '🌙' },
]

export const CURRENCIES: Currency[] = [
  { code: 'USD', symbol: '$', label: 'US Dollar' },
  { code: 'EUR', symbol: '€', label: 'Euro' },
  { code: 'GBP', symbol: '£', label: 'British Pound' },
  { code: 'PLN', symbol: 'zł', label: 'Polish Złoty' },
  { code: 'INR', symbol: '₹', label: 'Indian Rupee' },
  { code: 'JPY', symbol: '¥', label: 'Japanese Yen' },
]

const LOCALE_COOKIE = 'locale'
const CURRENCY_COOKIE = 'currency'

export const localeUtils = {
  getDefaultLocale: (): string => {
    if (typeof window === 'undefined') return 'en'
    const saved = Cookies.get(LOCALE_COOKIE)
    if (saved) return saved
    
    const browserLang = navigator.language.split('-')[0]
    const supported = LANGUAGES.find(l => l.code === browserLang)
    return supported ? supported.code : 'en'
  },

  getDefaultCurrency: (): string => {
    if (typeof window === 'undefined') return 'USD'
    const saved = Cookies.get(CURRENCY_COOKIE)
    if (saved) return saved
    
    return 'USD'
  },

  setLocale: (locale: string): void => {
    Cookies.set(LOCALE_COOKIE, locale, { expires: 365 })
    if (typeof window !== 'undefined') {
      localStorage.setItem(LOCALE_COOKIE, locale)
    }
  },

  setCurrency: (currency: string): void => {
    Cookies.set(CURRENCY_COOKIE, currency, { expires: 365 })
    if (typeof window !== 'undefined') {
      localStorage.setItem(CURRENCY_COOKIE, currency)
    }
  },

  getLanguage: (code: string): Language | undefined => {
    return LANGUAGES.find(l => l.code === code)
  },

  getCurrency: (code: string): Currency | undefined => {
    return CURRENCIES.find(c => c.code === code)
  },

  formatPrice: (amount: number, currencyCode: string = 'USD'): string => {
    const currency = CURRENCIES.find(c => c.code === currencyCode)
    if (!currency) return `${amount}`

    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currencyCode,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(amount)
    } catch {
      return `${currency.symbol}${amount}`
    }
  },
}
