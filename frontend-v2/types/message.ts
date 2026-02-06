import type { User } from './user';

// Backend uses thread-based messaging
export interface MessageThread {
  id?: number;
  other_user_id: number;
  other_user_email: string;
  other_user_first_name?: string;
  other_user_last_name?: string;
  other_user_avatar_url?: string;
  other_user_role: string;
  booking_id?: number;
  last_message: string;
  last_message_time: string;
  last_sender_id: number;
  unread_count: number;
  // Additional fields for conversation compatibility
  participants?: User[];
  created_at?: string;
  updated_at?: string;
}

export interface Message {
  id: number;
  sender_id: number;
  recipient_id?: number;
  message: string; // Message content (backend field name)
  booking_id?: number;
  conversation_id?: number;
  is_read: boolean;
  read_at?: string;
  is_edited?: boolean;
  edited_at?: string;
  created_at: string;
  attachments?: MessageAttachment[];
  sender?: User;
}

export interface MessageAttachment {
  id: number;
  original_filename: string;
  file_size: number;
  mime_type: string;
}

export interface SendMessageInput {
  recipient_id?: number; // Optional when used in conversation context
  message?: string;
  booking_id?: number;
}

export interface PaginatedMessagesResponse {
  messages: Message[];
  total: number;
  page: number;
  page_size: number;
  // Conversation details that may be included in response
  participants?: User[];
  unread_count?: number;
}

export interface UnreadCountResponse {
  total: number;
  by_sender: Record<number, number>;
}

// Conversation type for conversation-based UI
export interface Conversation {
  id: number;
  participants: User[];
  last_message?: Message | string;
  unread_count: number;
  created_at: string;
  updated_at: string;
  // Thread compatibility fields
  other_user_id?: number;
  last_message_time?: string;
}
