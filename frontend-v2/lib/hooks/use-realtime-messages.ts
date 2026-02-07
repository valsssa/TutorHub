'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './use-websocket';
import { messageKeys } from './use-messages';
import type {
  ServerMessage,
  NewMessageMessage,
  TypingIndicatorMessage,
  PresenceStatusMessage,
  MessageReadAckMessage,
} from '@/types/websocket';
import type { Message } from '@/types';

interface TypingState {
  [userId: number]: boolean;
}

interface PresenceState {
  [userId: number]: 'online' | 'offline';
}

interface UseRealtimeMessagesOptions {
  /** Current conversation ID (for filtering relevant messages) */
  conversationId?: number;
  /** User ID of the other participant (for typing/presence) */
  otherUserId?: number;
  /** Callback when new message arrives */
  onNewMessage?: (message: NewMessageMessage) => void;
  /** Auto-connect (default: true when conversationId is provided) */
  enabled?: boolean;
}

interface UseRealtimeMessagesReturn {
  /** WebSocket connection state */
  isConnected: boolean;
  /** Whether currently reconnecting */
  isReconnecting: boolean;
  /** Typing state for users */
  typingUsers: TypingState;
  /** Presence state for users */
  presenceState: PresenceState;
  /** Send typing indicator */
  sendTyping: (isTyping: boolean) => void;
  /** Mark message as read via WebSocket */
  markAsRead: (messageId: number) => void;
  /** Check if a user is online */
  isUserOnline: (userId: number) => boolean;
  /** Check if user is typing */
  isUserTyping: (userId: number) => boolean;
  /** Connection error message */
  error: string | null;
  /** Manually reconnect */
  reconnect: () => void;
}

/**
 * Real-time messaging hook that integrates WebSocket with React Query
 *
 * Features:
 * - Automatic cache updates on new messages
 * - Typing indicators
 * - Presence (online/offline) tracking
 * - Read receipts
 *
 * @example
 * ```tsx
 * const { isConnected, typingUsers, sendTyping } = useRealtimeMessages({
 *   conversationId: 123,
 *   otherUserId: 456,
 *   onNewMessage: (msg) => scrollToBottom(),
 * });
 * ```
 */
export function useRealtimeMessages(
  options: UseRealtimeMessagesOptions = {}
): UseRealtimeMessagesReturn {
  const { conversationId, otherUserId, onNewMessage, enabled = true } = options;

  const queryClient = useQueryClient();
  const [typingUsers, setTypingUsers] = useState<TypingState>({});
  const [presenceState, setPresenceState] = useState<PresenceState>({});
  const typingTimeoutRef = useRef<Map<number, NodeJS.Timeout>>(new Map());
  const checkPresenceRef = useRef<(userIds: number[]) => void>(() => {});

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (message: ServerMessage) => {
      switch (message.type) {
        case 'new_message': {
          const newMsg = message as NewMessageMessage;

          // Update messages cache
          if (conversationId) {
            queryClient.setQueryData(
              [...messageKeys.messages(conversationId), 1],
              (old: { messages: Message[] } | undefined) => {
                if (!old) return old;
                // Add message if not already present
                const exists = old.messages.some((m) => m.id === newMsg.message_id);
                if (exists) return old;

                return {
                  ...old,
                  messages: [
                    {
                      id: newMsg.message_id,
                      sender_id: newMsg.sender_id,
                      recipient_id: newMsg.recipient_id,
                      message: newMsg.content,
                      booking_id: newMsg.booking_id,
                      conversation_id: newMsg.conversation_id,
                      is_read: false,
                      created_at: newMsg.created_at,
                    } as Message,
                    ...old.messages,
                  ],
                };
              }
            );
          }

          // Update conversations list
          queryClient.invalidateQueries({ queryKey: messageKeys.conversations() });

          // Update unread count
          queryClient.invalidateQueries({ queryKey: messageKeys.unreadCount() });

          // Clear typing indicator for sender
          setTypingUsers((prev) => ({ ...prev, [newMsg.sender_id]: false }));

          // Callback
          onNewMessage?.(newMsg);
          break;
        }

        case 'message_sent': {
          // Confirm our message was sent - refresh messages
          if (conversationId) {
            queryClient.invalidateQueries({
              queryKey: messageKeys.messages(conversationId),
            });
          }
          break;
        }

        case 'message_read': {
          const readMsg = message as MessageReadAckMessage;

          // Update message read status in cache
          if (conversationId) {
            queryClient.setQueryData(
              [...messageKeys.messages(conversationId), 1],
              (old: { messages: Message[] } | undefined) => {
                if (!old) return old;
                return {
                  ...old,
                  messages: old.messages.map((m) =>
                    m.id === readMsg.message_id
                      ? { ...m, is_read: true, read_at: readMsg.read_at }
                      : m
                  ),
                };
              }
            );
          }
          break;
        }

        case 'typing': {
          const typingMsg = message as TypingIndicatorMessage;

          // Clear existing timeout for this user
          const existingTimeout = typingTimeoutRef.current.get(typingMsg.user_id);
          if (existingTimeout) {
            clearTimeout(existingTimeout);
          }

          if (typingMsg.is_typing) {
            // Set typing state
            setTypingUsers((prev) => ({ ...prev, [typingMsg.user_id]: true }));

            // Auto-clear after 5 seconds
            const timeout = setTimeout(() => {
              setTypingUsers((prev) => ({ ...prev, [typingMsg.user_id]: false }));
              typingTimeoutRef.current.delete(typingMsg.user_id);
            }, 5000);

            typingTimeoutRef.current.set(typingMsg.user_id, timeout);
          } else {
            // Clear typing state
            setTypingUsers((prev) => ({ ...prev, [typingMsg.user_id]: false }));
            typingTimeoutRef.current.delete(typingMsg.user_id);
          }
          break;
        }

        case 'presence_status': {
          const presenceMsg = message as PresenceStatusMessage;
          setPresenceState((prev) => ({
            ...prev,
            ...presenceMsg.user_statuses,
          }));
          break;
        }

        case 'connection': {
          // On connect, check presence of other user
          if (otherUserId) {
            checkPresenceRef.current([otherUserId]);
          }
          break;
        }
      }
    },
    [conversationId, otherUserId, queryClient, onNewMessage]
  );

  // Initialize WebSocket
  const {
    state,
    isConnected,
    sendTyping: wsSendTyping,
    sendMessageRead,
    checkPresence,
    connect,
    lastError,
  } = useWebSocket({
    autoConnect: enabled,
    onMessage: handleMessage,
    onConnect: () => {
      // Check presence when connected - use ref to avoid circular dependency
      if (otherUserId) {
        setTimeout(() => checkPresenceRef.current([otherUserId]), 100);
      }
    },
  });

  // Keep checkPresenceRef in sync with checkPresence
  useEffect(() => {
    checkPresenceRef.current = checkPresence;
  }, [checkPresence]);

  // Send typing indicator (debounced at component level typically)
  const sendTyping = useCallback(
    (isTyping: boolean) => {
      if (otherUserId) {
        wsSendTyping(otherUserId, isTyping);
      }
    },
    [otherUserId, wsSendTyping]
  );

  // Mark message as read
  const markAsRead = useCallback(
    (messageId: number) => {
      sendMessageRead(messageId);
    },
    [sendMessageRead]
  );

  // Check if user is online
  const isUserOnline = useCallback(
    (userId: number) => presenceState[userId] === 'online',
    [presenceState]
  );

  // Check if user is typing
  const isUserTyping = useCallback(
    (userId: number) => typingUsers[userId] === true,
    [typingUsers]
  );

  // Cleanup typing timeouts on unmount
  useEffect(() => {
    const timeoutMap = typingTimeoutRef.current;
    return () => {
      timeoutMap.forEach((timeout) => clearTimeout(timeout));
      timeoutMap.clear();
    };
  }, []);

  // Check presence when otherUserId changes
  useEffect(() => {
    if (isConnected && otherUserId) {
      checkPresence([otherUserId]);
    }
  }, [isConnected, otherUserId, checkPresence]);

  return {
    isConnected,
    isReconnecting: state === 'reconnecting',
    typingUsers,
    presenceState,
    sendTyping,
    markAsRead,
    isUserOnline,
    isUserTyping,
    error: lastError,
    reconnect: connect,
  };
}

/**
 * Hook for typing indicator with debounce
 * Use this to prevent flooding the server with typing events
 */
export function useTypingIndicator(
  sendTyping: (isTyping: boolean) => void,
  debounceMs = 300
) {
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isTypingRef = useRef(false);

  const startTyping = useCallback(() => {
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      sendTyping(true);
    }

    // Reset the stop-typing timer
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      isTypingRef.current = false;
      sendTyping(false);
    }, debounceMs + 2000); // Stop typing after 2s of no input
  }, [sendTyping, debounceMs]);

  const stopTyping = useCallback(() => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    if (isTypingRef.current) {
      isTypingRef.current = false;
      sendTyping(false);
    }
  }, [sendTyping]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  return { startTyping, stopTyping };
}
