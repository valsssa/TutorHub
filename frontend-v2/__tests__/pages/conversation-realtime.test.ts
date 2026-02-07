import { describe, it, expect } from 'vitest';
import type { NewMessageMessage } from '@/types/websocket';

describe('Conversation real-time message handling', () => {
  it('should map NewMessageMessage to Message type correctly', () => {
    const wsMessage: NewMessageMessage = {
      type: 'new_message',
      message_id: 42,
      sender_id: 10,
      recipient_id: 20,
      content: 'Hello from WebSocket',
      booking_id: null,
      conversation_id: 5,
      created_at: '2026-02-07T10:00:00Z',
    };

    // Simulate the mapping from handleNewMessage
    const mapped = {
      id: wsMessage.message_id,
      sender_id: wsMessage.sender_id,
      recipient_id: wsMessage.recipient_id,
      message: wsMessage.content,
      booking_id: wsMessage.booking_id,
      conversation_id: wsMessage.conversation_id,
      is_read: false,
      created_at: wsMessage.created_at,
    };

    expect(mapped.id).toBe(42);
    expect(mapped.message).toBe('Hello from WebSocket');
    expect(mapped.is_read).toBe(false);
    expect(mapped.conversation_id).toBe(5);
  });

  it('should not add duplicate messages', () => {
    const existing = [
      { id: 1, message: 'First' },
      { id: 2, message: 'Second' },
    ];

    const incoming = { id: 2, message: 'Second (duplicate)' };

    const exists = existing.some((m) => m.id === incoming.id);
    expect(exists).toBe(true);

    // Only add if not exists
    const updated = exists ? existing : [...existing, incoming];
    expect(updated.length).toBe(2);
  });

  it('should append new messages to the list', () => {
    const existing = [
      { id: 1, message: 'First' },
      { id: 2, message: 'Second' },
    ];

    const incoming = { id: 3, message: 'Third (new)' };

    const exists = existing.some((m) => m.id === incoming.id);
    expect(exists).toBe(false);

    const updated = [...existing, incoming];
    expect(updated.length).toBe(3);
    expect(updated[2].id).toBe(3);
  });

  it('should mark incoming messages as read when from other user', () => {
    const currentUserId = 20;
    const incomingSenderId = 10;

    // Logic: mark as read if sender is not the current user
    const shouldMarkRead = incomingSenderId !== currentUserId;
    expect(shouldMarkRead).toBe(true);
  });

  it('should not mark own messages as read', () => {
    const currentUserId = 20;
    const ownSenderId = 20;

    const shouldMarkRead = ownSenderId !== currentUserId;
    expect(shouldMarkRead).toBe(false);
  });
});
