import { renderHook, waitFor } from '@testing-library/react'
import { useDebounce } from '@/hooks/useDebounce'
import { act } from 'react'

describe('useDebounce Hook', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500))
    expect(result.current).toBe('initial')
  })

  it('debounces value changes with default delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    expect(result.current).toBe('initial')

    // Update value
    rerender({ value: 'updated', delay: 500 })
    
    // Value should not change immediately
    expect(result.current).toBe('initial')

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Value should now be updated
    expect(result.current).toBe('updated')
  })

  it('debounces value changes with custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 1000 },
      }
    )

    rerender({ value: 'updated', delay: 1000 })
    
    // Before delay
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe('initial')

    // After delay
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe('updated')
  })

  it('cancels previous timeout on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: 'first' },
      }
    )

    // First change
    rerender({ value: 'second' })
    act(() => {
      jest.advanceTimersByTime(250)
    })

    // Second change before first completes
    rerender({ value: 'third' })
    act(() => {
      jest.advanceTimersByTime(250)
    })

    // Should still show first value
    expect(result.current).toBe('first')

    // After full delay from last change
    act(() => {
      jest.advanceTimersByTime(250)
    })
    expect(result.current).toBe('third')
  })

  it('handles multiple rapid changes correctly', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: 'v1' },
      }
    )

    // Simulate rapid typing
    rerender({ value: 'v2' })
    act(() => {
      jest.advanceTimersByTime(100)
    })

    rerender({ value: 'v3' })
    act(() => {
      jest.advanceTimersByTime(100)
    })

    rerender({ value: 'v4' })
    act(() => {
      jest.advanceTimersByTime(100)
    })

    rerender({ value: 'v5' })
    
    // Should still be initial value
    expect(result.current).toBe('v1')

    // After full delay from last change
    act(() => {
      jest.advanceTimersByTime(300)
    })
    expect(result.current).toBe('v5')
  })

  it('works with different types (numbers)', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: 0 },
      }
    )

    expect(result.current).toBe(0)

    rerender({ value: 42 })
    
    act(() => {
      jest.advanceTimersByTime(500)
    })
    
    expect(result.current).toBe(42)
  })

  it('works with different types (objects)', () => {
    const initialObj = { name: 'John' }
    const updatedObj = { name: 'Jane' }

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: initialObj },
      }
    )

    expect(result.current).toBe(initialObj)

    rerender({ value: updatedObj })
    
    act(() => {
      jest.advanceTimersByTime(500)
    })
    
    expect(result.current).toBe(updatedObj)
  })

  it('works with different types (arrays)', () => {
    const initialArray = [1, 2, 3]
    const updatedArray = [4, 5, 6]

    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: initialArray },
      }
    )

    expect(result.current).toBe(initialArray)

    rerender({ value: updatedArray })
    
    act(() => {
      jest.advanceTimersByTime(500)
    })
    
    expect(result.current).toBe(updatedArray)
  })

  it('handles zero delay', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 0),
      {
        initialProps: { value: 'initial' },
      }
    )

    rerender({ value: 'updated' })
    
    act(() => {
      jest.advanceTimersByTime(0)
    })
    
    expect(result.current).toBe('updated')
  })

  it('cleans up timeout on unmount', () => {
    const { unmount } = renderHook(() => useDebounce('value', 500))
    
    // Unmount should clear the timeout
    expect(() => unmount()).not.toThrow()
  })

  it('updates delay dynamically', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    )

    rerender({ value: 'updated', delay: 1000 })
    
    // After 500ms (original delay)
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe('initial')

    // After 1000ms (new delay)
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe('updated')
  })

  it('handles empty string values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: 'text' },
      }
    )

    rerender({ value: '' })
    
    act(() => {
      jest.advanceTimersByTime(500)
    })
    
    expect(result.current).toBe('')
  })

  it('handles null and undefined values', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      {
        initialProps: { value: 'text' as string | null | undefined },
      }
    )

    rerender({ value: null })
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe(null)

    rerender({ value: undefined })
    act(() => {
      jest.advanceTimersByTime(500)
    })
    expect(result.current).toBe(undefined)
  })
})
