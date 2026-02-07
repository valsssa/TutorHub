import { describe, it, expect } from 'vitest';
import { createBookingSchema } from '@/lib/validators/booking';

describe('Booking schema - past date validation', () => {
  const validBase = {
    tutor_id: 1,
    subject_id: 1,
    duration: '60' as const,
  };

  it('rejects a date in the past', () => {
    const pastDate = new Date('2020-01-01T10:00:00').toISOString();
    const result = createBookingSchema.safeParse({
      ...validBase,
      start_time: pastDate,
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const messages = result.error.issues.map((i) => i.message);
      expect(messages).toContain('Session must be scheduled in the future');
    }
  });

  it('rejects the current time (not strictly in future)', () => {
    // Use a time slightly in the past to avoid race conditions
    const now = new Date(Date.now() - 60_000).toISOString();
    const result = createBookingSchema.safeParse({
      ...validBase,
      start_time: now,
    });
    expect(result.success).toBe(false);
  });

  it('accepts a date in the future', () => {
    const futureDate = new Date(Date.now() + 86_400_000).toISOString();
    const result = createBookingSchema.safeParse({
      ...validBase,
      start_time: futureDate,
    });
    expect(result.success).toBe(true);
  });

  it('rejects an empty start_time', () => {
    const result = createBookingSchema.safeParse({
      ...validBase,
      start_time: '',
    });
    expect(result.success).toBe(false);
  });

  it('rejects an invalid date string', () => {
    const result = createBookingSchema.safeParse({
      ...validBase,
      start_time: 'not-a-date',
    });
    expect(result.success).toBe(false);
  });
});

describe('Booking form - min datetime attribute', () => {
  it('booking form page sets min attribute on datetime-local input', () => {
    // Verify the source code pattern via file read
    const fs = require('fs');
    const path = require('path');
    const source = fs.readFileSync(
      path.resolve(
        __dirname,
        '../../../app/(dashboard)/bookings/new/page.tsx'
      ),
      'utf-8'
    );
    expect(source).toContain('min={minDateTime}');
    expect(source).toContain("type=\"datetime-local\"");
    expect(source).toContain('const minDateTime = useMemo');
  });
});
