'use client';

import { useState, useMemo } from 'react';
import { MessageCircle, Search, AlertCircle } from 'lucide-react';
import { useConversations } from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Skeleton,
} from '@/components/ui';
import { ConversationListItem } from '@/components/messages';
import type { Conversation } from '@/types';

function ConversationSkeleton() {
  return (
    <div className="flex items-center gap-3 p-4">
      <Skeleton className="h-12 w-12 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
}

export default function MessagesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const { data: conversations, isLoading, error } = useConversations();

  // Transform MessageThread[] to Conversation[] if needed
  const normalizedConversations = useMemo(() => {
    if (!conversations) return [];
    return conversations.map((thread) => {
      // If it's already a Conversation type, return as-is
      if ('participants' in thread && Array.isArray(thread.participants) && thread.participants.length > 0) {
        return thread as Conversation;
      }
      // Transform MessageThread to Conversation
      const conv: Conversation = {
        id: thread.other_user_id ?? thread.id ?? 0,
        participants: thread.participants ?? [
          {
            id: thread.other_user_id ?? 0,
            email: thread.other_user_email ?? '',
            first_name: thread.other_user_first_name ?? '',
            last_name: thread.other_user_last_name ?? '',
            role: (thread.other_user_role ?? 'student') as 'student' | 'tutor' | 'admin' | 'owner',
            avatar_url: thread.other_user_avatar_url,
            is_active: true,
            created_at: thread.created_at ?? new Date().toISOString(),
          },
        ],
        last_message: thread.last_message,
        unread_count: thread.unread_count ?? 0,
        created_at: thread.created_at ?? new Date().toISOString(),
        updated_at: thread.updated_at ?? thread.last_message_time ?? new Date().toISOString(),
        other_user_id: thread.other_user_id,
      };
      return conv;
    });
  }, [conversations]);

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return normalizedConversations;

    const query = searchQuery.toLowerCase();
    return normalizedConversations.filter((conv) => {
      const participants = conv.participants ?? [];
      const participantNames = participants
        .map((p) => `${p.first_name} ${p.last_name}`.toLowerCase())
        .join(' ');
      // Handle last_message which could be string, Message object, or undefined
      let lastMessageContent = '';
      if (typeof conv.last_message === 'string') {
        lastMessageContent = conv.last_message.toLowerCase();
      } else if (conv.last_message && typeof conv.last_message === 'object') {
        lastMessageContent = (conv.last_message.content || '').toLowerCase();
      }

      return participantNames.includes(query) || lastMessageContent.includes(query);
    });
  }, [normalizedConversations, searchQuery]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          Messages
        </h1>
        <p className="text-slate-500 dark:text-slate-400">
          Chat with your tutors and students
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conversations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex h-10 w-full rounded-xl border bg-white pl-10 pr-4 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500 dark:text-white"
              />
            </div>
          </div>

          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {isLoading ? (
              <>
                <ConversationSkeleton />
                <ConversationSkeleton />
                <ConversationSkeleton />
              </>
            ) : error ? (
              <div className="text-center py-12">
                <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-3" />
                <p className="text-slate-700 dark:text-slate-300 font-medium">
                  Failed to load conversations
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  Please try refreshing the page
                </p>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="text-center py-12">
                <MessageCircle className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 dark:text-slate-400">
                  {searchQuery
                    ? 'No conversations match your search'
                    : 'No conversations yet'}
                </p>
                {!searchQuery && (
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
                    Start a conversation by booking a session with a tutor
                  </p>
                )}
              </div>
            ) : (
              filteredConversations.map((conversation) => (
                <ConversationListItem
                  key={conversation.id}
                  conversation={conversation}
                />
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
