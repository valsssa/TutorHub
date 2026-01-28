import { renderHook } from '@testing-library/react'
import { usePrice } from '@/hooks/usePrice'
import { LocaleProvider } from '@/contexts/LocaleContext'
import { ReactNode } from 'react'

// Mock the LocaleContext
jest.mock('@/contexts/LocaleContext', () => ({
  ...jest.requireActual('@/contexts/LocaleContext'),
  useLocale: jest.fn(),
  LocaleProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
}))

describe('usePrice Hook', () => {
  const mockFormatPrice = jest.fn((price: number) => `$${price.toFixed(2)}`)
  
  beforeEach(() => {
    jest.clearAllMocks()
    const { useLocale } = require('@/contexts/LocaleContext')
    useLocale.mockReturnValue({
      currency: 'USD',
      formatPrice: mockFormatPrice,
    })
  })

  it('returns currency and formatPrice from locale context', () => {
    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(result.current.currency).toBe('USD')
    expect(result.current.formatPrice).toBe(mockFormatPrice)
  })

  it('formatPrice function works correctly', () => {
    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    const formatted = result.current.formatPrice(100)
    expect(formatted).toBe('$100.00')
    expect(mockFormatPrice).toHaveBeenCalledWith(100)
  })

  it('handles different currency settings', () => {
    const { useLocale } = require('@/contexts/LocaleContext')
    useLocale.mockReturnValue({
      currency: 'EUR',
      formatPrice: (price: number) => `€${price.toFixed(2)}`,
    })

    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(result.current.currency).toBe('EUR')
  })

  it('handles different currency settings - GBP', () => {
    const { useLocale } = require('@/contexts/LocaleContext')
    useLocale.mockReturnValue({
      currency: 'GBP',
      formatPrice: (price: number) => `£${price.toFixed(2)}`,
    })

    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(result.current.currency).toBe('GBP')
    const formatted = result.current.formatPrice(50)
    expect(formatted).toBe('£50.00')
  })

  it('re-renders when context changes', () => {
    const { useLocale } = require('@/contexts/LocaleContext')
    
    // Initial state
    useLocale.mockReturnValue({
      currency: 'USD',
      formatPrice: mockFormatPrice,
    })

    const { result, rerender } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(result.current.currency).toBe('USD')

    // Change context
    useLocale.mockReturnValue({
      currency: 'EUR',
      formatPrice: (price: number) => `€${price}`,
    })

    rerender()

    expect(result.current.currency).toBe('EUR')
  })

  it('returns both currency and formatPrice properties', () => {
    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(result.current).toHaveProperty('currency')
    expect(result.current).toHaveProperty('formatPrice')
  })

  it('formatPrice is a function', () => {
    const { result } = renderHook(() => usePrice(), {
      wrapper: LocaleProvider,
    })

    expect(typeof result.current.formatPrice).toBe('function')
  })
})
