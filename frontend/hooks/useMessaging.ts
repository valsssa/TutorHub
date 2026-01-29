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
  otherUserId: number;
  otherUserEmail: string;
  otherUserRole?: string;
  bookingId?: number;
  lastMessage: string;
  lastMessageTime: string;
  lastSenderId?: number;
  totalMessages?: number;
  unreadCount: number;
}

// WebSocket message payload types (matching backend)
interface NewMessagePayload extends WebSocketMessage {
  type: "new_message";
  message_id: number;
  sender_id: number;
  sender_email: string;
  recipient_id: number;
  booking_id: number | null;
  message: string;
  created_at: string;
  is_read: boolean;
}

interface MessageSentPayload extends WebSocketMessage {
  type: "message_sent";
  message_id: number;
  recipient_id: number;
}

interface DeliveryReceiptPayload extends WebSocketMessage {
  type: "delivery_receipt";
  message_id: number;
  recipient_id: number;
  state: "delivered" | "read";
}

interface MessageReadPayload extends WebSocketMessage {
  type: "message_read";
  message_id: number;
  reader_id: number;
  read_at?: string;
}

interface MessageEditedPayload extends WebSocketMessage {
  type: "message_edited";
  message_id: number;
  new_content: string;
  edited_at: string;
}

interface MessageDeletedPayload extends WebSocketMessage {
  type: "message_deleted";
  message_id: number;
  deleted_by: number;
}

interface TypingPayload extends WebSocketMessage {
  type: "typing";
  user_id: number;
  user_email: string;
}

interface ThreadReadPayload extends WebSocketMessage {
  type: "thread_read";
  reader_id: number;
  message_count: number;
}

interface UseMessagingProps {
  currentUserId: number | null;
  selectedThreadId?: number;
}

export function useMessaging({ currentUserId, selectedThreadId }: UseMessagingProps) {
  const {
    isConnected,
    lastMessage,
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
          handleNewMessage(lastMessage as NewMessagePayload);
          break;
        case "message_sent":
          handleMessageSent(lastMessage as MessageSentPayload);
          break;
        case "delivery_receipt":
          handleDeliveryReceipt(lastMessage as DeliveryReceiptPayload);
          break;
        case "message_read":
          handleMessageRead(lastMessage as MessageReadPayload);
          break;
        case "message_edited":
          handleMessageEdited(lastMessage as MessageEditedPayload);
          break;
        case "message_deleted":
          handleMessageDeleted(lastMessage as MessageDeletedPayload);
          break;
        case "typing":
          handleTyping(lastMessage as TypingPayload);
          break;
        case "thread_read":
          handleThreadRead(lastMessage as ThreadReadPayload);
          break;
      }
    };

    handleMessage();
  }, [lastMessage, currentUserId, selectedThreadId]);

  // Handler functions
  const handleNewMessage = (msg: NewMessagePayload) => {
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
        booking_id: msg.booking_id ?? undefined,
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

  const handleMessageSent = (msg: MessageSentPayload) => {
    if (msg.message_id && selectedThreadId) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msg.message_id ? { ...m, delivery_state: "sent" as const } : m
        )
      );
    }
  };

  const handleDeliveryReceipt = (msg: DeliveryReceiptPayload) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.message_id ? { ...m, delivery_state: "delivered" as const } : m
      )
    );
  };

  const handleMessageRead = (msg: MessageReadPayload) => {
    // Update message read status in real-time
    // This updates check marks from 1 to 2 when recipient reads the message
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msg.message_id && !m.is_read
          ? { ...m, is_read: true, read_at: msg.read_at, delivery_state: "read" as const }
          : m
      )
    );
  };

  const handleMessageEdited = (msg: MessageEditedPayload) => {
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

  const handleMessageDeleted = (msg: MessageDeletedPayload) => {
    setMessages((prev) => prev.filter((m) => m.id !== msg.message_id));
  };

  const handleTyping = (msg: TypingPayload) => {
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

  const handleThreadRead = (msg: ThreadReadPayload) => {
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
      const processSendReadReceipts = (messageList: Message[]) => {
        if (currentUserId && selectedThreadId && sendMessageRead) {
          messageList.forEach((msg) => {
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
