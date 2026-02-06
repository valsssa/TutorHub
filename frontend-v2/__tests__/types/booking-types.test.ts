import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const LEGACY_SESSION_STATES = [
  'pending_tutor', 'pending_student', 'confirmed', 'in_progress',
  'completed', 'cancelled', 'expired', 'no_show',
];

const LEGACY_PAYMENT_STATES = [
  'pending', 'authorized', 'captured', 'released_to_tutor', 'refunded', 'failed',
];

describe('SessionState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    for (const legacyState of LEGACY_SESSION_STATES) {
      expect(typeFile).not.toContain(`'${legacyState}'`);
    }
  });
});

describe('PaymentState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    for (const legacyState of LEGACY_PAYMENT_STATES) {
      expect(typeFile).not.toContain(`'${legacyState}'`);
    }
  });
});
