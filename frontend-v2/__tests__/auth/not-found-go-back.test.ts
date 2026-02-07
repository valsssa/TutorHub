import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const NOT_FOUND_PATH = path.resolve(__dirname, '../../app/not-found.tsx');

describe('404 Not Found page - Go Back button', () => {
  const source = fs.readFileSync(NOT_FOUND_PATH, 'utf-8');

  it('does not use javascript: protocol in any href', () => {
    expect(source).not.toContain('javascript:');
  });

  it('does not use Link component for go-back navigation', () => {
    // "Go back" should not be wrapped in a Link tag with href
    expect(source).not.toMatch(/href=.*Go back/);
  });

  it('uses window.history.back() via onClick handler', () => {
    expect(source).toContain('window.history.back()');
  });

  it('uses a Button component for go-back (not an anchor)', () => {
    // The go-back button should use <Button with onClick, not asChild with Link
    expect(source).toMatch(/Button[^>]*onClick[^>]*>[\s\S]*?Go back/);
  });

  it('has a home link that navigates to /', () => {
    expect(source).toContain('href="/"');
    expect(source).toContain('Go home');
  });
});
