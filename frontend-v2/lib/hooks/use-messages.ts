import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi } from '@/lib/api';
import type { SendMessageInput } from '@/types';

export const messageKeys = {
  all: ['messages'] as const,
  conversations: () => [...messageKeys.all, 'conversations'] as const,
  conversation: (id: number) => [...messageKeys.all, 'conversation', id] as const,
  messages: (conversationId: number) =>
    [...messageKeys.all, 'messages', conversationId] as const,
  unreadCount: () => [...messageKeys.all, 'unread-count'] as const,
};

export function useConversations() {
  return useQuery({
    queryKey: messageKeys.conversations(),
    queryFn: messagesApi.getConversations,
  });
}

export function useConversation(id: number) {
  return useQuery({
    queryKey: messageKeys.conversation(id),
    queryFn: () => messagesApi.getConversation(id),
    enabled: !!id,
  });
}

export function useMessages(conversationId: number, page = 1) {
  return useQuery({
    queryKey: [...messageKeys.messages(conversationId), page],
    queryFn: () => messagesApi.getMessages(conversationId, page),
    enabled: !!conversationId,
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: messageKeys.unreadCount(),
    queryFn: messagesApi.getUnreadCount,
    refetchInterval: 30 * 1000,
  });
}

export function useSendMessage(conversationId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SendMessageInput) =>
      messagesApi.sendMessage({ ...data, recipient_id: data.recipient_id ?? conversationId }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: messageKeys.messages(conversationId)
      });
      queryClient.invalidateQueries({
        queryKey: messageKeys.conversations()
      });
    },
  });
}

export function useStartConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, message }: { userId: number; message: string }) =>
      messagesApi.startConversation(userId, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: messageKeys.conversations() });
    },
  });
}

export function useMarkAsRead(conversationId: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => messagesApi.markThreadAsRead(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: messageKeys.unreadCount() });
      queryClient.invalidateQueries({
        queryKey: messageKeys.conversation(conversationId)
      });
    },
  });
}
