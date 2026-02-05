'use client';

import { useRef, useCallback, useEffect, useState } from 'react';
import type {
  WebSocketState,
  ServerMessage,
  ClientMessage,
  UseWebSocketOptions,
  UseWebSocketReturn,
} from '@/types/websocket';

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1';

/**
 * WebSocket hook for real-time messaging
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong to detect dead connections
 * - Token-based authentication
 * - Type-safe message handling
 *
 * @example
 * ```tsx
 * const { isConnected, send, sendTyping } = useWebSocket({
 *   onMessage: (msg) => {
 *     if (msg.type === 'new_message') {
 *       // Handle new message
 *     }
 *   },
 * });
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    autoConnect = true,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectDelay = 1000,
    heartbeatInterval = 30000,
    connectionTimeout = 5000,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    onReconnecting,
  } = options;

  const [state, setState] = useState<WebSocketState>('disconnected');
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
  }, []);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }

    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  // Schedule reconnection with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (!autoReconnect || reconnectAttempt >= maxReconnectAttempts) {
      setState('disconnected');
      if (reconnectAttempt >= maxReconnectAttempts) {
        setLastError(`Max reconnection attempts (${maxReconnectAttempts}) exceeded`);
      }
      return;
    }

    const nextAttempt = reconnectAttempt + 1;
    const delay = Math.min(reconnectDelay * Math.pow(2, reconnectAttempt), 30000);

    setState('reconnecting');
    setReconnectAttempt(nextAttempt);
    onReconnecting?.(nextAttempt);

    reconnectTimeoutRef.current = setTimeout(() => {
      if (mountedRef.current) {
        connect();
      }
    }, delay);
  }, [autoReconnect, maxReconnectAttempts, reconnectAttempt, reconnectDelay, onReconnecting]);

  // Connect to WebSocket server
  const connect = useCallback(() => {
    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    clearTimers();
    setState('connecting');
    setLastError(null);

    try {
      // WebSocket connection uses cookies for authentication (no token in URL)
      // The backend will read the session cookie from the WebSocket handshake
      const wsUrl = `${WS_BASE_URL}/ws/messages`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      // Connection timeout
      connectionTimeoutRef.current = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.close();
          setLastError('Connection timeout');
          scheduleReconnect();
        }
      }, connectionTimeout);

      ws.onopen = () => {
        if (!mountedRef.current) return;

        clearTimeout(connectionTimeoutRef.current!);
        setState('connected');
        setReconnectAttempt(0);
        setLastError(null);
        startHeartbeat();
        onConnect?.();
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message = JSON.parse(event.data) as ServerMessage;

          // Handle pong internally
          if (message.type === 'pong') {
            return;
          }

          // Handle token expiration
          if (message.type === 'token_expired') {
            setLastError('Session expired');
            ws.close(4001, 'Token expired');
            return;
          }

          // Handle errors
          if (message.type === 'error') {
            setLastError(message.message);
          }

          // Forward to handler
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        if (!mountedRef.current) return;
        onError?.(event);
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;

        clearTimers();
        wsRef.current = null;

        onDisconnect?.(event.code, event.reason);

        // Don't reconnect on intentional close or auth failure
        if (event.code === 1000 || event.code === 4001 || event.code === 1008) {
          setState('disconnected');
          return;
        }

        scheduleReconnect();
      };
    } catch (err) {
      setLastError(err instanceof Error ? err.message : 'Connection failed');
      scheduleReconnect();
    }
  }, [
    clearTimers,
    connectionTimeout,
    onConnect,
    onDisconnect,
    onError,
    onMessage,
    scheduleReconnect,
    startHeartbeat,
  ]);

  // Disconnect from WebSocket server
  const disconnect = useCallback(() => {
    clearTimers();
    setReconnectAttempt(0);

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setState('disconnected');
  }, [clearTimers]);

  // Send a message
  const send = useCallback(<T extends ClientMessage>(message: T): boolean => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify(message));
      return true;
    } catch (err) {
      console.error('Failed to send WebSocket message:', err);
      return false;
    }
  }, []);

  // Convenience method: Send typing indicator
  const sendTyping = useCallback(
    (recipientId: number, isTyping: boolean) => {
      send({
        type: 'typing',
        recipient_id: recipientId,
        is_typing: isTyping,
      });
    },
    [send]
  );

  // Convenience method: Mark message as read
  const sendMessageRead = useCallback(
    (messageId: number) => {
      send({
        type: 'message_read',
        message_id: messageId,
      });
    },
    [send]
  );

  // Convenience method: Check presence
  const checkPresence = useCallback(
    (userIds: number[]) => {
      send({
        type: 'presence_check',
        user_ids: userIds,
      });
    },
    [send]
  );

  // Auto-connect on mount
  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      // Small delay to allow cookies to be set after login
      const timer = setTimeout(() => {
        if (mountedRef.current) {
          connect();
        }
      }, 100);

      return () => {
        clearTimeout(timer);
      };
    }
  }, [autoConnect, connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      clearTimers();
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
        wsRef.current = null;
      }
    };
  }, [clearTimers]);

  return {
    state,
    isConnected: state === 'connected',
    connect,
    disconnect,
    send,
    sendTyping,
    sendMessageRead,
    checkPresence,
    reconnectAttempt,
    lastError,
  };
}
