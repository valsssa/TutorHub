/**
 * React Messaging Hook - Production-Ready
 * Clean state management for message threads with real-time updates.
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { useWebSocket, WebSocketMessage } from "./useWebSocket";

export interface Message {
  id: number;
  sender_id: number;
  recipient_id: number;
  booking_id?: number;
  message: string;
  created_at: string;
  is_read: boolean;
  read_at?: string;
  is_edited?: boolean;
  edited_at?: string;
  delivery_state?: "sent" | "delivered" | "read";
}

export interface MessageThread {
  other_user_id: number;
  other_user_email: string;
  other_user_role?: string;
  booking_id?: number;
  last_message: string;
  last_message_time: string;
  last_sender_id?: number;
  total_messages?: number;
  unread_count: number;
}

interface UseMessagingProps {
  currentUserId: number | null;
  selectedThreadId?: number;
}

export function useMessaging({ currentUserId, selectedThreadId }: UseMessagingProps) {
  const {
    isConnected,
    lastMessage,
    sendMessage: wsSendMessage,
    sendTyping: wsSendTyping,
    sendMessageDelivered,
    sendMessageRead,
  } = useWebSocket();

  const [messages, setMessages] = useState<Message[]>([]);
  const [typingUsers, setTypingUsers] = useState<Set<number>>(new Set());
  const typingTimeoutRef = useRef<Map<number, NodeJS.Timeout>>(new Map());

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage || !currentUserId) return;

    const handleMessage = () => {
      switch (lastMessage.type) {
        case "new_message":
          handleNewMessage(lastMessage);
          break;
        case "message_sent":
          handleMessageSent(lastMessage);
          break;
        case "delivery_receipt":
          handleDeliveryReceipt(lastMessage);
          break;
        case "message_read":
          handleMessageRead(lastMessage);
          break;
        case "message_edited":
          handleMessageEdited(lastMessage);
          break;
        case "message_deleted":
          handleMessageDeleted(lastMessage);
          break;
        case "typing":
          handleTyping(lastMessage);
          break;
        case "thread_read":
          handleThreadRead(lastMessage);
          break;
      }
    };

    handleMessage();
  }, [lastMessage, currentUserId, selectedThreadId]);

  // Handler functions
  const handleNewMessage = (msg: WebSocketMessage) => {
    // Only add message if it's for the current thread
    if (
      selectedThreadId &&
      ((msg.sender_id === selectedThreadId && msg.recipient_id === currentUserId) ||
        (msg.sender_id === currentUserId && msg.recipient_id === selectedThreadId))
    ) {
      const newMsg: Message = {
        id: msg.message_id,
        sender_id: msg.sender_id,
        recipient_id: msg.recipient_id,
        booking_id: msg.booking_id,
        message: msg.message,
        created_at: msg.created_at,
        is_read: msg.is_read || false,
        delivery_state: "sent",
      };

      setMessages((prev) => {
        // Avoid duplicates
        if (prev.some((m) => m.id === newMsg.id)) {
          return prev;
        }
        return [...prev, newMsg];
      });

      // Send delivery acknowledgment if we're the recipient
      if (msg.recipient_id === currentUserId && sendMessageDelivered) {
        sendMessageDelivered(msg.message_id, msg.sender_id);
      }
    }
  };

  const handleMessageSent = (msg: WebSocketMessage) => {
    if (msg.message_id && selectedThreadId) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msg.message_id ? { ...m, delivery_state: "sent" } : m
        )
      );
    }
  };

  const handleDeliveryReceipt = (msg: WebSocketMessage) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.message_id ? { ...m, delivery_state: "delivered" } : m
      )
    );
  };

  const handleMessageRead = (msg: WebSocketMessage) => {
    // Update message read status in real-time
    // This updates check marks from 1 to 2 when recipient reads the message
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.message_id && !m.is_read
          ? { ...m, is_read: true, read_at: msg.read_at, delivery_state: "read" }
          : m
      )
    );
  };

  const handleMessageEdited = (msg: WebSocketMessage) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.message_id
          ? {
              ...m,
              message: msg.new_content,
              is_edited: true,
              edited_at: msg.edited_at,
            }
          : m
      )
    );
  };

  const handleMessageDeleted = (msg: WebSocketMessage) => {
    setMessages((prev) => prev.filter((m) => m.id !== msg.message_id));
  };

  const handleTyping = (msg: WebSocketMessage) => {
    if (selectedThreadId && msg.user_id === selectedThreadId) {
      setTypingUsers((prev) => new Set(prev).add(msg.user_id));

      // Clear existing timeout
      const existingTimeout = typingTimeoutRef.current.get(msg.user_id);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // Set new timeout to clear typing indicator after 3 seconds
      const timeout = setTimeout(() => {
        setTypingUsers((prev) => {
          const newSet = new Set(prev);
          newSet.delete(msg.user_id);
          return newSet;
        });
        typingTimeoutRef.current.delete(msg.user_id);
      }, 3000);

      typingTimeoutRef.current.set(msg.user_id, timeout);
    }
  };

  const handleThreadRead = (msg: WebSocketMessage) => {
    // Could update UI to show messages were read
    console.log(`Thread read by user ${msg.reader_id}: ${msg.message_count} messages`);
  };

  // Cleanup typing timeouts on unmount
  useEffect(() => {
    return () => {
      typingTimeoutRef.current.forEach((timeout) => clearTimeout(timeout));
      typingTimeoutRef.current.clear();
    };
  }, []);

  // Send read receipts when viewing messages
  const setMessageList = useCallback(
    (newMessagesOrUpdater: Message[] | ((prev: Message[]) => Message[])) => {
      const processSendReadReceipts = (messages: Message[]) => {
        if (currentUserId && selectedThreadId && sendMessageRead) {
          messages.forEach((msg) => {
            if (
              msg.sender_id === selectedThreadId &&
              msg.recipient_id === currentUserId &&
              !msg.is_read &&
              msg.delivery_state !== "read"
            ) {
              sendMessageRead(msg.id, msg.sender_id);
            }
          });
        }
      };

      if (typeof newMessagesOrUpdater === "function") {
        setMessages((prev) => {
          const newMessages = newMessagesOrUpdater(prev);
          processSendReadReceipts(newMessages);
          return newMessages;
        });
      } else {
        setMessages(newMessagesOrUpdater);
        processSendReadReceipts(newMessagesOrUpdater);
      }
    },
    [currentUserId, selectedThreadId, sendMessageRead]
  );

  const sendTypingIndicator = useCallback(() => {
    if (selectedThreadId && wsSendTyping) {
      wsSendTyping(selectedThreadId);
    }
  }, [selectedThreadId, wsSendTyping]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setTypingUsers(new Set());
  }, []);

  return {
    messages,
    setMessages: setMessageList,
    clearMessages,
    typingUsers,
    isConnected,
    handleTyping: sendTypingIndicator,
  };
}
