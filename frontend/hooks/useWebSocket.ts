/**
 * React WebSocket Hook - Production-Ready
 * Clean state management for real-time messaging.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import Cookies from 'js-cookie';
import { WebSocketClient, createWebSocketClient } from '@/lib/websocket';
import type { WebSocketMessage } from '@/lib/websocket';

export type { WebSocketMessage };

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const clientRef = useRef<WebSocketClient | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    const token = Cookies.get('token');
    if (!token) {
      console.warn('[useWebSocket] No token found, cannot connect');
      return;
    }

    // Create WebSocket client
    const client = createWebSocketClient(token);
    clientRef.current = client;

    // Register connection state handler
    const unsubscribeConnection = client.onConnectionChange((connected) => {
      if (mountedRef.current) {
        setIsConnected(connected);
      }
    });

    // Register message handler
    const unsubscribeMessages = client.onMessage((message: WebSocketMessage) => {
      if (mountedRef.current) {
        setLastMessage(message);
      }
    });

    // Connect to WebSocket
    client.connect().catch((error) => {
      console.error('[useWebSocket] Failed to connect:', error);
    });

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      unsubscribeConnection();
      unsubscribeMessages();
      client.disconnect();
      setIsConnected(false);
    };
  }, []); // Only run once on mount

  const sendMessage = useCallback((data: any) => {
    if (clientRef.current) {
      clientRef.current.send(data);
    } else {
      console.warn('[useWebSocket] Client not initialized');
    }
  }, []);

  const sendTyping = useCallback((recipientId: number) => {
    if (clientRef.current) {
      clientRef.current.sendTyping(recipientId);
    }
  }, []);

  const sendMessageDelivered = useCallback((messageId: number, senderId: number) => {
    if (clientRef.current) {
      clientRef.current.sendMessageDelivered(messageId, senderId);
    }
  }, []);

  const sendMessageRead = useCallback((messageId: number, senderId: number) => {
    if (clientRef.current) {
      clientRef.current.sendMessageRead(messageId, senderId);
    }
  }, []);

  const checkPresence = useCallback((userIds: number[]) => {
    if (clientRef.current) {
      clientRef.current.checkPresence(userIds);
    }
  }, []);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    sendTyping,
    sendMessageDelivered,
    sendMessageRead,
    checkPresence,
    client: clientRef.current,
  };
}
