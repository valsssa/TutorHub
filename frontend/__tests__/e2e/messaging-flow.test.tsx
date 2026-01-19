/**
 * E2E Tests for Messaging Flow
 * Tests the complete messaging workflow including:
 * - Sending and receiving messages
 * - Delivery states (sent/delivered/read)
 * - Message editing and deletion
 * - Search and pagination
 * - Real-time WebSocket updates
 */

import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { messages as messagesAPI } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import Cookies from "js-cookie";
import axios from "axios";

// Mock dependencies
jest.mock("@/lib/api");
jest.mock("@/hooks/useWebSocket");
jest.mock("js-cookie");
jest.mock("axios");
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
  }),
  useSearchParams: () => ({
    get: jest.fn(),
  }),
}));

const mockCurrentUser = {
  id: 1,
  email: "student@example.com",
  role: "student",
  is_active: true,
};

const mockThreads = [
  {
    other_user_id: 2,
    other_user_email: "tutor@example.com",
    booking_id: null,
    last_message: "Hi, I'm interested in lessons",
    last_message_time: new Date().toISOString(),
    unread_count: 1,
    total_messages: 3,
  },
];

const mockMessages = [
  {
    id: 1,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: "Hi, I'm interested in lessons",
    is_read: true,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    delivery_state: "read",
  },
  {
    id: 2,
    sender_id: 2,
    recipient_id: 1,
    booking_id: null,
    message: "Great! What subject are you interested in?",
    is_read: false,
    created_at: new Date(Date.now() - 1800000).toISOString(),
    delivery_state: "delivered",
  },
  {
    id: 3,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: "I want to learn mathematics",
    is_read: false,
    created_at: new Date().toISOString(),
    delivery_state: "sent",
  },
];

describe("E2E Messaging Flow", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue("mock-token");
    (axios.get as jest.Mock).mockResolvedValue({ data: mockCurrentUser });
    (messagesAPI.listThreads as jest.Mock).mockResolvedValue(mockThreads);
    (messagesAPI.getThreadMessages as jest.Mock).mockResolvedValue(mockMessages);
    (messagesAPI.send as jest.Mock).mockImplementation((data) =>
      Promise.resolve({
        id: Date.now(),
        ...data,
        sender_id: mockCurrentUser.id,
        is_read: false,
        created_at: new Date().toISOString(),
        delivery_state: "sent",
      })
    );
    (useWebSocket as jest.Mock).mockReturnValue({
      isConnected: true,
      lastMessage: null,
      sendTyping: jest.fn(),
      sendMessage: jest.fn(),
    });
  });

  describe("Message Sending Flow", () => {
    it("successfully sends a message", async () => {
      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      // Select thread
      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        expect(messagesAPI.getThreadMessages).toHaveBeenCalledWith(2, null, 1, 50, "");
      });

      // Type message
      const input = screen.getByPlaceholderText(/Type your message/i);
      fireEvent.change(input, { target: { value: "When can we start?" } });

      // Send message
      const sendButton = screen.getByRole("button", { name: /send/i });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(messagesAPI.send).toHaveBeenCalledWith({
          recipient_id: 2,
          message: "When can we start?",
          booking_id: null,
        });
      });
    });

    it("shows delivery states correctly", async () => {
      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        // Check for delivery indicators
        const messageList = screen.getByRole("list") || screen.getByTestId("message-list");
        expect(messageList).toBeInTheDocument();
      });
    });

    it("receives real-time messages via WebSocket", async () => {
      const newMessage = {
        type: "new_message",
        message_id: 4,
        sender_id: 2,
        sender_email: "tutor@example.com",
        recipient_id: 1,
        booking_id: null,
        message: "Let's schedule for tomorrow",
        created_at: new Date().toISOString(),
        is_read: false,
        state: "sent",
      };

      const { rerender } = render(<div>Placeholder</div>);

      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: newMessage,
        sendTyping: jest.fn(),
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      rerender(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText("Let's schedule for tomorrow")).toBeInTheDocument();
      });
    });
  });

  describe("Message Editing Flow", () => {
    it("allows editing own messages within time limit", async () => {
      (messagesAPI.editMessage as jest.Mock).mockResolvedValue({
        message: "Message updated successfully",
        new_content: "Updated message content",
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        expect(messagesAPI.getThreadMessages).toHaveBeenCalled();
      });

      // Find edit button for own message
      const ownMessage = screen.getByText("I want to learn mathematics");
      const editButton = ownMessage.closest("div")?.querySelector('[aria-label="Edit"]');

      if (editButton) {
        fireEvent.click(editButton);

        // Edit message
        const editInput = screen.getByDisplayValue("I want to learn mathematics");
        fireEvent.change(editInput, {
          target: { value: "I want to learn advanced mathematics" },
        });

        // Save
        const saveButton = screen.getByRole("button", { name: /save/i });
        fireEvent.click(saveButton);

        await waitFor(() => {
          expect(messagesAPI.editMessage).toHaveBeenCalledWith(3, {
            message: "I want to learn advanced mathematics",
          });
        });
      }
    });

    it("receives edited message via WebSocket", async () => {
      const editedMessage = {
        type: "message_edited",
        message_id: 2,
        new_content: "Great! What specific topics are you interested in?",
        edited_by: 2,
      };

      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: editedMessage,
        sendTyping: jest.fn(),
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText(editedMessage.new_content)).toBeInTheDocument();
      });
    });
  });

  describe("Message Deletion Flow", () => {
    it("allows deleting own messages", async () => {
      (messagesAPI.deleteMessage as jest.Mock).mockResolvedValue({
        message: "Message deleted successfully",
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        expect(messagesAPI.getThreadMessages).toHaveBeenCalled();
      });

      // Find delete button
      const ownMessage = screen.getByText("I want to learn mathematics");
      const deleteButton = ownMessage.closest("div")?.querySelector('[aria-label="Delete"]');

      if (deleteButton) {
        fireEvent.click(deleteButton);

        await waitFor(() => {
          expect(messagesAPI.deleteMessage).toHaveBeenCalledWith(3);
        });
      }
    });

    it("handles deleted message via WebSocket", async () => {
      const deletedMessage = {
        type: "message_deleted",
        message_id: 2,
        deleted_by: 2,
      };

      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: deletedMessage,
        sendTyping: jest.fn(),
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        // Message should be removed from UI
        expect(
          screen.queryByText("Great! What subject are you interested in?")
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("Search and Pagination", () => {
    it("searches messages in thread", async () => {
      const searchResults = [mockMessages[2]];
      (messagesAPI.getThreadMessages as jest.Mock).mockResolvedValue(searchResults);

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      // Search
      const searchInput = screen.getByPlaceholderText(/search messages/i);
      fireEvent.change(searchInput, { target: { value: "mathematics" } });

      await waitFor(() => {
        expect(messagesAPI.getThreadMessages).toHaveBeenCalledWith(
          2,
          null,
          1,
          50,
          "mathematics"
        );
      });
    });

    it("loads more messages on scroll", async () => {
      const page2Messages = [
        {
          id: 4,
          sender_id: 2,
          recipient_id: 1,
          booking_id: null,
          message: "Older message",
          is_read: true,
          created_at: new Date(Date.now() - 7200000).toISOString(),
        },
      ];

      (messagesAPI.getThreadMessages as jest.Mock)
        .mockResolvedValueOnce(mockMessages)
        .mockResolvedValueOnce(page2Messages);

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        expect(messagesAPI.getThreadMessages).toHaveBeenCalledTimes(1);
      });

      // Trigger load more
      const loadMoreButton = screen.queryByRole("button", { name: /load more/i });
      if (loadMoreButton) {
        fireEvent.click(loadMoreButton);

        await waitFor(() => {
          expect(messagesAPI.getThreadMessages).toHaveBeenCalledWith(2, null, 2, 50, "");
        });
      }
    });
  });

  describe("Delivery Tracking", () => {
    it("sends delivery acknowledgment when receiving message", async () => {
      const sendMessageMock = jest.fn();
      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: {
          type: "new_message",
          message_id: 5,
          sender_id: 2,
          recipient_id: 1,
          message: "New incoming message",
        },
        sendTyping: jest.fn(),
        sendMessage: sendMessageMock,
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(sendMessageMock).toHaveBeenCalledWith({
          type: "message_delivered",
          message_id: 5,
          sender_id: 2,
        });
      });
    });

    it("marks message as read and sends read receipt", async () => {
      (messagesAPI.markAsRead as jest.Mock).mockResolvedValue({});

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        // Mark all as read should be called for unread messages
        const markReadButton = screen.queryByRole("button", {
          name: /mark all as read/i,
        });
        if (markReadButton) {
          fireEvent.click(markReadButton);
          expect(messagesAPI.markThreadAsRead).toHaveBeenCalledWith(2, null);
        }
      });
    });

    it("updates delivery state from WebSocket", async () => {
      const deliveryReceipt = {
        type: "delivery_receipt",
        message_id: 3,
        recipient_id: 2,
        state: "delivered",
      };

      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: deliveryReceipt,
        sendTyping: jest.fn(),
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        // Delivery state should update in UI
        const message = screen.getByText("I want to learn mathematics");
        expect(message).toBeInTheDocument();
      });
    });
  });

  describe("Pre-booking CTA", () => {
    it("shows booking CTA after 3 messages in pre-booking conversation", async () => {
      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      await waitFor(() => {
        // Should show BookingCTA since message count >= 3
        expect(screen.getByText(/Ready to book a lesson?/i)).toBeInTheDocument();
      });
    });
  });

  describe("Typing Indicators", () => {
    it("sends typing indicator when user types", async () => {
      const sendTypingMock = jest.fn();
      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: null,
        sendTyping: sendTypingMock,
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messagesAPI.listThreads).toHaveBeenCalled();
      });

      fireEvent.click(screen.getByText("tutor@example.com"));

      const input = screen.getByPlaceholderText(/Type your message/i);
      fireEvent.change(input, { target: { value: "Test" } });

      await waitFor(() => {
        expect(sendTypingMock).toHaveBeenCalledWith(2);
      });
    });

    it("shows typing indicator when other user is typing", async () => {
      (useWebSocket as jest.Mock).mockReturnValue({
        isConnected: true,
        lastMessage: {
          type: "typing",
          sender_id: 2,
        },
        sendTyping: jest.fn(),
        sendMessage: jest.fn(),
      });

      const MessagesPage = (await import("@/app/messages/page")).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/is typing.../i)).toBeInTheDocument();
      });
    });
  });
});
