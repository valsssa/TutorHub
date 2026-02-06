import { api } from './client';
import type {
  MessageThread,
  Message,
  SendMessageInput,
  PaginatedMessagesResponse,
  UnreadCountResponse,
} from '@/types';

export const messagesApi = {
  // Get all conversation threads for current user
  getThreads: (limit = 100) =>
    api.get<MessageThread[]>(`/messages/threads?limit=${limit}`),

  // Get messages in a conversation with another user
  getConversation: (otherUserId: number, page = 1, pageSize = 50, bookingId?: number) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (bookingId) params.append('booking_id', String(bookingId));
    return api.get<PaginatedMessagesResponse>(
      `/messages/threads/${otherUserId}?${params.toString()}`
    );
  },

  // Send a message to another user
  sendMessage: (data: SendMessageInput) =>
    api.post<Message>('/messages', data),

  // Mark a single message as read
  markAsRead: (messageId: number) =>
    api.patch<{ message: string; read_at: string }>(`/messages/${messageId}/read`, {}),

  // Mark all messages in a thread as read
  markThreadAsRead: (otherUserId: number, bookingId?: number) => {
    const params = bookingId ? `?booking_id=${bookingId}` : '';
    return api.patch<{ message: string; count: number }>(
      `/messages/threads/${otherUserId}/read-all${params}`,
      {}
    );
  },

  // Get unread message count
  getUnreadCount: () =>
    api.get<UnreadCountResponse>('/messages/unread/count'),

  // Search messages
  searchMessages: (query: string, page = 1, pageSize = 20) =>
    api.get<{
      messages: Message[];
      total: number;
      page: number;
      page_size: number;
      total_pages: number;
    }>(`/messages/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`),

  // Edit a message (within 15 minutes)
  editMessage: (messageId: number, message: string) =>
    api.patch<Message>(`/messages/${messageId}`, { message }),

  // Delete a message
  deleteMessage: (messageId: number) =>
    api.delete<void>(`/messages/${messageId}`),

  // Get user info for messaging
  getUserInfo: (userId: number) =>
    api.get<{
      id: number;
      email: string;
      first_name?: string;
      last_name?: string;
      avatar_url?: string;
      role: string;
    }>(`/messages/users/${userId}`),

  // Legacy aliases for backward compatibility
  getConversations: () => messagesApi.getThreads(),
  getMessages: (conversationId: number, page = 1) =>
    messagesApi.getConversation(conversationId, page),
  startConversation: (userId: number, message: string) =>
    messagesApi.sendMessage({ recipient_id: userId, message }),
};
