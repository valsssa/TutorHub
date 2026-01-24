/**
 * WebSocket Client - Production-Ready Implementation
 * 
 * DDD + KISS Architecture:
 * - Single Responsibility: WebSocket connection management only
 * - Clean Interface: Simple subscribe/send pattern
 * - Automatic Reconnection: Exponential backoff with max attempts
 * - Health Monitoring: Ping/pong keep-alive
 * - Error Resilience: Graceful error handling
 * 
 * Features:
 * - Auto-reconnect with exponential backoff (1s -> 30s)
 * - Heartbeat monitoring (ping every 30s)
 * - Dead connection detection
 * - Multi-handler support (multiple subscribers)
 * - Clean disconnect handling
 */

import { getWebSocketBaseUrl } from "@/shared/utils/url";

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

// Re-export for convenience
export type { WebSocketMessage as Message };

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;

// Configuration constants
const PING_INTERVAL_MS = 30000; // 30 seconds
const INITIAL_RECONNECT_DELAY_MS = 1000; // 1 second
const MAX_RECONNECT_DELAY_MS = 30000; // 30 seconds
const MAX_RECONNECT_ATTEMPTS = 5;

export class WebSocketClient {
  // WebSocket connection
  private ws: WebSocket | null = null;
  private token: string;
  private url: string;
  
  // Reconnection state
  private reconnectAttempts = 0;
  private reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isManuallyDisconnected = false;
  private isConnecting = false;
  
  // Health monitoring
  private pingInterval: NodeJS.Timeout | null = null;
  private lastPongTime: number = 0;
  
  // Event handlers
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();

  constructor(token: string) {
    this.token = token;
    
    // Build WebSocket URL from API URL
    const wsBaseUrl = getWebSocketBaseUrl(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000');
    this.url = `${wsBaseUrl}/ws/messages?token=${token}`;
    
    console.log(`[WebSocket] Initialized with URL: ${this.url.replace(/token=.*/, 'token=***')}`);
  }

  async connect(): Promise<void> {
    // Prevent duplicate connection attempts
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.log('[WebSocket] Already connecting or connected');
      return;
    }

    this.isConnecting = true;
    console.log(`[WebSocket] Connecting... (attempt ${this.reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        this.isManuallyDisconnected = false;

        // Connection opened successfully
        this.ws.onopen = () => {
          console.log('✅ [WebSocket] Connected successfully');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
          this.lastPongTime = Date.now();
          this.startPingInterval();
          this.notifyConnectionHandlers(true);
          resolve();
        };

        // Message received from server
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            
            // Update last pong time for health monitoring
            if (message.type === 'pong') {
              this.lastPongTime = Date.now();
            }
            
            // Log only non-ping/pong messages (reduce noise)
            if (message.type !== 'pong' && message.type !== 'ping') {
              console.log(`📨 [WebSocket] ${message.type}`, message);
            }
            
            // Notify all handlers
            this.messageHandlers.forEach((handler) => {
              try {
                handler(message);
              } catch (error) {
                console.error('[WebSocket] Handler error:', error);
              }
            });
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        // Connection error
        this.ws.onerror = (error) => {
          console.error('❌ [WebSocket] Connection error:', error);
          this.isConnecting = false;
          this.notifyConnectionHandlers(false);
          reject(error);
        };

        // Connection closed
        this.ws.onclose = (event) => {
          const reason = event.reason || 'Unknown reason';
          console.log(`❌ [WebSocket] Disconnected: code=${event.code}, reason=${reason}`);
          
          this.isConnecting = false;
          this.stopPingInterval();
          this.notifyConnectionHandlers(false);

          // Auto-reconnect if not manually disconnected
          if (!this.isManuallyDisconnected && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            this.scheduleReconnect();
          } else if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            console.error('❌ [WebSocket] Max reconnection attempts reached');
          }
        };
        
      } catch (error) {
        console.error('[WebSocket] Connection setup failed:', error);
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  private scheduleReconnect(): void {
    // Clear any existing reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    this.reconnectAttempts++;
    
    console.log(
      `🔄 [WebSocket] Scheduling reconnection... ` +
      `Attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${this.reconnectDelay}ms`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('❌ [WebSocket] Reconnection failed:', error);
      });
    }, this.reconnectDelay);

    // Exponential backoff: 1s -> 2s -> 4s -> 8s -> 16s -> 30s (max)
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_DELAY_MS);
  }

  private startPingInterval(): void {
    // Clear any existing interval
    this.stopPingInterval();
    
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Send ping
        this.send({ type: 'ping' });
        
        // Check if connection is healthy (received pong recently)
        const timeSinceLastPong = Date.now() - this.lastPongTime;
        if (timeSinceLastPong > PING_INTERVAL_MS * 2) {
          console.warn(
            `⚠️ [WebSocket] No pong received for ${timeSinceLastPong}ms, connection may be dead`
          );
          // Connection might be dead, close and trigger reconnection
          this.ws.close();
        }
      }
    }, PING_INTERVAL_MS);
    
    console.log(`💓 [WebSocket] Heartbeat started (every ${PING_INTERVAL_MS}ms)`);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
      console.log('[WebSocket] Heartbeat stopped');
    }
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach((handler) => handler(connected));
  }

  send(data: any): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        return true;
      } catch (error) {
        console.error('[WebSocket] Failed to send message:', error, data);
        return false;
      }
    } else {
      const state = this.ws?.readyState;
      const stateStr = state === WebSocket.CONNECTING ? 'CONNECTING' :
                       state === WebSocket.CLOSING ? 'CLOSING' :
                       state === WebSocket.CLOSED ? 'CLOSED' : 'UNKNOWN';
      console.warn(`⚠️ [WebSocket] Cannot send, state: ${stateStr}`, data);
      return false;
    }
  }

  sendTyping(recipientId: number): void {
    this.send({
      type: 'typing',
      recipient_id: recipientId,
    });
  }

  sendMessageDelivered(messageId: number, senderId: number): void {
    this.send({
      type: 'message_delivered',
      message_id: messageId,
      sender_id: senderId,
    });
  }

  sendMessageRead(messageId: number, senderId: number): void {
    this.send({
      type: 'message_read',
      message_id: messageId,
      sender_id: senderId,
    });
  }

  checkPresence(userIds: number[]): void {
    this.send({
      type: 'presence_check',
      user_ids: userIds,
    });
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    // Return unsubscribe function
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    // Return unsubscribe function
    return () => {
      this.connectionHandlers.delete(handler);
    };
  }

  disconnect(): void {
    console.log('👋 [WebSocket] Manual disconnect requested');
    
    // Mark as manually disconnected (prevents auto-reconnect)
    this.isManuallyDisconnected = true;
    
    // Stop all timers
    this.stopPingInterval();
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Close WebSocket connection
    if (this.ws) {
      try {
        this.ws.close(1000, 'Client disconnecting'); // Normal closure
      } catch (error) {
        console.error('[WebSocket] Error closing connection:', error);
      }
      this.ws = null;
    }
    
    // Notify handlers
    this.notifyConnectionHandlers(false);
    
    // Clear handlers for clean shutdown
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    
    console.log('[WebSocket] Disconnected and cleaned up');
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }
  
  getConnectionState(): string {
    if (!this.ws) return 'DISCONNECTED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'CONNECTED';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'DISCONNECTED';
      default:
        return 'UNKNOWN';
    }
  }
  
  getStats(): {
    connected: boolean;
    state: string;
    reconnectAttempts: number;
    isManual: boolean;
    lastPongMs: number;
  } {
    return {
      connected: this.isConnected(),
      state: this.getConnectionState(),
      reconnectAttempts: this.reconnectAttempts,
      isManual: this.isManuallyDisconnected,
      lastPongMs: this.lastPongTime > 0 ? Date.now() - this.lastPongTime : -1,
    };
  }
}

export function createWebSocketClient(token: string): WebSocketClient {
  return new WebSocketClient(token);
}
