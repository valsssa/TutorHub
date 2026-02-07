import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const LOGIN_PAGE_PATH = path.resolve(
  __dirname,
  '../../app/(auth)/login/page.tsx'
);

describe('Login page redirect handling', () => {
  const source = fs.readFileSync(LOGIN_PAGE_PATH, 'utf-8');

  it('reads the redirect search param from the URL', () => {
    expect(source).toContain("searchParams.get('redirect')");
  });

  it('validates redirect URL starts with / (prevents open redirect)', () => {
    expect(source).toContain("redirectTo.startsWith('/')");
  });

  it('rejects protocol-relative URLs starting with //', () => {
    expect(source).toContain("!redirectTo.startsWith('//')");
  });

  it('falls back to role-based redirect when no redirect param', () => {
    expect(source).toContain('getRoleBasedRedirect(user.role)');
  });

  it('uses router.push to navigate after login', () => {
    expect(source).toContain('router.push(redirectTo)');
    expect(source).toContain('router.push(getRoleBasedRedirect(user.role))');
  });

  it('does not use window.location for redirect', () => {
    expect(source).not.toContain('window.location.href');
    expect(source).not.toContain('window.location.replace');
  });
});
