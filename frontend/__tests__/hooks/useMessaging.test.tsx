/**
 * Tests for useMessaging hook
 * Critical: Messaging is a core feature for student-tutor communication
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { useMessaging, Message } from "@/hooks/useMessaging";

// Mock the useWebSocket hook
const mockSendMessage = jest.fn();
const mockSendTyping = jest.fn();
const mockSendMessageDelivered = jest.fn();
const mockSendMessageRead = jest.fn();

let mockLastMessage: any = null;
let mockIsConnected = true;

jest.mock("@/hooks/useWebSocket", () => ({
  useWebSocket: () => ({
    isConnected: mockIsConnected,
    lastMessage: mockLastMessage,
    sendMessage: mockSendMessage,
    sendTyping: mockSendTyping,
    sendMessageDelivered: mockSendMessageDelivered,
    sendMessageRead: mockSendMessageRead,
  }),
}));

describe("useMessaging", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockLastMessage = null;
    mockIsConnected = true;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("initialization", () => {
    it("initializes with empty messages array", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      expect(result.current.messages).toEqual([]);
      expect(result.current.typingUsers.size).toBe(0);
    });

    it("exposes isConnected from websocket", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      expect(result.current.isConnected).toBe(true);
    });

    it("handles disconnected state", () => {
      mockIsConnected = false;

      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      expect(result.current.isConnected).toBe(false);
    });
  });

  describe("new message handling", () => {
    it("adds new message to messages array when for current thread", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Simulate receiving a new message
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Hello there",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      rerender();

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0]).toMatchObject({
        id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Hello there",
        delivery_state: "sent",
      });
    });

    it("sends delivery acknowledgment when receiving message as recipient", () => {
      const { rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Test message",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      rerender();

      expect(mockSendMessageDelivered).toHaveBeenCalledWith(100, 2);
    });

    it("does not add duplicate messages", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Hello",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      rerender();
      rerender(); // Trigger again with same message

      expect(result.current.messages).toHaveLength(1);
    });

    it("ignores messages not for current thread", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 5, // Different thread
        recipient_id: 1,
        message: "Wrong thread",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      rerender();

      expect(result.current.messages).toHaveLength(0);
    });

    it("adds sent messages from current user to selected thread", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 101,
        sender_id: 1, // Current user
        recipient_id: 2, // Selected thread
        message: "My sent message",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      rerender();

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.messages[0].sender_id).toBe(1);
    });
  });

  describe("message sent confirmation", () => {
    it("updates message delivery state to sent on confirmation", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // First, add a message
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Then receive message_sent confirmation
      mockLastMessage = {
        type: "message_sent",
        message_id: 100,
      };
      rerender();

      expect(result.current.messages[0].delivery_state).toBe("sent");
    });
  });

  describe("delivery receipt handling", () => {
    it("updates message delivery state to delivered on receipt", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add a message first
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 1,
        recipient_id: 2,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Then receive delivery receipt
      mockLastMessage = {
        type: "delivery_receipt",
        message_id: 100,
      };
      rerender();

      expect(result.current.messages[0].delivery_state).toBe("delivered");
    });
  });

  describe("message read handling", () => {
    it("updates message to read status", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add a message first
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 1,
        recipient_id: 2,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Then receive read confirmation
      mockLastMessage = {
        type: "message_read",
        message_id: 100,
        read_at: "2025-01-25T10:05:00Z",
      };
      rerender();

      expect(result.current.messages[0].is_read).toBe(true);
      expect(result.current.messages[0].read_at).toBe("2025-01-25T10:05:00Z");
      expect(result.current.messages[0].delivery_state).toBe("read");
    });

    it("does not update already read messages", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add an already-read message
      act(() => {
        result.current.setMessages([
          {
            id: 100,
            sender_id: 1,
            recipient_id: 2,
            message: "Test",
            created_at: "2025-01-25T10:00:00Z",
            is_read: true,
            read_at: "2025-01-25T10:01:00Z",
            delivery_state: "read",
          },
        ]);
      });

      // Try to mark it read again
      mockLastMessage = {
        type: "message_read",
        message_id: 100,
        read_at: "2025-01-25T10:10:00Z",
      };
      rerender();

      // Original read_at should be preserved
      expect(result.current.messages[0].read_at).toBe("2025-01-25T10:01:00Z");
    });
  });

  describe("message edited handling", () => {
    it("updates message content when edited", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add a message first
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Original",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Then receive edit notification
      mockLastMessage = {
        type: "message_edited",
        message_id: 100,
        new_content: "Edited content",
        edited_at: "2025-01-25T10:05:00Z",
      };
      rerender();

      expect(result.current.messages[0].message).toBe("Edited content");
      expect(result.current.messages[0].is_edited).toBe(true);
      expect(result.current.messages[0].edited_at).toBe("2025-01-25T10:05:00Z");
    });
  });

  describe("message deleted handling", () => {
    it("removes message from array when deleted", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add a message first
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "To delete",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      expect(result.current.messages).toHaveLength(1);

      // Then receive delete notification
      mockLastMessage = {
        type: "message_deleted",
        message_id: 100,
      };
      rerender();

      expect(result.current.messages).toHaveLength(0);
    });
  });

  describe("typing indicator handling", () => {
    it("adds user to typing set when typing event received", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      expect(result.current.typingUsers.has(2)).toBe(true);
    });

    it("clears typing indicator after timeout", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      expect(result.current.typingUsers.has(2)).toBe(true);

      // Advance time by 3 seconds
      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(result.current.typingUsers.has(2)).toBe(false);
    });

    it("ignores typing from users not in current thread", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "typing",
        user_id: 5, // Different user
      };
      rerender();

      expect(result.current.typingUsers.has(5)).toBe(false);
    });

    it("resets typing timeout on repeated typing events", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      // Advance time by 2 seconds
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      // Another typing event
      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      // Advance time by 2 more seconds (4 total from first, 2 from second)
      act(() => {
        jest.advanceTimersByTime(2000);
      });

      // Should still be typing since timeout restarted
      expect(result.current.typingUsers.has(2)).toBe(true);

      // Advance to clear
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.typingUsers.has(2)).toBe(false);
    });
  });

  describe("send typing indicator", () => {
    it("sends typing indicator via websocket", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      act(() => {
        result.current.handleTyping();
      });

      expect(mockSendTyping).toHaveBeenCalledWith(2);
    });

    it("does not send typing when no thread selected", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: undefined })
      );

      act(() => {
        result.current.handleTyping();
      });

      expect(mockSendTyping).not.toHaveBeenCalled();
    });
  });

  describe("setMessages", () => {
    it("sets messages directly with array", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      const newMessages: Message[] = [
        {
          id: 1,
          sender_id: 2,
          recipient_id: 1,
          message: "First",
          created_at: "2025-01-25T10:00:00Z",
          is_read: false,
        },
        {
          id: 2,
          sender_id: 1,
          recipient_id: 2,
          message: "Second",
          created_at: "2025-01-25T10:01:00Z",
          is_read: false,
        },
      ];

      act(() => {
        result.current.setMessages(newMessages);
      });

      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].message).toBe("First");
    });

    it("sets messages with updater function", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      const initialMessage: Message = {
        id: 1,
        sender_id: 2,
        recipient_id: 1,
        message: "Initial",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };

      act(() => {
        result.current.setMessages([initialMessage]);
      });

      act(() => {
        result.current.setMessages((prev) => [
          ...prev,
          {
            id: 2,
            sender_id: 1,
            recipient_id: 2,
            message: "Added",
            created_at: "2025-01-25T10:01:00Z",
            is_read: false,
          },
        ]);
      });

      expect(result.current.messages).toHaveLength(2);
    });

    it("sends read receipts for unread messages from other user", () => {
      const { result } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      const messagesWithUnread: Message[] = [
        {
          id: 100,
          sender_id: 2, // From selected thread
          recipient_id: 1, // To current user
          message: "Unread message",
          created_at: "2025-01-25T10:00:00Z",
          is_read: false,
        },
      ];

      act(() => {
        result.current.setMessages(messagesWithUnread);
      });

      expect(mockSendMessageRead).toHaveBeenCalledWith(100, 2);
    });
  });

  describe("clearMessages", () => {
    it("clears all messages and typing users", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add a message
      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Add typing user
      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      expect(result.current.messages).toHaveLength(1);
      expect(result.current.typingUsers.size).toBe(1);

      act(() => {
        result.current.clearMessages();
      });

      expect(result.current.messages).toHaveLength(0);
      expect(result.current.typingUsers.size).toBe(0);
    });
  });

  describe("thread read handling", () => {
    it("handles thread_read event", () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      const { rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "thread_read",
        reader_id: 2,
        message_count: 5,
      };
      rerender();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Thread read by user 2")
      );

      consoleSpy.mockRestore();
    });
  });

  describe("cleanup", () => {
    it("clears typing timeouts on unmount", () => {
      const { rerender, unmount } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      // Add typing event
      mockLastMessage = {
        type: "typing",
        user_id: 2,
      };
      rerender();

      // Unmount should clear the timeout
      unmount();

      // Advance timers - should not throw
      act(() => {
        jest.advanceTimersByTime(5000);
      });
    });
  });

  describe("edge cases", () => {
    it("handles null currentUserId", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: null, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Should not add message when currentUserId is null
      expect(result.current.messages).toHaveLength(0);
    });

    it("handles undefined selectedThreadId", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: undefined })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        message: "Test",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      // Should not add message when no thread selected
      expect(result.current.messages).toHaveLength(0);
    });

    it("handles message with booking_id", () => {
      const { result, rerender } = renderHook(() =>
        useMessaging({ currentUserId: 1, selectedThreadId: 2 })
      );

      mockLastMessage = {
        type: "new_message",
        message_id: 100,
        sender_id: 2,
        recipient_id: 1,
        booking_id: 50,
        message: "About our booking",
        created_at: "2025-01-25T10:00:00Z",
        is_read: false,
      };
      rerender();

      expect(result.current.messages[0].booking_id).toBe(50);
    });
  });
});
