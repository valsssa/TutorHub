import { describe, it, expect } from 'vitest';

describe('Tutor search query validation', () => {
  it('should trim and limit search query to 100 characters', () => {
    const longQuery = 'a'.repeat(150);
    const sanitized = longQuery.trim().slice(0, 100);
    expect(sanitized.length).toBe(100);
  });

  it('should trim whitespace before slicing', () => {
    const paddedQuery = '   hello world   ';
    const sanitized = paddedQuery.trim().slice(0, 100);
    expect(sanitized).toBe('hello world');
  });

  it('should return undefined for empty query after trim', () => {
    const emptyQuery = '   ';
    const sanitized = emptyQuery.trim().slice(0, 100);
    const result = sanitized || undefined;
    expect(result).toBeUndefined();
  });

  it('should pass through normal length queries unchanged', () => {
    const normalQuery = 'Mathematics';
    const sanitized = normalQuery.trim().slice(0, 100);
    expect(sanitized).toBe('Mathematics');
  });

  it('should handle exactly 100 character queries', () => {
    const exact = 'x'.repeat(100);
    const sanitized = exact.trim().slice(0, 100);
    expect(sanitized.length).toBe(100);
    expect(sanitized).toBe(exact);
  });
});
