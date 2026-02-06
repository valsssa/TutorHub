import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

// Extract the type definition block from the file
function extractTypeBlock(content: string, typeName: string): string {
  const regex = new RegExp(`export type ${typeName} =[\\s\\S]*?;`, 'm');
  const match = content.match(regex);
  return match ? match[0] : '';
}

describe('DisputeState type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should have DisputeState type defined', () => {
    expect(typeFile).toContain('DisputeState');
  });

  it('should include all valid dispute states', () => {
    const disputeStateBlock = extractTypeBlock(typeFile, 'DisputeState');

    // Verify we found the type block
    expect(disputeStateBlock).toContain('export type DisputeState');

    const validStates = ['NONE', 'OPEN', 'RESOLVED_UPHELD', 'RESOLVED_REFUNDED'];
    for (const state of validStates) {
      expect(disputeStateBlock).toContain(`'${state}'`);
    }
  });
});

describe('SessionOutcome type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should have SessionOutcome type defined', () => {
    expect(typeFile).toContain('SessionOutcome');
  });

  it('should include all valid outcomes', () => {
    const sessionOutcomeBlock = extractTypeBlock(typeFile, 'SessionOutcome');

    // Verify we found the type block
    expect(sessionOutcomeBlock).toContain('export type SessionOutcome');

    const validOutcomes = ['COMPLETED', 'NOT_HELD', 'NO_SHOW_STUDENT', 'NO_SHOW_TUTOR'];
    for (const outcome of validOutcomes) {
      expect(sessionOutcomeBlock).toContain(`'${outcome}'`);
    }
  });
});

describe('Booking interface uses state types', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/booking.ts'),
    'utf-8'
  );

  it('should have session_outcome field using SessionOutcome type', () => {
    expect(typeFile).toMatch(/session_outcome\??: SessionOutcome/);
  });

  it('should have dispute_state field using DisputeState type', () => {
    expect(typeFile).toMatch(/dispute_state\??: DisputeState/);
  });
});
