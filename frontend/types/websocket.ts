/**
 * WebSocket message type definitions
 * These types match the backend WebSocket message format from
 * backend/modules/messages/websocket.py
 */

export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  data?: T;
  timestamp?: string;
  _ack_id?: string;
  [key: string]: unknown;
}

/**
 * Server -> Client message types (as sent by backend)
 */
export enum WebSocketMessageType {
  // Connection events
  CONNECTION = "connection",
  PONG = "pong",
  TOKEN_EXPIRED = "token_expired",
  TOKEN_REFRESHED = "token_refreshed",
  ERROR = "error",
  ACK = "ack",

  // Message events
  NEW_MESSAGE = "new_message",
  MESSAGE_SENT = "message_sent",
  MESSAGE_READ = "message_read",
  MESSAGE_EDITED = "message_edited",
  MESSAGE_DELETED = "message_deleted",
  DELIVERY_RECEIPT = "delivery_receipt",

  // User events
  TYPING = "typing",
  PRESENCE_STATUS = "presence_status",

  // Thread events
  THREAD_READ = "thread_read",
}

/**
 * Client -> Server message types
 */
export enum WebSocketClientMessageType {
  PING = "ping",
  ACK = "ack",
  TYPING = "typing",
  MESSAGE_DELIVERED = "message_delivered",
  MESSAGE_READ = "message_read",
  PRESENCE_CHECK = "presence_check",
  REFRESH_TOKEN = "refresh_token",
}

export interface ConnectionData {
  status: "connected";
  user_id: number;
  email: string;
  role: string;
}

export interface NewMessageData {
  message_id: number;
  sender_id: number;
  sender_email: string;
  recipient_id: number;
  booking_id: number | null;
  message: string;
  created_at: string;
  is_read: boolean;
}

export interface MessageSentData {
  message_id: number;
  recipient_id: number;
}

export interface MessageReadData {
  message_id: number;
  reader_id: number;
  read_at?: string;
}

export interface MessageEditedData {
  message_id: number;
  new_content: string;
  edited_at: string;
}

export interface MessageDeletedData {
  message_id: number;
  deleted_by: number;
}

export interface DeliveryReceiptData {
  message_id: number;
  recipient_id: number;
  state: "delivered" | "read";
}

export interface UserTypingData {
  user_id: number;
  user_email: string;
}

export interface PresenceStatusData {
  online_users: number[];
  offline_users: number[];
}

export interface ThreadReadData {
  reader_id: number;
  message_count: number;
}

export interface WebSocketErrorData {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}
