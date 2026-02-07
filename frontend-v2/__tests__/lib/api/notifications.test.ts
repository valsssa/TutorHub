import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock the api client
const mockGet = vi.fn();
const mockPatch = vi.fn();
const mockDelete = vi.fn();
const mockPut = vi.fn();

vi.mock('@/lib/api/client', () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
    put: (...args: unknown[]) => mockPut(...args),
  },
}));

vi.mock('@/lib/utils', () => ({
  toQueryString: (params: Record<string, string | number | boolean>) =>
    Object.entries(params)
      .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
      .join('&'),
}));

import { notificationsApi } from '@/lib/api/notifications';

describe('notificationsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ items: [], total: 0, unread_count: 0 });
  });

  describe('getNotifications', () => {
    it('calls API with no query params when no filters provided', async () => {
      await notificationsApi.getNotifications();
      expect(mockGet).toHaveBeenCalledWith('/notifications');
    });

    it('passes type filter as query param', async () => {
      await notificationsApi.getNotifications({ type: 'booking_request' });
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('type=booking_request')
      );
    });

    it('passes category filter as query param', async () => {
      await notificationsApi.getNotifications({ category: 'bookings' });
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('category=bookings')
      );
    });

    it('passes unread_only filter as query param', async () => {
      await notificationsApi.getNotifications({ unread_only: true });
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('unread_only=true')
      );
    });

    it('passes limit filter as query param', async () => {
      await notificationsApi.getNotifications({ limit: 10 });
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('limit=10')
      );
    });

    it('maps page_size to limit when limit is not set', async () => {
      await notificationsApi.getNotifications({ page_size: 5 });
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining('limit=5')
      );
    });

    it('prefers limit over page_size when both are set', async () => {
      await notificationsApi.getNotifications({ limit: 10, page_size: 5 });
      const callArg = mockGet.mock.calls[0][0] as string;
      expect(callArg).toContain('limit=10');
      // Should not have two limit params
      const limitMatches = callArg.match(/limit=/g);
      expect(limitMatches).toHaveLength(1);
    });

    it('normalizes is_read field in response', async () => {
      mockGet.mockResolvedValue({
        items: [
          { id: 1, type: 'message', title: 'Test', message: 'msg', read: true, created_at: '' },
        ],
        total: 1,
        unread_count: 0,
      });

      const result = await notificationsApi.getNotifications();
      expect(result.items[0].is_read).toBe(true);
    });

    it('normalizes is_read to false when both fields are missing', async () => {
      mockGet.mockResolvedValue({
        items: [
          { id: 1, type: 'message', title: 'Test', message: 'msg', created_at: '' },
        ],
        total: 1,
        unread_count: 1,
      });

      const result = await notificationsApi.getNotifications();
      expect(result.items[0].is_read).toBe(false);
    });
  });

  describe('markAsRead', () => {
    it('sends PATCH to correct endpoint', async () => {
      await notificationsApi.markAsRead(42);
      expect(mockPatch).toHaveBeenCalledWith('/notifications/42/read', {});
    });
  });

  describe('markAllAsRead', () => {
    it('sends PATCH to mark-all-read endpoint', async () => {
      await notificationsApi.markAllAsRead();
      expect(mockPatch).toHaveBeenCalledWith('/notifications/mark-all-read', {});
    });
  });

  describe('delete', () => {
    it('sends DELETE to correct endpoint', async () => {
      await notificationsApi.delete(99);
      expect(mockDelete).toHaveBeenCalledWith('/notifications/99');
    });
  });
});
