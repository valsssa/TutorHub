import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const NOTIFICATION_SETTINGS_PATH = path.resolve(
  __dirname,
  '../../app/(dashboard)/settings/notifications/page.tsx'
);

describe('Notification settings - infinite re-render prevention', () => {
  const source = fs.readFileSync(NOTIFICATION_SETTINGS_PATH, 'utf-8');

  it('has a useEffect that resets form when preferences load', () => {
    expect(source).toContain('form.reset(');
    expect(source).toContain('if (preferences)');
  });

  it('does NOT include form in the useEffect dependency array', () => {
    // The useEffect for resetting form should depend only on [preferences],
    // not [preferences, form], because form is a new reference every render.
    // Find the useEffect block that contains form.reset
    const useEffectMatch = source.match(
      /useEffect\(\s*\(\)\s*=>\s*\{[^}]*form\.reset\([^)]*\)[^}]*\}[\s\S]*?\[([^\]]*)\]/
    );
    expect(useEffectMatch).toBeTruthy();
    if (useEffectMatch) {
      const deps = useEffectMatch[1];
      expect(deps).toContain('preferences');
      expect(deps).not.toMatch(/\bform\b/);
    }
  });

  it('has eslint-disable comment for exhaustive-deps', () => {
    // The eslint-disable is needed because form is intentionally omitted
    expect(source).toContain('eslint-disable-next-line react-hooks/exhaustive-deps');
  });
});
