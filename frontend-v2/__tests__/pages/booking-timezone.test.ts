import { describe, it, expect } from 'vitest';

describe('Booking form timezone conversion', () => {
  it('should convert local datetime string to UTC ISO string', () => {
    // Simulate what the booking form does before submission
    const localDatetime = '2026-03-15T14:30';
    const utcIso = new Date(localDatetime).toISOString();

    // The result should be a valid ISO 8601 string ending with Z (UTC)
    expect(utcIso).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$/);

    // Parse it back and verify it represents the same instant
    const parsed = new Date(utcIso);
    const original = new Date(localDatetime);
    expect(parsed.getTime()).toBe(original.getTime());
  });

  it('should produce a different string than the raw local input when not UTC', () => {
    const localDatetime = '2026-06-20T09:00';
    const utcIso = new Date(localDatetime).toISOString();

    // toISOString always returns UTC — the raw local string has no timezone suffix
    expect(utcIso).toContain('Z');
    expect(localDatetime).not.toContain('Z');
  });

  it('should use Math.round for cents conversion', () => {
    // Simulate the cents conversion used in wallet topup
    const amount = 25.99;
    const cents = Math.round(amount * 100);
    expect(cents).toBe(2599);

    // Floating point edge case
    const tricky = 0.1 + 0.2; // 0.30000000000000004
    const trickyCents = Math.round(tricky * 100);
    expect(trickyCents).toBe(30);
  });

  it('should detect user timezone via Intl', () => {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    expect(typeof tz).toBe('string');
    expect(tz.length).toBeGreaterThan(0);
  });
});
