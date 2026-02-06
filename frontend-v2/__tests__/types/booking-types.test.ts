import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

// Legacy lowercase states that should NOT appear in the type union definitions
const LEGACY_SESSION_STATES = [
  'pending_tutor', 'pending_student', 'confirmed', 'in_progress',
  'no_show',
];

const LEGACY_PAYMENT_STATES = [
  'released_to_tutor', 'failed',
];

// Extract the type definition block from the file
function extractTypeBlock(content: string, typeName: string): string {
  const regex = new RegExp(`export type ${typeName} =[\\s\\S]*?;`, 'm');
  const match = content.match(regex);
  return match ? match[0] : '';
}

describe('SessionState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    const sessionStateBlock = extractTypeBlock(typeFile, 'SessionState');

    // Verify we found the type block
    expect(sessionStateBlock).toContain('export type SessionState');

    // Check for legacy states in the type definition only
    for (const legacyState of LEGACY_SESSION_STATES) {
      expect(sessionStateBlock).not.toContain(`'${legacyState}'`);
    }

    // Verify expected uppercase states ARE present
    expect(sessionStateBlock).toContain("'REQUESTED'");
    expect(sessionStateBlock).toContain("'SCHEDULED'");
    expect(sessionStateBlock).toContain("'ACTIVE'");
    expect(sessionStateBlock).toContain("'ENDED'");
    expect(sessionStateBlock).toContain("'CANCELLED'");
    expect(sessionStateBlock).toContain("'EXPIRED'");
  });
});

describe('PaymentState type', () => {
  it('should not include legacy lowercase states', () => {
    const typeFile = fs.readFileSync(
      path.join(__dirname, '../../types/booking.ts'),
      'utf-8'
    );
    const paymentStateBlock = extractTypeBlock(typeFile, 'PaymentState');

    // Verify we found the type block
    expect(paymentStateBlock).toContain('export type PaymentState');

    // Check for legacy states in the type definition only
    for (const legacyState of LEGACY_PAYMENT_STATES) {
      expect(paymentStateBlock).not.toContain(`'${legacyState}'`);
    }

    // Verify expected uppercase states ARE present
    expect(paymentStateBlock).toContain("'PENDING'");
    expect(paymentStateBlock).toContain("'AUTHORIZED'");
    expect(paymentStateBlock).toContain("'CAPTURED'");
    expect(paymentStateBlock).toContain("'VOIDED'");
    expect(paymentStateBlock).toContain("'REFUNDED'");
    expect(paymentStateBlock).toContain("'PARTIALLY_REFUNDED'");
  });
});
