import { useLocale } from '@/contexts/LocaleContext'

export function usePrice() {
  const { currency, formatPrice } = useLocale()

  return {
    currency,
    formatPrice,
  }
}
