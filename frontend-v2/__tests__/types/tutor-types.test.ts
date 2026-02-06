import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('TutorProfileStatus type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/tutor.ts'),
    'utf-8'
  );

  it('should have TutorProfileStatus type defined', () => {
    expect(typeFile).toContain('TutorProfileStatus');
  });

  it('should include all valid status values', () => {
    const validStatuses = [
      'incomplete', 'pending_approval', 'under_review',
      'approved', 'rejected', 'archived'
    ];
    for (const status of validStatuses) {
      expect(typeFile).toContain(`'${status}'`);
    }
  });
});

describe('TutorProfile type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/tutor.ts'),
    'utf-8'
  );

  it('should use typed profile_status', () => {
    expect(typeFile).toMatch(/profile_status.*TutorProfileStatus/);
  });
});
