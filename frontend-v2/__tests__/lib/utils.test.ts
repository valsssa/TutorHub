import { describe, it, expect } from 'vitest';
import { cn, formatCurrency, formatDate, toQueryString } from '@/lib/utils';

describe('cn', () => {
  it('merges class names', () => {
    const result = cn('foo', 'bar');
    expect(result).toBe('foo bar');
  });

  it('handles conditional classes', () => {
    const isActive = true;
    const result = cn('base', isActive && 'active');
    expect(result).toBe('base active');
  });

  it('handles false conditional classes', () => {
    const isActive = false;
    const result = cn('base', isActive && 'active');
    expect(result).toBe('base');
  });

  it('merges tailwind classes correctly', () => {
    const result = cn('px-2 py-1', 'px-4');
    expect(result).toBe('py-1 px-4');
  });

  it('handles arrays of classes', () => {
    const result = cn(['foo', 'bar'], 'baz');
    expect(result).toBe('foo bar baz');
  });

  it('handles objects with boolean values', () => {
    const result = cn({
      foo: true,
      bar: false,
      baz: true,
    });
    expect(result).toBe('foo baz');
  });

  it('handles undefined and null values', () => {
    const result = cn('foo', undefined, null, 'bar');
    expect(result).toBe('foo bar');
  });

  it('handles empty string', () => {
    const result = cn('foo', '', 'bar');
    expect(result).toBe('foo bar');
  });
});

describe('formatCurrency', () => {
  it('formats USD by default', () => {
    const result = formatCurrency(1234.56);
    expect(result).toBe('$1,234.56');
  });

  it('formats EUR', () => {
    const result = formatCurrency(1234.56, 'EUR');
    expect(result).toContain('1,234.56');
  });

  it('formats GBP', () => {
    const result = formatCurrency(1234.56, 'GBP');
    expect(result).toContain('1,234.56');
  });

  it('formats zero', () => {
    const result = formatCurrency(0);
    expect(result).toBe('$0.00');
  });

  it('formats negative values', () => {
    const result = formatCurrency(-50);
    expect(result).toBe('-$50.00');
  });

  it('formats large numbers with commas', () => {
    const result = formatCurrency(1000000);
    expect(result).toBe('$1,000,000.00');
  });

  it('rounds to two decimal places', () => {
    const result = formatCurrency(10.999);
    expect(result).toBe('$11.00');
  });
});

describe('formatDate', () => {
  it('formats date string with default options', () => {
    const result = formatDate('2024-06-15');
    expect(result).toContain('Jun');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('formats Date object', () => {
    const date = new Date(2024, 5, 15);
    const result = formatDate(date);
    expect(result).toContain('Jun');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('accepts custom format options', () => {
    const result = formatDate('2024-06-15', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
    });
    expect(result).toContain('Saturday');
    expect(result).toContain('June');
    expect(result).toContain('15');
  });

  it('formats with year only', () => {
    const result = formatDate('2024-06-15', { year: 'numeric' });
    expect(result).toBe('2024');
  });

  it('formats ISO timestamp', () => {
    const result = formatDate('2024-06-15T14:30:00Z');
    expect(result).toContain('Jun');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });
});

describe('toQueryString', () => {
  it('converts object to query string', () => {
    const result = toQueryString({ foo: 'bar', baz: '123' });
    expect(result).toBe('foo=bar&baz=123');
  });

  it('filters out undefined values', () => {
    const result = toQueryString({ foo: 'bar', baz: undefined });
    expect(result).toBe('foo=bar');
  });

  it('filters out null values', () => {
    const result = toQueryString({ foo: 'bar', baz: null });
    expect(result).toBe('foo=bar');
  });

  it('filters out empty strings', () => {
    const result = toQueryString({ foo: 'bar', baz: '' });
    expect(result).toBe('foo=bar');
  });

  it('converts numbers to strings', () => {
    const result = toQueryString({ page: 1, limit: 10 });
    expect(result).toBe('page=1&limit=10');
  });

  it('converts booleans to strings', () => {
    const result = toQueryString({ active: true, archived: false });
    expect(result).toBe('active=true&archived=false');
  });

  it('returns empty string for empty object', () => {
    const result = toQueryString({});
    expect(result).toBe('');
  });

  it('returns empty string when all values are filtered', () => {
    const result = toQueryString({ foo: undefined, bar: null, baz: '' });
    expect(result).toBe('');
  });

  it('encodes special characters', () => {
    const result = toQueryString({ search: 'hello world' });
    expect(result).toBe('search=hello+world');
  });

  it('handles zero values correctly', () => {
    const result = toQueryString({ count: 0 });
    expect(result).toBe('count=0');
  });
});
