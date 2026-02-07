import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';

const VIDEO_SETTINGS_PATH = path.resolve(
  __dirname,
  '../../app/(dashboard)/settings/video/page.tsx'
);

describe('Video settings - infinite re-render prevention', () => {
  const source = fs.readFileSync(VIDEO_SETTINGS_PATH, 'utf-8');

  it('has a useEffect that resets form when settings load', () => {
    expect(source).toContain('form.reset(');
    expect(source).toContain('if (settings)');
  });

  it('does NOT include form in the useEffect dependency array', () => {
    // The useEffect for resetting form should depend only on [settings],
    // not [settings, form], because form is a new reference every render.
    const useEffectMatch = source.match(
      /useEffect\(\s*\(\)\s*=>\s*\{[^}]*form\.reset\([^)]*\)[^}]*\}[\s\S]*?\[([^\]]*)\]/
    );
    expect(useEffectMatch).toBeTruthy();
    if (useEffectMatch) {
      const deps = useEffectMatch[1];
      expect(deps).toContain('settings');
      expect(deps).not.toMatch(/\bform\b/);
    }
  });

  it('has eslint-disable comment for exhaustive-deps', () => {
    expect(source).toContain('eslint-disable-next-line react-hooks/exhaustive-deps');
  });
});
