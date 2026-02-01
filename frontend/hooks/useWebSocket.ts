/**
 * React WebSocket Hook - Production-Ready with Enhanced Stability
 *
 * Features:
 * - Detailed connection state tracking
 * - Manual reconnection capability
 * - Token refresh integration
 * - Error handling with callbacks
 * - Queue status monitoring
 * - Automatic cleanup on unmount
 */

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import Cookies from "js-cookie";
import {
  WebSocketClient,
  createWebSocketClient,
  ConnectionState,
  ConnectionDetails,
} from "@/lib/websocket";
import type { WebSocketMessage } from "@/lib/websocket";

export type { WebSocketMessage, ConnectionState, ConnectionDetails };

export interface WebSocketState {
  isConnected: boolean;
  connectionState: ConnectionState;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  nextReconnectMs: number | null;
  queuedMessages: number;
  isOnline: boolean;
  lastError: Error | null;
}

export interface UseWebSocketOptions {
  autoConnect?: boolean;
  onError?: (error: Error) => void;
  onTokenExpired?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { autoConnect = true, onError, onTokenExpired } = options;

  // State
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    connectionState: "disconnected",
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
    nextReconnectMs: null,
    queuedMessages: 0,
    isOnline: typeof navigator !== "undefined" ? navigator.onLine : true,
    lastError: null,
  });
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  // Refs
  const clientRef = useRef<WebSocketClient | null>(null);
  const mountedRef = useRef(true);
  const tokenRef = useRef<string | null>(null);

  // Callbacks stored in refs to avoid re-creating effect
  const onErrorRef = useRef(onError);
  const onTokenExpiredRef = useRef(onTokenExpired);
  onErrorRef.current = onError;
  onTokenExpiredRef.current = onTokenExpired;

  // Initialize WebSocket client
  useEffect(() => {
    mountedRef.current = true;

    const token = Cookies.get("token");
    if (!token) {
      setState((prev) => ({
        ...prev,
        connectionState: "disconnected",
        isConnected: false,
      }));
      return;
    }

    tokenRef.current = token;

    // Create WebSocket client
    const client = createWebSocketClient(token);
    clientRef.current = client;

    // Register connection state handler
    const unsubscribeConnection = client.onConnectionChange(
      (newState: ConnectionState, details?: ConnectionDetails) => {
        if (!mountedRef.current) return;

        setState((prev) => ({
          ...prev,
          isConnected: newState === "connected",
          connectionState: newState,
          reconnectAttempts: details?.reconnectAttempts ?? prev.reconnectAttempts,
          maxReconnectAttempts: details?.maxReconnectAttempts ?? prev.maxReconnectAttempts,
          nextReconnectMs: details?.nextReconnectMs ?? null,
          queuedMessages: details?.queuedMessages ?? prev.queuedMessages,
          isOnline: details?.isOnline ?? prev.isOnline,
        }));
      }
    );

    // Register message handler
    const unsubscribeMessages = client.onMessage((message: WebSocketMessage) => {
      if (!mountedRef.current) return;
      setLastMessage(message);
    });

    // Register error handler
    const unsubscribeErrors = client.onError((error: Error) => {
      if (!mountedRef.current) return;

      setState((prev) => ({
        ...prev,
        lastError: error,
      }));

      // Check for token expiration
      if (error.message.includes("Token expired") || error.message.includes("token_expired")) {
        onTokenExpiredRef.current?.();
      } else {
        onErrorRef.current?.(error);
      }
    });

    // Connect if autoConnect is enabled
    if (autoConnect) {
      client.connect().catch((error) => {
        if (mountedRef.current) {
          setState((prev) => ({
            ...prev,
            lastError: error instanceof Error ? error : new Error(String(error)),
          }));
        }
      });
    }

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      unsubscribeConnection();
      unsubscribeMessages();
      unsubscribeErrors();
      client.destroy();
    };
  }, [autoConnect]);

  // Token refresh handler - update token when cookie changes
  useEffect(() => {
    const checkToken = () => {
      const currentToken = Cookies.get("token");
      if (currentToken && currentToken !== tokenRef.current && clientRef.current) {
        tokenRef.current = currentToken;
        clientRef.current.updateToken(currentToken);
      }
    };

    // Check token periodically (every 30 seconds)
    const interval = setInterval(checkToken, 30000);

    return () => clearInterval(interval);
  }, []);

  // Memoized actions
  const sendMessage = useCallback((data: WebSocketMessage) => {
    if (clientRef.current) {
      return clientRef.current.send(data);
    }
    return false;
  }, []);

  const sendWithAck = useCallback((data: WebSocketMessage): string | null => {
    if (clientRef.current) {
      return clientRef.current.sendWithAck(data);
    }
    return null;
  }, []);

  const sendTyping = useCallback((recipientId: number) => {
    clientRef.current?.sendTyping(recipientId);
  }, []);

  const sendMessageDelivered = useCallback((messageId: number, senderId: number) => {
    clientRef.current?.sendMessageDelivered(messageId, senderId);
  }, []);

  const sendMessageRead = useCallback((messageId: number, senderId: number) => {
    clientRef.current?.sendMessageRead(messageId, senderId);
  }, []);

  const checkPresence = useCallback((userIds: number[]) => {
    clientRef.current?.checkPresence(userIds);
  }, []);

  const reconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.reconnect();
    } else {
      // Try to create a new client if one doesn't exist
      const token = Cookies.get("token");
      if (token) {
        const client = createWebSocketClient(token);
        clientRef.current = client;
        client.connect().catch(() => {
          // Connection error handled by error callback
        });
      }
    }
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  const updateToken = useCallback((newToken: string) => {
    tokenRef.current = newToken;
    clientRef.current?.updateToken(newToken);
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      lastError: null,
    }));
  }, []);

  // Get detailed stats (memoized)
  const getStats = useCallback(() => {
    return clientRef.current?.getStats() ?? null;
  }, []);

  // Computed values
  const isReconnecting = state.connectionState === "reconnecting";
  const hasFailed = state.connectionState === "failed";
  const canReconnect = hasFailed || (state.connectionState === "disconnected" && !state.isConnected);

  // Return value
  return useMemo(
    () => ({
      // Connection state
      isConnected: state.isConnected,
      connectionState: state.connectionState,
      isReconnecting,
      hasFailed,
      canReconnect,

      // Reconnection info
      reconnectAttempts: state.reconnectAttempts,
      maxReconnectAttempts: state.maxReconnectAttempts,
      nextReconnectMs: state.nextReconnectMs,

      // Queue info
      queuedMessages: state.queuedMessages,

      // Network status
      isOnline: state.isOnline,

      // Error handling
      lastError: state.lastError,
      clearError,

      // Messages
      lastMessage,

      // Actions
      sendMessage,
      sendWithAck,
      sendTyping,
      sendMessageDelivered,
      sendMessageRead,
      checkPresence,
      reconnect,
      disconnect,
      updateToken,

      // Utilities
      getStats,
      client: clientRef.current,
    }),
    [
      state,
      isReconnecting,
      hasFailed,
      canReconnect,
      lastMessage,
      sendMessage,
      sendWithAck,
      sendTyping,
      sendMessageDelivered,
      sendMessageRead,
      checkPresence,
      reconnect,
      disconnect,
      updateToken,
      clearError,
      getStats,
    ]
  );
}

/**
 * Hook for subscribing to specific message types
 */
export function useWebSocketMessage<T = WebSocketMessage>(
  messageType: string,
  callback: (message: T) => void
) {
  const { lastMessage } = useWebSocket({ autoConnect: false });

  useEffect(() => {
    if (lastMessage && lastMessage.type === messageType) {
      callback(lastMessage as unknown as T);
    }
  }, [lastMessage, messageType, callback]);
}
