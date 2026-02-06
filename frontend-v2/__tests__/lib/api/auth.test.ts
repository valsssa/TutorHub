import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authApi } from '@/lib/api/auth';
import { api } from '@/lib/api/client';
import type { User, AuthTokens, LoginInput, RegisterInput } from '@/types';

vi.mock('@/lib/api/client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    postForm: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('authApi', () => {
  const mockUser: User = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    full_name: 'Test User',
    profile_incomplete: false,
    role: 'student',
    is_active: true,
    is_verified: true,
    timezone: 'UTC',
    currency: 'USD',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const mockTokens: AuthTokens = {
    access_token: 'mock-jwt-token',
    token_type: 'bearer',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('login', () => {
    it('calls postForm with username (email) and password', async () => {
      vi.mocked(api.postForm).mockResolvedValueOnce(mockTokens);

      const loginData: LoginInput = {
        email: 'user@example.com',
        password: 'password123',
      };

      const result = await authApi.login(loginData);

      expect(api.postForm).toHaveBeenCalledWith('/auth/login', {
        username: 'user@example.com',
        password: 'password123',
      });
      expect(result).toEqual(mockTokens);
    });

    it('maps email field to username for OAuth2 compatibility', async () => {
      vi.mocked(api.postForm).mockResolvedValueOnce(mockTokens);

      await authApi.login({ email: 'test@test.com', password: 'pass' });

      const callArgs = vi.mocked(api.postForm).mock.calls[0];
      expect(callArgs[1]).toHaveProperty('username', 'test@test.com');
      expect(callArgs[1]).not.toHaveProperty('email');
    });

    it('uses form-urlencoded content type (via postForm)', async () => {
      vi.mocked(api.postForm).mockResolvedValueOnce(mockTokens);

      await authApi.login({ email: 'test@test.com', password: 'pass' });

      expect(api.postForm).toHaveBeenCalled();
      expect(api.post).not.toHaveBeenCalled();
    });
  });

  describe('register', () => {
    it('calls post with registration data', async () => {
      vi.mocked(api.post).mockResolvedValueOnce(mockUser);

      const registerData: RegisterInput = {
        email: 'newuser@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
        role: 'student',
      };

      const result = await authApi.register(registerData);

      expect(api.post).toHaveBeenCalledWith('/auth/register', registerData);
      expect(result).toEqual(mockUser);
    });

    it('supports tutor role registration', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ ...mockUser, role: 'tutor' });

      const registerData: RegisterInput = {
        email: 'tutor@example.com',
        password: 'password123',
        first_name: 'Tutor',
        last_name: 'User',
        role: 'tutor',
      };

      await authApi.register(registerData);

      expect(api.post).toHaveBeenCalledWith('/auth/register', expect.objectContaining({
        role: 'tutor',
      }));
    });
  });

  describe('me', () => {
    it('calls get on /auth/me endpoint', async () => {
      vi.mocked(api.get).mockResolvedValueOnce(mockUser);

      const result = await authApi.me();

      expect(api.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });

    it('returns user data with all fields', async () => {
      const fullUser: User = {
        id: 42,
        email: 'full@example.com',
        first_name: 'Full',
        last_name: 'User',
        full_name: 'Full User',
        profile_incomplete: false,
        role: 'admin',
        avatar_url: 'https://example.com/avatar.jpg',
        is_active: true,
        is_verified: true,
        timezone: 'America/New_York',
        currency: 'USD',
        created_at: '2024-06-15T10:30:00Z',
        updated_at: '2024-06-15T10:30:00Z',
      };
      vi.mocked(api.get).mockResolvedValueOnce(fullUser);

      const result = await authApi.me();

      expect(result).toEqual(fullUser);
      expect(result.avatar_url).toBe('https://example.com/avatar.jpg');
    });
  });

  describe('logout', () => {
    it('calls POST on /auth/logout endpoint', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ message: 'Logged out' });

      const result = await authApi.logout();

      expect(api.post).toHaveBeenCalledWith('/auth/logout');
      expect(result).toEqual({ message: 'Logged out' });
    });
  });

  describe('forgotPassword', () => {
    it('calls post with email', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ message: 'Email sent' });

      const result = await authApi.forgotPassword('user@example.com');

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset-request', {
        email: 'user@example.com',
      });
      expect(result).toEqual({ message: 'Email sent' });
    });
  });

  describe('resetPassword', () => {
    it('calls post with token and new password', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ message: 'Password reset' });

      const result = await authApi.resetPassword('reset-token-123', 'newPassword');

      expect(api.post).toHaveBeenCalledWith('/auth/password/reset-confirm', {
        token: 'reset-token-123',
        new_password: 'newPassword',
      });
      expect(result).toEqual({ message: 'Password reset' });
    });
  });

  describe('verifyEmail', () => {
    it('calls post with verification token', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ message: 'Email verified' });

      const result = await authApi.verifyEmail('verify-token-456');

      expect(api.post).toHaveBeenCalledWith('/auth/verify-email', {
        token: 'verify-token-456',
      });
      expect(result).toEqual({ message: 'Email verified' });
    });
  });

  describe('updateProfile', () => {
    it('calls put with partial user data', async () => {
      const updatedUser = { ...mockUser, first_name: 'Updated' };
      vi.mocked(api.put).mockResolvedValueOnce(updatedUser);

      const result = await authApi.updateProfile({ first_name: 'Updated' });

      expect(api.put).toHaveBeenCalledWith('/auth/me', { first_name: 'Updated' });
      expect(result).toEqual(updatedUser);
    });

    it('supports updating multiple fields', async () => {
      const updates = {
        first_name: 'New',
        last_name: 'Name',
        avatar_url: 'https://new-avatar.com/img.jpg',
      };
      vi.mocked(api.put).mockResolvedValueOnce({ ...mockUser, ...updates });

      await authApi.updateProfile(updates);

      expect(api.put).toHaveBeenCalledWith('/auth/me', updates);
    });
  });

  describe('changePassword', () => {
    it('calls post with current and new password', async () => {
      vi.mocked(api.post).mockResolvedValueOnce({ message: 'Password changed' });

      const result = await authApi.changePassword('oldPass123', 'newPass456');

      expect(api.post).toHaveBeenCalledWith('/auth/change-password', {
        current_password: 'oldPass123',
        new_password: 'newPass456',
      });
      expect(result).toEqual({ message: 'Password changed' });
    });
  });
});
