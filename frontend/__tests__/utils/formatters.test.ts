import {
  formatCurrency,
  formatDate,
  formatTime,
  formatDateTime,
  formatDateTimeInTimezone,
  formatRelativeTime,
  calculateDuration,
  formatDuration,
  capitalize,
  truncate,
  formatFileSize,
} from '@/shared/utils/formatters'

describe('Formatters Utility Functions', () => {
  describe('formatCurrency', () => {
    it('formats USD currency correctly', () => {
      expect(formatCurrency(100, 'USD')).toContain('100')
    })

    it('formats EUR currency correctly', () => {
      expect(formatCurrency(100, 'EUR')).toContain('100')
    })

    it('handles string amounts', () => {
      expect(formatCurrency('100.50', 'USD')).toContain('100.50')
    })

    it('formats with 2 decimal places', () => {
      const result = formatCurrency(100.5, 'USD')
      expect(result).toMatch(/100\.50/)
    })

    it('uses custom locale when provided', () => {
      const result = formatCurrency(1000, 'USD', 'en-US')
      expect(result).toBeTruthy()
    })

    it('handles zero amount', () => {
      expect(formatCurrency(0, 'USD')).toContain('0.00')
    })

    it('handles negative amounts', () => {
      const result = formatCurrency(-50, 'USD')
      expect(result).toContain('50')
    })
  })

  describe('formatDate', () => {
    it('formats date object', () => {
      const date = new Date('2024-01-15')
      const result = formatDate(date)
      expect(result).toContain('2024')
    })

    it('formats date string', () => {
      const result = formatDate('2024-01-15')
      expect(result).toContain('2024')
    })

    it('respects timezone parameter', () => {
      const date = new Date('2024-01-15T12:00:00Z')
      const result = formatDate(date, 'America/New_York')
      expect(result).toBeTruthy()
    })
  })

  describe('formatTime', () => {
    it('formats time from date object', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatTime(date)
      expect(result).toMatch(/\d{1,2}:\d{2}/)
    })

    it('formats time from date string', () => {
      const result = formatTime('2024-01-15T14:30:00Z')
      expect(result).toMatch(/\d{1,2}:\d{2}/)
    })

    it('respects timezone parameter', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatTime(date, 'America/New_York')
      expect(result).toBeTruthy()
    })
  })

  describe('formatDateTime', () => {
    it('formats date and time together', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatDateTime(date)
      expect(result).toContain('at')
      expect(result).toContain('2024')
    })

    it('handles timezone parameter', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatDateTime(date, 'America/New_York')
      expect(result).toBeTruthy()
    })
  })

  describe('formatDateTimeInTimezone', () => {
    it('formats with timezone name', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatDateTimeInTimezone(date, 'America/New_York')
      expect(result).toBeTruthy()
    })

    it('defaults to UTC', () => {
      const date = new Date('2024-01-15T14:30:00Z')
      const result = formatDateTimeInTimezone(date)
      expect(result).toContain('UTC')
    })
  })

  describe('formatRelativeTime', () => {
    it('returns "just now" for recent times', () => {
      const now = new Date()
      expect(formatRelativeTime(now)).toBe('just now')
    })

    it('formats minutes ago', () => {
      const date = new Date(Date.now() - 5 * 60 * 1000) // 5 minutes ago
      expect(formatRelativeTime(date)).toContain('minutes ago')
    })

    it('formats hours ago', () => {
      const date = new Date(Date.now() - 2 * 60 * 60 * 1000) // 2 hours ago
      expect(formatRelativeTime(date)).toContain('hours ago')
    })

    it('formats days ago', () => {
      const date = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) // 3 days ago
      expect(formatRelativeTime(date)).toContain('days ago')
    })

    it('formats months ago', () => {
      const date = new Date(Date.now() - 60 * 24 * 60 * 60 * 1000) // ~60 days ago
      expect(formatRelativeTime(date)).toContain('months ago')
    })

    it('formats years ago', () => {
      const date = new Date(Date.now() - 400 * 24 * 60 * 60 * 1000) // ~400 days ago
      expect(formatRelativeTime(date)).toContain('years ago')
    })
  })

  describe('calculateDuration', () => {
    it('calculates duration in hours', () => {
      const start = new Date('2024-01-15T10:00:00Z')
      const end = new Date('2024-01-15T12:00:00Z')
      expect(calculateDuration(start, end)).toBe(2)
    })

    it('handles string dates', () => {
      const duration = calculateDuration(
        '2024-01-15T10:00:00Z',
        '2024-01-15T13:00:00Z'
      )
      expect(duration).toBe(3)
    })

    it('handles fractional hours', () => {
      const start = new Date('2024-01-15T10:00:00Z')
      const end = new Date('2024-01-15T10:30:00Z')
      expect(calculateDuration(start, end)).toBe(0.5)
    })
  })

  describe('formatDuration', () => {
    it('formats whole hours', () => {
      expect(formatDuration(2)).toBe('2 hours')
    })

    it('formats single hour', () => {
      expect(formatDuration(1)).toBe('1 hour')
    })

    it('formats hours and minutes', () => {
      expect(formatDuration(2.5)).toBe('2h 30m')
    })

    it('formats minutes only', () => {
      expect(formatDuration(0.5)).toBe('30 minutes')
    })

    it('formats single minute', () => {
      expect(formatDuration(1 / 60)).toBe('1 minute')
    })

    it('handles zero hours', () => {
      expect(formatDuration(0)).toBe('0 minutes')
    })
  })

  describe('capitalize', () => {
    it('capitalizes first letter', () => {
      expect(capitalize('hello')).toBe('Hello')
    })

    it('lowercases rest of string', () => {
      expect(capitalize('HELLO')).toBe('Hello')
    })

    it('handles empty string', () => {
      expect(capitalize('')).toBe('')
    })

    it('handles single character', () => {
      expect(capitalize('a')).toBe('A')
    })

    it('handles mixed case', () => {
      expect(capitalize('hELLo')).toBe('Hello')
    })
  })

  describe('truncate', () => {
    it('truncates long strings', () => {
      expect(truncate('This is a long string', 10)).toBe('This is...')
    })

    it('does not truncate short strings', () => {
      expect(truncate('Short', 10)).toBe('Short')
    })

    it('uses custom suffix', () => {
      expect(truncate('Long string here', 10, '---')).toBe('Long st---')
    })

    it('handles empty string', () => {
      expect(truncate('', 10)).toBe('')
    })

    it('handles exact length', () => {
      expect(truncate('Exact', 5)).toBe('Exact')
    })
  })

  describe('formatFileSize', () => {
    it('formats bytes', () => {
      expect(formatFileSize(500)).toBe('500 Bytes')
    })

    it('formats kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1 KB')
    })

    it('formats megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1 MB')
    })

    it('formats gigabytes', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB')
    })

    it('handles zero bytes', () => {
      expect(formatFileSize(0)).toBe('0 Bytes')
    })

    it('formats decimal values', () => {
      const result = formatFileSize(1536)
      expect(result).toContain('1.5')
      expect(result).toContain('KB')
    })
  })
})
