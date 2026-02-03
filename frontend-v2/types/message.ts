import type { User } from './user';

export interface Conversation {
  id: number;
  participants: User[];
  last_message?: Message;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  is_read: boolean;
  created_at: string;
  sender?: User;
}

export interface SendMessageInput {
  content: string;
}
