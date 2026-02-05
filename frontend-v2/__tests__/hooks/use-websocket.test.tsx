import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '@/lib/hooks/use-websocket';

// Store WebSocket instances for testing
let mockWsInstance: MockWebSocket | null = null;

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    mockWsInstance = this;
  }

  send = vi.fn();

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
  }

  // Helper to simulate connection open
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  // Helper to simulate receiving a message
  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
  }

  // Helper to simulate error
  simulateError() {
    this.onerror?.(new Event('error'));
  }
}

describe('useWebSocket', () => {
  beforeEach(() => {
    mockWsInstance = null;
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  describe('initialization', () => {
    it('should start disconnected when autoConnect is false', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      expect(result.current.state).toBe('disconnected');
      expect(result.current.isConnected).toBe(false);
    });

    it('should expose connect and disconnect functions', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      expect(typeof result.current.connect).toBe('function');
      expect(typeof result.current.disconnect).toBe('function');
      expect(typeof result.current.send).toBe('function');
    });
  });

  describe('connection', () => {
    it('should connect using cookies (no token in URL)', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
      });

      // URL should not contain token - authentication is via cookies
      expect(mockWsInstance?.url).not.toContain('token=');
      expect(mockWsInstance?.url).toContain('/ws/messages');
    });

    it('should transition to connecting state', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
      });

      expect(result.current.state).toBe('connecting');
    });

    it('should transition to connected state on open', () => {
      const onConnect = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onConnect })
      );

      act(() => {
        result.current.connect();
      });

      act(() => {
        mockWsInstance?.simulateOpen();
      });

      expect(result.current.state).toBe('connected');
      expect(result.current.isConnected).toBe(true);
      expect(onConnect).toHaveBeenCalled();
    });
  });

  describe('message handling', () => {
    it('should call onMessage for incoming messages', () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onMessage })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.simulateMessage({
          type: 'new_message',
          message_id: 1,
          sender_id: 2,
          content: 'Hello',
        });
      });

      expect(onMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'new_message',
          message_id: 1,
        })
      );
    });

    it('should not call onMessage for pong messages', () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onMessage })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.simulateMessage({ type: 'pong' });
      });

      expect(onMessage).not.toHaveBeenCalled();
    });

    it('should handle token expiration', () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onMessage })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.simulateMessage({
          type: 'token_expired',
          message: 'Token has expired',
        });
      });

      expect(result.current.lastError).toBe('Session expired');
      expect(onMessage).not.toHaveBeenCalled();
    });

    it('should set lastError on error messages', () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onMessage })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.simulateMessage({
          type: 'error',
          message: 'Something went wrong',
        });
      });

      expect(result.current.lastError).toBe('Something went wrong');
      expect(onMessage).toHaveBeenCalled(); // Error messages are still forwarded
    });
  });

  describe('sending messages', () => {
    it('should send typing indicator', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        result.current.sendTyping(123, true);
      });

      expect(mockWsInstance?.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'typing',
          recipient_id: 123,
          is_typing: true,
        })
      );
    });

    it('should send message read', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        result.current.sendMessageRead(456);
      });

      expect(mockWsInstance?.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'message_read',
          message_id: 456,
        })
      );
    });

    it('should send presence check', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        result.current.checkPresence([1, 2, 3]);
      });

      expect(mockWsInstance?.send).toHaveBeenCalledWith(
        JSON.stringify({
          type: 'presence_check',
          user_ids: [1, 2, 3],
        })
      );
    });

    it('should return false when sending on disconnected socket', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      let sent = false;
      act(() => {
        sent = result.current.send({ type: 'ping' });
      });

      expect(sent).toBe(false);
    });

    it('should return true when sending on connected socket', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      let sent = false;
      act(() => {
        sent = result.current.send({ type: 'ping' });
      });

      expect(sent).toBe(true);
    });
  });

  describe('disconnection', () => {
    it('should call onDisconnect when connection closes', () => {
      const onDisconnect = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, onDisconnect, autoReconnect: false })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.close(1000, 'Normal closure');
      });

      expect(onDisconnect).toHaveBeenCalledWith(1000, 'Normal closure');
      expect(result.current.state).toBe('disconnected');
    });

    it('should disconnect cleanly when disconnect is called', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, autoReconnect: true })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      expect(result.current.isConnected).toBe(true);

      act(() => {
        result.current.disconnect();
      });

      expect(result.current.state).toBe('disconnected');
      expect(result.current.reconnectAttempt).toBe(0);
    });
  });

  describe('reconnection', () => {
    it('should set reconnecting state on unexpected disconnect', () => {
      const onReconnecting = vi.fn();
      const { result } = renderHook(() =>
        useWebSocket({
          autoConnect: false,
          autoReconnect: true,
          onReconnecting,
        })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        // Simulate unexpected disconnect (code 1006)
        mockWsInstance?.close(1006, 'Connection lost');
      });

      expect(result.current.state).toBe('reconnecting');
      expect(result.current.reconnectAttempt).toBe(1);
      expect(onReconnecting).toHaveBeenCalledWith(1);
    });

    it('should not reconnect on auth failure (code 4001)', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, autoReconnect: true })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.close(4001, 'Token expired');
      });

      expect(result.current.state).toBe('disconnected');
      expect(result.current.reconnectAttempt).toBe(0);
    });

    it('should not reconnect on normal close (code 1000)', () => {
      const { result } = renderHook(() =>
        useWebSocket({ autoConnect: false, autoReconnect: true })
      );

      act(() => {
        result.current.connect();
        mockWsInstance?.simulateOpen();
      });

      act(() => {
        mockWsInstance?.close(1000, 'Normal closure');
      });

      expect(result.current.state).toBe('disconnected');
      expect(result.current.reconnectAttempt).toBe(0);
    });
  });
});
