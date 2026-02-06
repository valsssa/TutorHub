import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('Booking type fields', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should use start_at as primary field', () => {
    expect(typeFile).toMatch(/^\s+start_at: string;/m);
  });

  it('should NOT have start_time alias', () => {
    // start_time should not exist as a separate field
    expect(typeFile).not.toMatch(/^\s+start_time\??: string;/m);
  });

  it('should use end_at as primary field', () => {
    expect(typeFile).toMatch(/^\s+end_at: string;/m);
  });

  it('should NOT have end_time alias', () => {
    // end_time should not exist as a separate field
    expect(typeFile).not.toMatch(/^\s+end_time\??: string;/m);
  });
});

describe('BookingListResponse type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should NOT have items alias field', () => {
    // BookingListResponse should only have bookings, not items
    expect(typeFile).not.toMatch(/items\?: Booking\[\]/);
  });
});
