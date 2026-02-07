import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const REGISTER_PAGE_PATH = path.resolve(
  __dirname,
  '../../app/(auth)/register/page.tsx'
);

describe('Registration page - email already exists handling', () => {
  const source = fs.readFileSync(REGISTER_PAGE_PATH, 'utf-8');

  it('detects "already exists" or "already registered" pattern in error', () => {
    expect(source).toMatch(/already\s*\(exists\|registered\)/i);
  });

  it('shows a user-friendly message for duplicate email', () => {
    expect(source).toContain(
      'An account with this email already exists.'
    );
  });

  it('provides a link to the login page when email exists', () => {
    expect(source).toContain('href="/login"');
    expect(source).toContain('Sign in instead');
  });

  it('falls back to generic error message for other errors', () => {
    expect(source).toContain('Registration failed');
  });

  it('checks registerError instanceof Error before accessing .message', () => {
    expect(source).toContain('registerError instanceof Error');
  });
});
