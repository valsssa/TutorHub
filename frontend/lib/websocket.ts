/**
 * WebSocket Client - Production-Ready Implementation with Enhanced Stability
 *
 * Features:
 * - Exponential backoff reconnection (1s -> 60s) with jitter
 * - Configurable max reconnection attempts
 * - Ping/pong heartbeat with dead connection detection
 * - Message queue for offline handling with retry
 * - Message acknowledgment system
 * - Visibility change detection (tab focus/blur)
 * - Network change detection (online/offline)
 * - Token expiration handling
 * - Multi-tab coordination via BroadcastChannel
 * - Connection state machine
 */

import { getWebSocketBaseUrl } from "@/shared/utils/url";

// Message types
export interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

export type { WebSocketMessage as Message };

// Connection states
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "failed";

// Message with acknowledgment tracking
interface PendingMessage {
  id: string;
  data: WebSocketMessage;
  timestamp: number;
  retries: number;
  maxRetries: number;
}

// Event handlers
type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (state: ConnectionState, details?: ConnectionDetails) => void;
type ErrorHandler = (error: Error) => void;

// Connection details for handlers
export interface ConnectionDetails {
  state: ConnectionState;
  reconnectAttempts: number;
  maxReconnectAttempts: number;
  nextReconnectMs: number | null;
  lastConnectedAt: number | null;
  lastDisconnectedAt: number | null;
  queuedMessages: number;
  isOnline: boolean;
  isVisible: boolean;
}

// Configuration
interface WebSocketConfig {
  pingIntervalMs: number;
  pongTimeoutMs: number;
  initialReconnectDelayMs: number;
  maxReconnectDelayMs: number;
  maxReconnectAttempts: number;
  messageRetryAttempts: number;
  messageAckTimeoutMs: number;
  maxQueueSize: number;
  jitterFactor: number;
}

const DEFAULT_CONFIG: WebSocketConfig = {
  pingIntervalMs: 30000,
  pongTimeoutMs: 10000,
  initialReconnectDelayMs: 1000,
  maxReconnectDelayMs: 60000,
  maxReconnectAttempts: 10,
  messageRetryAttempts: 3,
  messageAckTimeoutMs: 5000,
  maxQueueSize: 100,
  jitterFactor: 0.3,
};

// Generate unique message ID
function generateMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
}

export class WebSocketClient {
  // WebSocket connection
  private ws: WebSocket | null = null;
  private token: string;
  private url: string;
  private config: WebSocketConfig;

  // Connection state
  private state: ConnectionState = "disconnected";
  private isAuthenticated = false;
  private lastConnectedAt: number | null = null;
  private lastDisconnectedAt: number | null = null;

  // Reconnection state
  private reconnectAttempts = 0;
  private reconnectDelay: number;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private isManuallyDisconnected = false;

  // Health monitoring
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private pongTimeout: ReturnType<typeof setTimeout> | null = null;
  private lastPongTime = 0;
  private awaitingPong = false;

  // Message queue for offline handling
  private messageQueue: PendingMessage[] = [];
  private pendingAcks: Map<string, PendingMessage> = new Map();
  private ackTimeouts: Map<string, ReturnType<typeof setTimeout>> = new Map();

  // Network and visibility state
  private isOnline = true;
  private isVisible = true;
  private networkHandler: (() => void) | null = null;
  private visibilityHandler: (() => void) | null = null;

  // Event handlers
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();

  // Multi-tab coordination
  private broadcastChannel: BroadcastChannel | null = null;

  constructor(token: string, config: Partial<WebSocketConfig> = {}) {
    this.token = token;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.reconnectDelay = this.config.initialReconnectDelayMs;

    // Build WebSocket URL
    // Note: WebSocket endpoint is registered under /api/v1 prefix in backend
    const wsBaseUrl = getWebSocketBaseUrl(
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    );
    this.url = `${wsBaseUrl}/api/v1/ws/messages`;

    // Set up browser event listeners
    this.setupBrowserListeners();

    // Set up multi-tab coordination
    this.setupBroadcastChannel();
  }

  private setupBrowserListeners(): void {
    if (typeof window === "undefined") return;

    // Network status changes
    this.networkHandler = () => {
      const wasOnline = this.isOnline;
      this.isOnline = navigator.onLine;

      if (!wasOnline && this.isOnline && this.state === "failed") {
        // Network came back online after being failed - try to reconnect
        this.reconnectAttempts = 0;
        this.reconnectDelay = this.config.initialReconnectDelayMs;
        this.scheduleReconnect();
      } else if (this.isOnline && this.state === "disconnected" && !this.isManuallyDisconnected) {
        // We're online but disconnected - try to connect
        this.connect().catch(() => {});
      }
    };

    window.addEventListener("online", this.networkHandler);
    window.addEventListener("offline", this.networkHandler);
    this.isOnline = navigator.onLine;

    // Visibility changes (tab focus/blur)
    this.visibilityHandler = () => {
      const wasVisible = this.isVisible;
      this.isVisible = document.visibilityState === "visible";

      if (!wasVisible && this.isVisible) {
        // Tab became visible
        if (this.state === "connected") {
          // Send immediate ping to verify connection is still alive
          this.sendPing();
        } else if (
          (this.state === "disconnected" || this.state === "failed") &&
          !this.isManuallyDisconnected &&
          this.isOnline
        ) {
          // Try to reconnect
          this.reconnectAttempts = 0;
          this.reconnectDelay = this.config.initialReconnectDelayMs;
          this.connect().catch(() => {});
        }
      }
    };

    document.addEventListener("visibilitychange", this.visibilityHandler);
    this.isVisible = document.visibilityState === "visible";
  }

  private setupBroadcastChannel(): void {
    if (typeof window === "undefined" || !("BroadcastChannel" in window)) return;

    try {
      this.broadcastChannel = new BroadcastChannel("websocket-sync");
      this.broadcastChannel.onmessage = (event) => {
        const { type, data } = event.data;
        if (type === "token_refreshed" && data.token) {
          // Token was refreshed in another tab
          this.updateToken(data.token);
        }
      };
    } catch {
      // BroadcastChannel not available
    }
  }

  private setState(newState: ConnectionState): void {
    if (this.state === newState) return;

    this.state = newState;

    // Update timestamps
    if (newState === "connected") {
      this.lastConnectedAt = Date.now();
    } else if (newState === "disconnected" || newState === "failed") {
      this.lastDisconnectedAt = Date.now();
    }

    // Notify handlers
    const details = this.getConnectionDetails();
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(newState, details);
      } catch {
        // Silently ignore handler errors in production
      }
    });
  }

  async connect(): Promise<void> {
    // Prevent duplicate connection attempts
    if (this.state === "connecting" || this.state === "connected") {
      return;
    }

    // Check network status
    if (!this.isOnline) {
      this.setState("disconnected");
      return;
    }

    this.setState("connecting");
    this.isManuallyDisconnected = false;

    return new Promise((resolve, reject) => {
      try {
        // Build URL with token
        const wsUrl = this.token
          ? `${this.url}${this.url.includes("?") ? "&" : "?"}token=${encodeURIComponent(this.token)}`
          : this.url;

        this.ws = new WebSocket(wsUrl);

        const connectionTimeout = setTimeout(() => {
          if (this.state === "connecting") {
            this.ws?.close();
            reject(new Error("Connection timeout"));
          }
        }, 15000);

        // Connection opened
        this.ws.onopen = () => {
          clearTimeout(connectionTimeout);
          // Authentication is handled via token in query parameter
          // Server will send 'connection' message on successful auth
        };

        // Handle auth success
        const onAuthSuccess = () => {
          this.isAuthenticated = true;
          this.reconnectAttempts = 0;
          this.reconnectDelay = this.config.initialReconnectDelayMs;
          this.lastPongTime = Date.now();

          this.setState("connected");
          this.startPingInterval();
          this.processMessageQueue();

          resolve();
        };

        (this as { _onAuthSuccess?: () => void })._onAuthSuccess = onAuthSuccess;

        // Message received
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message, resolve, reject);
          } catch {
            // Failed to parse message - ignore malformed messages
          }
        };

        // Connection error
        this.ws.onerror = () => {
          clearTimeout(connectionTimeout);

          const error = new Error("WebSocket connection error");
          this.notifyError(error);

          if (this.state === "connecting") {
            this.setState("disconnected");
            reject(error);
          }
        };

        // Connection closed
        this.ws.onclose = (event) => {
          clearTimeout(connectionTimeout);
          this.handleClose(event);
        };
      } catch (error) {
        this.setState("disconnected");
        reject(error);
      }
    });
  }

  private handleMessage(
    message: WebSocketMessage,
    resolve: () => void,
    reject: (err: Error) => void
  ): void {
    // Handle authentication responses
    if (message.type === "auth_success" || message.type === "authenticated" || message.type === "connection") {
      const onAuthSuccess = (this as { _onAuthSuccess?: () => void })._onAuthSuccess;
      if (onAuthSuccess) {
        onAuthSuccess();
        delete (this as { _onAuthSuccess?: () => void })._onAuthSuccess;
      }
      return;
    }

    if (message.type === "auth_error" || message.type === "auth_failed") {
      this.isAuthenticated = false;
      const errorMessage = (message.error || message.message || "Authentication failed") as string;
      reject(new Error(errorMessage));
      return;
    }

    // Handle pong
    if (message.type === "pong") {
      this.lastPongTime = Date.now();
      this.awaitingPong = false;
      if (this.pongTimeout) {
        clearTimeout(this.pongTimeout);
        this.pongTimeout = null;
      }
      return;
    }

    // Handle message acknowledgment
    if (message.type === "ack" && typeof message.message_id === "string") {
      this.handleAck(message.message_id);
      return;
    }

    // Handle token expiration
    if (message.type === "token_expired" || message.type === "token_invalid") {
      this.notifyError(new Error("Token expired"));
      // Don't auto-reconnect for token issues - let the app refresh the token
      this.isManuallyDisconnected = true;
      this.disconnect();
      return;
    }

    // Notify message handlers
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch {
        // Silently ignore handler errors in production
      }
    });
  }

  private handleClose(event: CloseEvent): void {
    this.isAuthenticated = false;
    this.stopPingInterval();

    // Determine if we should reconnect
    if (this.isManuallyDisconnected) {
      this.setState("disconnected");
      return;
    }

    // Token-related close codes - don't auto-reconnect
    if (event.code === 1008 || event.code === 4001 || event.code === 4003) {
      this.setState("failed");
      return;
    }

    // Check reconnection limits
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.setState("failed");
      return;
    }

    // Schedule reconnection
    this.setState("reconnecting");
    this.scheduleReconnect();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }

    if (!this.isOnline) {
      return;
    }

    this.reconnectAttempts++;

    // Calculate delay with jitter
    const jitter = 1 + (Math.random() - 0.5) * 2 * this.config.jitterFactor;
    const delay = Math.min(
      this.reconnectDelay * jitter,
      this.config.maxReconnectDelayMs
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(() => {});
    }, delay);

    // Exponential backoff
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      this.config.maxReconnectDelayMs
    );

    // Notify handlers of state change with next reconnect time
    const details = this.getConnectionDetails();
    details.nextReconnectMs = delay;
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(this.state, details);
      } catch {
        // Silently ignore handler errors in production
      }
    });
  }

  private startPingInterval(): void {
    this.stopPingInterval();

    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendPing();
      }
    }, this.config.pingIntervalMs);
  }

  private sendPing(): void {
    if (this.awaitingPong) {
      // Already waiting for pong - connection may be dead
      return;
    }

    this.send({ type: "ping" });
    this.awaitingPong = true;

    // Set timeout for pong response
    this.pongTimeout = setTimeout(() => {
      if (this.awaitingPong) {
        this.ws?.close(4000, "Pong timeout");
      }
    }, this.config.pongTimeoutMs);
  }

  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
    this.awaitingPong = false;
  }

  // Message queue management
  private processMessageQueue(): void {
    if (this.state !== "connected" || this.messageQueue.length === 0) {
      return;
    }

    const messages = [...this.messageQueue];
    this.messageQueue = [];

    for (const pending of messages) {
      this.sendWithAck(pending.data, pending.id, pending.retries);
    }
  }

  private handleAck(messageId: string): void {
    const pending = this.pendingAcks.get(messageId);
    if (pending) {
      this.pendingAcks.delete(messageId);

      const timeout = this.ackTimeouts.get(messageId);
      if (timeout) {
        clearTimeout(timeout);
        this.ackTimeouts.delete(messageId);
      }
    }
  }

  // Public methods
  send(data: WebSocketMessage): boolean {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(data));
        return true;
      } catch {
        return false;
      }
    }

    // Connection not open - queue message if not a ping
    if (data.type !== "ping") {
      this.queueMessage(data);
    }
    return false;
  }

  sendWithAck(
    data: WebSocketMessage,
    messageId?: string,
    currentRetries = 0
  ): string {
    const id = messageId || generateMessageId();
    const messageWithId = { ...data, _ack_id: id };

    const pending: PendingMessage = {
      id,
      data,
      timestamp: Date.now(),
      retries: currentRetries,
      maxRetries: this.config.messageRetryAttempts,
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(messageWithId));
      this.pendingAcks.set(id, pending);

      // Set up timeout for acknowledgment
      const timeout = setTimeout(() => {
        this.handleAckTimeout(id);
      }, this.config.messageAckTimeoutMs);
      this.ackTimeouts.set(id, timeout);
    } else {
      // Queue for later
      this.queueMessage(data, id, currentRetries);
    }

    return id;
  }

  private handleAckTimeout(messageId: string): void {
    const pending = this.pendingAcks.get(messageId);
    if (!pending) return;

    this.pendingAcks.delete(messageId);
    this.ackTimeouts.delete(messageId);

    if (pending.retries < pending.maxRetries) {
      this.sendWithAck(pending.data, pending.id, pending.retries + 1);
    } else {
      this.notifyError(new Error(`Message delivery failed: ${messageId}`));
    }
  }

  private queueMessage(data: WebSocketMessage, id?: string, retries = 0): void {
    if (this.messageQueue.length >= this.config.maxQueueSize) {
      // Remove oldest message
      this.messageQueue.shift();
    }

    this.messageQueue.push({
      id: id || generateMessageId(),
      data,
      timestamp: Date.now(),
      retries,
      maxRetries: this.config.messageRetryAttempts,
    });
  }

  // Convenience methods
  sendTyping(recipientId: number): void {
    this.send({
      type: "typing",
      recipient_id: recipientId,
    });
  }

  sendMessageDelivered(messageId: number, senderId: number): void {
    this.send({
      type: "message_delivered",
      message_id: messageId,
      sender_id: senderId,
    });
  }

  sendMessageRead(messageId: number, senderId: number): void {
    this.send({
      type: "message_read",
      message_id: messageId,
      sender_id: senderId,
    });
  }

  checkPresence(userIds: number[]): void {
    this.send({
      type: "presence_check",
      user_ids: userIds,
    });
  }

  // Token management
  updateToken(newToken: string): void {
    const tokenChanged = this.token !== newToken;
    this.token = newToken;

    if (tokenChanged && this.state === "connected") {
      // Reconnect with new token
      this.disconnect();
      this.isManuallyDisconnected = false;
      this.connect().catch(() => {});
    }

    // Notify other tabs
    if (this.broadcastChannel && tokenChanged) {
      this.broadcastChannel.postMessage({ type: "token_refreshed", data: { token: newToken } });
    }
  }

  // Event subscription
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onConnectionChange(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    // Immediately call with current state
    handler(this.state, this.getConnectionDetails());
    return () => this.connectionHandlers.delete(handler);
  }

  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  private notifyError(error: Error): void {
    this.errorHandlers.forEach((handler) => {
      try {
        handler(error);
      } catch {
        // Silently ignore handler errors in production
      }
    });
  }

  // Manual reconnection
  reconnect(): void {
    this.isManuallyDisconnected = false;
    this.reconnectAttempts = 0;
    this.reconnectDelay = this.config.initialReconnectDelayMs;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connect().catch(() => {});
  }

  // Disconnect
  disconnect(): void {
    this.isManuallyDisconnected = true;
    this.stopPingInterval();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Clear all ack timeouts
    this.ackTimeouts.forEach((timeout) => clearTimeout(timeout));
    this.ackTimeouts.clear();
    this.pendingAcks.clear();

    if (this.ws) {
      try {
        this.ws.close(1000, "Client disconnecting");
      } catch {
        // Ignore close errors
      }
      this.ws = null;
    }

    this.setState("disconnected");
  }

  // Cleanup
  destroy(): void {
    this.disconnect();

    // Remove browser listeners
    if (typeof window !== "undefined") {
      if (this.networkHandler) {
        window.removeEventListener("online", this.networkHandler);
        window.removeEventListener("offline", this.networkHandler);
      }
      if (this.visibilityHandler) {
        document.removeEventListener("visibilitychange", this.visibilityHandler);
      }
    }

    // Close broadcast channel
    if (this.broadcastChannel) {
      this.broadcastChannel.close();
      this.broadcastChannel = null;
    }

    // Clear all handlers
    this.messageHandlers.clear();
    this.connectionHandlers.clear();
    this.errorHandlers.clear();
    this.messageQueue = [];
  }

  // Status getters
  isConnected(): boolean {
    return this.state === "connected";
  }

  getState(): ConnectionState {
    return this.state;
  }

  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  getConnectionDetails(): ConnectionDetails {
    let nextReconnectMs: number | null = null;
    if (this.state === "reconnecting" && this.reconnectTimeout) {
      // Estimate based on current delay
      nextReconnectMs = this.reconnectDelay;
    }

    return {
      state: this.state,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.config.maxReconnectAttempts,
      nextReconnectMs,
      lastConnectedAt: this.lastConnectedAt,
      lastDisconnectedAt: this.lastDisconnectedAt,
      queuedMessages: this.messageQueue.length + this.pendingAcks.size,
      isOnline: this.isOnline,
      isVisible: this.isVisible,
    };
  }

  getStats(): {
    connected: boolean;
    state: ConnectionState;
    reconnectAttempts: number;
    maxReconnectAttempts: number;
    isManual: boolean;
    lastPongMs: number;
    queuedMessages: number;
    isOnline: boolean;
    isVisible: boolean;
  } {
    return {
      connected: this.isConnected(),
      state: this.state,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.config.maxReconnectAttempts,
      isManual: this.isManuallyDisconnected,
      lastPongMs: this.lastPongTime > 0 ? Date.now() - this.lastPongTime : -1,
      queuedMessages: this.messageQueue.length + this.pendingAcks.size,
      isOnline: this.isOnline,
      isVisible: this.isVisible,
    };
  }
}

export function createWebSocketClient(
  token: string,
  config?: Partial<WebSocketConfig>
): WebSocketClient {
  return new WebSocketClient(token, config);
}
