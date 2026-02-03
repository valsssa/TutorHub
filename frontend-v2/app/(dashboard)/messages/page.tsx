'use client';

import { useState, useMemo } from 'react';
import { MessageCircle, Search } from 'lucide-react';
import { useConversations } from '@/lib/hooks';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Input,
  Skeleton,
} from '@/components/ui';
import { ConversationListItem } from '@/components/messages';
import type { Conversation, User } from '@/types';

const mockConversations: Conversation[] = [
  {
    id: 1,
    participants: [
      {
        id: 1,
        email: 'student@example.com',
        first_name: 'John',
        last_name: 'Doe',
        role: 'student',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        email: 'tutor1@example.com',
        first_name: 'Sarah',
        last_name: 'Williams',
        role: 'tutor',
        avatar_url: undefined,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
    last_message: {
      id: 101,
      conversation_id: 1,
      sender_id: 2,
      content: 'Great progress today! Keep practicing those problems.',
      is_read: false,
      created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    unread_count: 2,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: 2,
    participants: [
      {
        id: 1,
        email: 'student@example.com',
        first_name: 'John',
        last_name: 'Doe',
        role: 'student',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 3,
        email: 'tutor2@example.com',
        first_name: 'Michael',
        last_name: 'Chen',
        role: 'tutor',
        avatar_url: undefined,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
    last_message: {
      id: 102,
      conversation_id: 2,
      sender_id: 1,
      content: 'Thank you for the session!',
      is_read: true,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    },
    unread_count: 0,
    created_at: '2024-01-10T14:00:00Z',
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
  },
  {
    id: 3,
    participants: [
      {
        id: 1,
        email: 'student@example.com',
        first_name: 'John',
        last_name: 'Doe',
        role: 'student',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 4,
        email: 'tutor3@example.com',
        first_name: 'Emily',
        last_name: 'Johnson',
        role: 'tutor',
        avatar_url: undefined,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ],
    last_message: {
      id: 103,
      conversation_id: 3,
      sender_id: 4,
      content: 'Let me know if you have any questions about the homework.',
      is_read: true,
      created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    },
    unread_count: 0,
    created_at: '2024-01-05T09:00:00Z',
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
  },
];

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
  const { data: apiConversations, isLoading } = useConversations();

  const conversations = apiConversations || mockConversations;

  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;

    const query = searchQuery.toLowerCase();
    return conversations.filter((conv) => {
      const participantNames = conv.participants
        .map((p) => `${p.first_name} ${p.last_name}`.toLowerCase())
        .join(' ');
      const lastMessage = conv.last_message?.content.toLowerCase() || '';

      return participantNames.includes(query) || lastMessage.includes(query);
    });
  }, [conversations, searchQuery]);

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
