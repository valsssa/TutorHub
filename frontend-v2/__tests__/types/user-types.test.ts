import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

describe('User type', () => {
  const typeFile = fs.readFileSync(
    path.join(__dirname, '../../types/user.ts'),
    'utf-8'
  );

  it('should include profile_incomplete field', () => {
    expect(typeFile).toContain('profile_incomplete');
  });

  it('should include full_name field', () => {
    expect(typeFile).toContain('full_name');
  });

  it('should have first_name as nullable', () => {
    expect(typeFile).toMatch(/first_name.*string \| null/);
  });

  it('should have last_name as nullable', () => {
    expect(typeFile).toMatch(/last_name.*string \| null/);
  });
});
