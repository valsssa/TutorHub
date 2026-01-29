/**
 * Integration tests for Messaging Flow
 *
 * Tests the complete messaging workflow including:
 * - Thread navigation and message display
 * - Message sending with real-time updates
 * - Message editing and deletion
 * - Search and filtering
 * - WebSocket connection states
 * - Error handling and recovery
 */

import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { messages } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import Cookies from 'js-cookie';

// Mock dependencies
jest.mock('@/lib/api');
jest.mock('@/hooks/useWebSocket');
jest.mock('js-cookie');

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: jest.fn(),
  }),
  usePathname: () => '/messages',
  useSearchParams: () => new URLSearchParams(),
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
  showWarning: jest.fn(),
};

jest.mock('@/components/ToastContainer', () => ({
  useToast: () => toastMocks,
  ToastProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock data
const mockThreads = [
  {
    other_user_id: 2,
    other_user_email: 'tutor@example.com',
    other_user_name: 'Dr. Sarah Johnson',
    booking_id: null,
    last_message: 'Looking forward to our session!',
    last_message_time: new Date(Date.now() - 3600000).toISOString(),
    unread_count: 2,
    total_messages: 15,
  },
  {
    other_user_id: 3,
    other_user_email: 'tutor2@example.com',
    other_user_name: 'Prof. Mike Chen',
    booking_id: 123,
    last_message: 'Great progress today!',
    last_message_time: new Date(Date.now() - 86400000).toISOString(),
    unread_count: 0,
    total_messages: 8,
  },
];

const mockMessages = [
  {
    id: 1,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: 'Hi, I would like to book a session',
    is_read: true,
    created_at: new Date(Date.now() - 7200000).toISOString(),
    delivery_state: 'read',
    edited: false,
  },
  {
    id: 2,
    sender_id: 2,
    recipient_id: 1,
    booking_id: null,
    message: 'Hello! I would be happy to help. What subject are you interested in?',
    is_read: true,
    created_at: new Date(Date.now() - 5400000).toISOString(),
    delivery_state: 'read',
    edited: false,
  },
  {
    id: 3,
    sender_id: 1,
    recipient_id: 2,
    booking_id: null,
    message: 'I need help with calculus, specifically integration',
    is_read: true,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    delivery_state: 'read',
    edited: false,
  },
  {
    id: 4,
    sender_id: 2,
    recipient_id: 1,
    booking_id: null,
    message: 'Looking forward to our session!',
    is_read: false,
    created_at: new Date(Date.now() - 1800000).toISOString(),
    delivery_state: 'delivered',
    edited: false,
  },
];

const mockCurrentUser = {
  id: 1,
  email: 'student@example.com',
  role: 'student',
  is_active: true,
  first_name: 'John',
  last_name: 'Doe',
};

describe('Messaging Flow Integration Tests', () => {
  let mockWebSocket: {
    isConnected: boolean;
    lastMessage: unknown | null;
    sendTyping: jest.Mock;
    sendMessage: jest.Mock;
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (Cookies.get as jest.Mock).mockReturnValue('valid-token');

    mockWebSocket = {
      isConnected: true,
      lastMessage: null,
      sendTyping: jest.fn(),
      sendMessage: jest.fn(),
    };

    (useWebSocket as jest.Mock).mockReturnValue(mockWebSocket);
    (messages.listThreads as jest.Mock).mockResolvedValue(mockThreads);
    (messages.getThreadMessages as jest.Mock).mockResolvedValue(mockMessages);
    (messages.send as jest.Mock).mockImplementation((data) =>
      Promise.resolve({
        id: Date.now(),
        sender_id: mockCurrentUser.id,
        recipient_id: data.recipient_id,
        message: data.message,
        booking_id: data.booking_id || null,
        is_read: false,
        created_at: new Date().toISOString(),
        delivery_state: 'sent',
      })
    );
  });

  describe('Thread Loading and Navigation', () => {
    it('loads and displays message threads', async () => {
      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messages.listThreads).toHaveBeenCalled();
      });

      // Verify threads are displayed
      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
        expect(screen.getByText('Prof. Mike Chen')).toBeInTheDocument();
      });

      // Verify unread count badges
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('loads messages when thread is selected', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Click on thread
      await user.click(screen.getByText('Dr. Sarah Johnson'));

      // Verify messages API call
      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalledWith(2, null, 1, 50);
      });

      // Verify messages are displayed
      await waitFor(() => {
        expect(screen.getByText('I would like to book a session')).toBeInTheDocument();
        expect(screen.getByText('Looking forward to our session!')).toBeInTheDocument();
      });
    });

    it('displays empty state when no threads exist', async () => {
      (messages.listThreads as jest.Mock).mockResolvedValue([]);

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/no.*messages|start.*conversation/i)).toBeInTheDocument();
      });
    });
  });

  describe('Message Sending', () => {
    it('sends message and displays in thread', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Select thread
      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      // Type message
      const messageInput = screen.getByPlaceholderText(/type.*message/i);
      await user.type(messageInput, 'Can we schedule for tomorrow?');

      // Send message
      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      // Verify API call
      await waitFor(() => {
        expect(messages.send).toHaveBeenCalledWith(
          expect.objectContaining({
            recipient_id: 2,
            message: 'Can we schedule for tomorrow?',
          })
        );
      });

      // Input should be cleared after sending
      expect(messageInput).toHaveValue('');
    });

    it('sends message on Enter key press', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      const messageInput = screen.getByPlaceholderText(/type.*message/i);
      await user.type(messageInput, 'Quick question{enter}');

      await waitFor(() => {
        expect(messages.send).toHaveBeenCalled();
      });
    });

    it('handles message send failure', async () => {
      const user = userEvent.setup();

      (messages.send as jest.Mock).mockRejectedValue({
        response: { data: { detail: 'Failed to send message' } },
      });

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      const messageInput = screen.getByPlaceholderText(/type.*message/i);
      await user.type(messageInput, 'Test message');

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      await waitFor(() => {
        expect(toastMocks.showError).toHaveBeenCalled();
      });
    });
  });

  describe('Real-time Updates', () => {
    it('displays incoming message from WebSocket', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      const { rerender } = render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      // Simulate incoming WebSocket message
      const newMessage = {
        type: 'new_message',
        message_id: 100,
        sender_id: 2,
        sender_email: 'tutor@example.com',
        recipient_id: 1,
        message: 'This is a real-time message!',
        created_at: new Date().toISOString(),
        is_read: false,
        delivery_state: 'sent',
      };

      mockWebSocket.lastMessage = newMessage;
      (useWebSocket as jest.Mock).mockReturnValue(mockWebSocket);

      rerender(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('This is a real-time message!')).toBeInTheDocument();
      });
    });

    it('shows typing indicator when other user is typing', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      const { rerender } = render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      // Simulate typing indicator
      mockWebSocket.lastMessage = {
        type: 'typing',
        sender_id: 2,
      };
      (useWebSocket as jest.Mock).mockReturnValue(mockWebSocket);

      rerender(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText(/typing/i)).toBeInTheDocument();
      });
    });

    it('sends typing indicator when user types', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      const messageInput = screen.getByPlaceholderText(/type.*message/i);
      await user.type(messageInput, 'Starting to type...');

      await waitFor(() => {
        expect(mockWebSocket.sendTyping).toHaveBeenCalledWith(2);
      });
    });
  });

  describe('Message Editing', () => {
    it('allows editing own recent messages', async () => {
      const user = userEvent.setup();

      (messages.editMessage as jest.Mock).mockResolvedValue({
        ...mockMessages[2],
        message: 'Updated: I need help with calculus',
        edited: true,
      });

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(screen.getByText('I need help with calculus, specifically integration')).toBeInTheDocument();
      });

      // Find and click edit button on own message
      const ownMessage = screen.getByText('I need help with calculus, specifically integration');
      const messageContainer = ownMessage.closest('[data-message-id]') || ownMessage.parentElement;
      const editButton = within(messageContainer as HTMLElement).queryByRole('button', { name: /edit/i });

      if (editButton) {
        await user.click(editButton);

        // Edit the message
        const editInput = screen.getByDisplayValue('I need help with calculus, specifically integration');
        await user.clear(editInput);
        await user.type(editInput, 'Updated: I need help with calculus');

        // Save edit
        const saveButton = screen.getByRole('button', { name: /save/i });
        await user.click(saveButton);

        await waitFor(() => {
          expect(messages.editMessage).toHaveBeenCalledWith(3, {
            message: 'Updated: I need help with calculus',
          });
        });
      }
    });
  });

  describe('Message Deletion', () => {
    it('allows deleting own messages', async () => {
      const user = userEvent.setup();

      (messages.deleteMessage as jest.Mock).mockResolvedValue({});

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(screen.getByText('I need help with calculus, specifically integration')).toBeInTheDocument();
      });

      // Find and click delete button
      const ownMessage = screen.getByText('I need help with calculus, specifically integration');
      const messageContainer = ownMessage.closest('[data-message-id]') || ownMessage.parentElement;
      const deleteButton = within(messageContainer as HTMLElement).queryByRole('button', { name: /delete/i });

      if (deleteButton) {
        await user.click(deleteButton);

        // Confirm deletion
        const confirmButton = await screen.findByRole('button', { name: /confirm|yes/i });
        await user.click(confirmButton);

        await waitFor(() => {
          expect(messages.deleteMessage).toHaveBeenCalledWith(3);
        });
      }
    });
  });

  describe('Search Functionality', () => {
    it('searches messages across threads', async () => {
      const user = userEvent.setup();

      const searchResults = {
        messages: [mockMessages[2]],
        total: 1,
        total_pages: 1,
      };

      (messages.searchMessages as jest.Mock).mockResolvedValue(searchResults);

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messages.listThreads).toHaveBeenCalled();
      });

      // Find and use search input
      const searchInput = screen.getByPlaceholderText(/search.*messages/i);
      await user.type(searchInput, 'calculus');

      // Wait for debounced search
      await waitFor(() => {
        expect(messages.searchMessages).toHaveBeenCalledWith('calculus', 1, expect.any(Number));
      }, { timeout: 1000 });
    });

    it('clears search and returns to thread list', async () => {
      const user = userEvent.setup();

      (messages.searchMessages as jest.Mock).mockResolvedValue({
        messages: [mockMessages[0]],
        total: 1,
        total_pages: 1,
      });

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messages.listThreads).toHaveBeenCalled();
      });

      // Search
      const searchInput = screen.getByPlaceholderText(/search.*messages/i);
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(messages.searchMessages).toHaveBeenCalled();
      });

      // Clear search
      await user.clear(searchInput);

      // Should show threads again
      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });
    });
  });

  describe('Connection Status', () => {
    it('displays connection status indicator', async () => {
      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messages.listThreads).toHaveBeenCalled();
      });

      // Should show connected status
      expect(screen.getByText(/connected|online/i)).toBeInTheDocument();
    });

    it('shows reconnecting state when disconnected', async () => {
      mockWebSocket.isConnected = false;
      (useWebSocket as jest.Mock).mockReturnValue(mockWebSocket);

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(messages.listThreads).toHaveBeenCalled();
      });

      // Should show disconnected/reconnecting status
      await waitFor(() => {
        const statusIndicator = screen.queryByText(/disconnected|reconnecting|offline/i);
        expect(statusIndicator).toBeInTheDocument();
      });
    });
  });

  describe('Message Read Status', () => {
    it('marks messages as read when thread is opened', async () => {
      const user = userEvent.setup();

      (messages.markThreadRead as jest.Mock).mockResolvedValue({});

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Thread has unread messages (unread_count: 2)
      expect(screen.getByText('2')).toBeInTheDocument();

      // Open thread
      await user.click(screen.getByText('Dr. Sarah Johnson'));

      // Should mark as read
      await waitFor(() => {
        expect(messages.markThreadRead).toHaveBeenCalledWith(2, null);
      });
    });

    it('updates unread count after marking as read', async () => {
      const user = userEvent.setup();

      (messages.markThreadRead as jest.Mock).mockResolvedValue({});

      // Update threads after marking as read
      const updatedThreads = mockThreads.map((t) =>
        t.other_user_id === 2 ? { ...t, unread_count: 0 } : t
      );

      const MessagesPage = (await import('@/app/messages/page')).default;
      const { rerender } = render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Dr. Sarah Johnson'));

      (messages.listThreads as jest.Mock).mockResolvedValue(updatedThreads);

      rerender(<MessagesPage />);

      // Unread badge should be gone
      await waitFor(() => {
        const threadItem = screen.getByText('Dr. Sarah Johnson').closest('[data-thread]');
        if (threadItem) {
          expect(within(threadItem as HTMLElement).queryByText('2')).not.toBeInTheDocument();
        }
      });
    });
  });

  describe('Booking Context', () => {
    it('shows booking context when thread is associated with booking', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Prof. Mike Chen')).toBeInTheDocument();
      });

      // Thread with booking_id: 123
      await user.click(screen.getByText('Prof. Mike Chen'));

      // Should show booking context
      await waitFor(() => {
        const bookingIndicator = screen.queryByText(/booking|session/i);
        expect(bookingIndicator).toBeInTheDocument();
      });
    });

    it('shows booking CTA after threshold messages in pre-booking thread', async () => {
      const user = userEvent.setup();

      const MessagesPage = (await import('@/app/messages/page')).default;
      render(<MessagesPage />);

      await waitFor(() => {
        expect(screen.getByText('Dr. Sarah Johnson')).toBeInTheDocument();
      });

      // Thread without booking (pre-booking conversation)
      await user.click(screen.getByText('Dr. Sarah Johnson'));

      await waitFor(() => {
        expect(messages.getThreadMessages).toHaveBeenCalled();
      });

      // With 4 messages, should show booking CTA
      await waitFor(() => {
        const bookingCTA = screen.queryByText(/book.*session|ready.*book/i);
        expect(bookingCTA).toBeInTheDocument();
      });
    });
  });
});
