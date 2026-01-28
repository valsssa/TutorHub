/**
 * WebSocket message type definitions
 */

export interface WebSocketMessage<T = unknown> {
  type: WebSocketMessageType;
  data: T;
  timestamp: string;
}

export enum WebSocketMessageType {
  MESSAGE_NEW = 'message:new',
  MESSAGE_READ = 'message:read',
  MESSAGE_DELETED = 'message:deleted',
  USER_TYPING = 'user:typing',
  USER_ONLINE = 'user:online',
  USER_OFFLINE = 'user:offline',
  NOTIFICATION_NEW = 'notification:new',
  BOOKING_UPDATED = 'booking:updated',
  ERROR = 'error',
  PING = 'ping',
  PONG = 'pong',
}

export interface NewMessageData {
  id: number;
  content: string;
  sender_id: number;
  recipient_id: number;
  created_at: string;
  read_at: string | null;
  booking_id?: number | null;
  sender_name?: string;
  sender_avatar?: string;
}

export interface MessageReadData {
  message_id: number;
  read_by: number;
  read_at: string;
}

export interface UserTypingData {
  user_id: number;
  conversation_id: number;
  is_typing: boolean;
}

export interface UserOnlineData {
  user_id: number;
  online: boolean;
  last_seen?: string;
}

export interface NotificationData {
  id: number;
  type: string;
  title: string;
  message: string;
  created_at: string;
  read: boolean;
  data?: Record<string, unknown>;
}

export interface BookingUpdatedData {
  booking_id: number;
  status: string;
  updated_at: string;
}

export interface WebSocketErrorData {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
