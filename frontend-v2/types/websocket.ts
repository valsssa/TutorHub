/**
 * WebSocket message types matching backend protocol
 * @see backend/modules/messages/websocket.py
 */

// Connection states
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

// Client -> Server message types
export type ClientMessageType =
  | 'ping'
  | 'ack'
  | 'typing'
  | 'message_delivered'
  | 'message_read'
  | 'presence_check'
  | 'refresh_token';

// Server -> Client message types
export type ServerMessageType =
  | 'connection'
  | 'pong'
  | 'new_message'
  | 'message_sent'
  | 'message_read'
  | 'typing'
  | 'presence_status'
  | 'delivery_receipt'
  | 'ack'
  | 'token_expired'
  | 'error';

// Base message interface
export interface WebSocketMessage {
  type: string;
  _ack_id?: string;
}

// Client -> Server messages
export interface PingMessage extends WebSocketMessage {
  type: 'ping';
}

export interface AckMessage extends WebSocketMessage {
  type: 'ack';
  ack_id: string;
}

export interface TypingMessage extends WebSocketMessage {
  type: 'typing';
  recipient_id: number;
  is_typing: boolean;
}

export interface MessageDeliveredMessage extends WebSocketMessage {
  type: 'message_delivered';
  message_id: number;
}

export interface MessageReadMessage extends WebSocketMessage {
  type: 'message_read';
  message_id: number;
}

export interface PresenceCheckMessage extends WebSocketMessage {
  type: 'presence_check';
  user_ids: number[];
}

export interface RefreshTokenMessage extends WebSocketMessage {
  type: 'refresh_token';
  token: string;
}

// Server -> Client messages
export interface ConnectionMessage extends WebSocketMessage {
  type: 'connection';
  status: 'connected';
  user_id: number;
}

export interface PongMessage extends WebSocketMessage {
  type: 'pong';
}

export interface NewMessageMessage extends WebSocketMessage {
  type: 'new_message';
  message_id: number;
  sender_id: number;
  sender_name?: string;
  recipient_id: number;
  content: string;
  booking_id?: number;
  conversation_id?: number;
  created_at: string;
}

export interface MessageSentMessage extends WebSocketMessage {
  type: 'message_sent';
  message_id: number;
  recipient_id: number;
  content: string;
  created_at: string;
}

export interface MessageReadAckMessage extends WebSocketMessage {
  type: 'message_read';
  message_id: number;
  read_by: number;
  read_at: string;
}

export interface TypingIndicatorMessage extends WebSocketMessage {
  type: 'typing';
  user_id: number;
  is_typing: boolean;
}

export interface PresenceStatusMessage extends WebSocketMessage {
  type: 'presence_status';
  user_statuses: Record<number, 'online' | 'offline'>;
}

export interface DeliveryReceiptMessage extends WebSocketMessage {
  type: 'delivery_receipt';
  message_id: number;
  delivered_at: string;
}

export interface ServerAckMessage extends WebSocketMessage {
  type: 'ack';
  ack_id: string;
  status: 'received';
}

export interface TokenExpiredMessage extends WebSocketMessage {
  type: 'token_expired';
  message: string;
}

export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  message: string;
  code?: string;
}

// Union types for type guards
export type ClientMessage =
  | PingMessage
  | AckMessage
  | TypingMessage
  | MessageDeliveredMessage
  | MessageReadMessage
  | PresenceCheckMessage
  | RefreshTokenMessage;

export type ServerMessage =
  | ConnectionMessage
  | PongMessage
  | NewMessageMessage
  | MessageSentMessage
  | MessageReadAckMessage
  | TypingIndicatorMessage
  | PresenceStatusMessage
  | DeliveryReceiptMessage
  | ServerAckMessage
  | TokenExpiredMessage
  | ErrorMessage;

// WebSocket hook options
export interface UseWebSocketOptions {
  /** Auto-connect on mount (default: true) */
  autoConnect?: boolean;
  /** Reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  /** Max reconnection attempts (default: 5) */
  maxReconnectAttempts?: number;
  /** Base delay between reconnects in ms (default: 1000) */
  reconnectDelay?: number;
  /** Heartbeat interval in ms (default: 30000) */
  heartbeatInterval?: number;
  /** Connection timeout in ms (default: 5000) */
  connectionTimeout?: number;
  /** Message handlers */
  onMessage?: (message: ServerMessage) => void;
  onConnect?: () => void;
  onDisconnect?: (code: number, reason: string) => void;
  onError?: (error: Event) => void;
  onReconnecting?: (attempt: number) => void;
}

// WebSocket hook return type
export interface UseWebSocketReturn {
  /** Current connection state */
  state: WebSocketState;
  /** Whether connected */
  isConnected: boolean;
  /** Connect to WebSocket server */
  connect: () => void;
  /** Disconnect from WebSocket server */
  disconnect: () => void;
  /** Send a message to the server */
  send: <T extends ClientMessage>(message: T) => boolean;
  /** Send typing indicator */
  sendTyping: (recipientId: number, isTyping: boolean) => void;
  /** Mark message as read */
  sendMessageRead: (messageId: number) => void;
  /** Check presence of users */
  checkPresence: (userIds: number[]) => void;
  /** Current reconnection attempt (0 if not reconnecting) */
  reconnectAttempt: number;
  /** Last error message */
  lastError: string | null;
}
