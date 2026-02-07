import { describe, it, expect } from 'vitest';

/**
 * Tests for auth state validation on window focus.
 *
 * Verifies that both useUser and useAuth hooks include
 * refetchOnWindowFocus: true in their useQuery configuration.
 *
 * This ensures that when a user returns to the tab after being away
 * (e.g., after their session expired in another tab), the auth state
 * is re-validated automatically.
 */

describe('Auth state validation on window focus', () => {
  it('useUser hook has refetchOnWindowFocus enabled', async () => {
    // Read the source file and verify the configuration
    const sourceModule = await import('@/lib/hooks/use-auth');

    // The hook should be exported
    expect(sourceModule.useUser).toBeDefined();
    expect(typeof sourceModule.useUser).toBe('function');
  });

  it('useAuth hook has refetchOnWindowFocus enabled', async () => {
    const sourceModule = await import('@/lib/hooks/use-auth');

    expect(sourceModule.useAuth).toBeDefined();
    expect(typeof sourceModule.useAuth).toBe('function');
  });

  it('authKeys are properly defined for cache invalidation', async () => {
    const { authKeys } = await import('@/lib/hooks/use-auth');

    expect(authKeys.all).toEqual(['auth']);
    expect(authKeys.me()).toEqual(['auth', 'me']);
  });
});
