'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MoreVertical } from 'lucide-react';
import {
  useConversation,
  useMessages,
  useSendMessage,
  useMarkAsRead,
  useAuth,
} from '@/lib/hooks';
import {
  Card,
  Avatar,
  Button,
  Skeleton,
} from '@/components/ui';
import { MessageBubble, MessageInput } from '@/components/messages';
import type { Message, Conversation, User } from '@/types';

const mockCurrentUser: User = {
  id: 1,
  email: 'student@example.com',
  first_name: 'John',
  last_name: 'Doe',
  role: 'student',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
};

const mockConversation: Conversation = {
  id: 1,
  participants: [
    mockCurrentUser,
    {
      id: 2,
      email: 'tutor@example.com',
      first_name: 'Sarah',
      last_name: 'Williams',
      role: 'tutor',
      avatar_url: undefined,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
    },
  ],
  unread_count: 0,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: new Date().toISOString(),
};

const mockMessages: Message[] = [
  {
    id: 1,
    conversation_id: 1,
    sender_id: 2,
    content: 'Hi! How can I help you today?',
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    sender: mockConversation.participants[1],
  },
  {
    id: 2,
    conversation_id: 1,
    sender_id: 1,
    content: 'Hi Sarah! I had a question about the calculus homework from our last session.',
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 1.9).toISOString(),
    sender: mockCurrentUser,
  },
  {
    id: 3,
    conversation_id: 1,
    sender_id: 2,
    content: 'Of course! Which problem are you stuck on?',
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 1.8).toISOString(),
    sender: mockConversation.participants[1],
  },
  {
    id: 4,
    conversation_id: 1,
    sender_id: 1,
    content: "Problem 5 about integration by parts. I'm not sure when to use it versus substitution.",
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 1.5).toISOString(),
    sender: mockCurrentUser,
  },
  {
    id: 5,
    conversation_id: 1,
    sender_id: 2,
    content: "Great question! Integration by parts is best when you have a product of two different types of functions - like x*e^x or x*sin(x). The key is to identify which part should be 'u' (the one you differentiate) and which should be 'dv' (the one you integrate).",
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    sender: mockConversation.participants[1],
  },
  {
    id: 6,
    conversation_id: 1,
    sender_id: 2,
    content: 'Would you like me to walk through an example during our next session?',
    is_read: true,
    created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    sender: mockConversation.participants[1],
  },
];

function MessageSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex gap-3 max-w-[70%]">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <Skeleton className="h-16 flex-1 rounded-2xl" />
      </div>
      <div className="flex gap-3 max-w-[70%] ml-auto flex-row-reverse">
        <Skeleton className="h-12 flex-1 rounded-2xl" />
      </div>
      <div className="flex gap-3 max-w-[70%]">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <Skeleton className="h-20 flex-1 rounded-2xl" />
      </div>
    </div>
  );
}

export default function ConversationPage() {
  const params = useParams();
  const router = useRouter();
  const conversationId = Number(params.conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [localMessages, setLocalMessages] = useState<Message[]>(mockMessages);

  const { user } = useAuth();
  const currentUser = user || mockCurrentUser;

  const { data: apiConversation, isLoading: conversationLoading } =
    useConversation(conversationId);
  const { data: apiMessagesData, isLoading: messagesLoading } =
    useMessages(conversationId);
  const sendMessageMutation = useSendMessage(conversationId);
  const markAsReadMutation = useMarkAsRead(conversationId);

  const conversation = apiConversation || mockConversation;
  const messages = apiMessagesData?.items || localMessages;

  const otherParticipant = useMemo(() => {
    return conversation.participants.find((p) => p.id !== currentUser.id);
  }, [conversation.participants, currentUser.id]);

  const displayName = otherParticipant
    ? `${otherParticipant.first_name} ${otherParticipant.last_name}`
    : 'Unknown User';

  useEffect(() => {
    if (conversation.unread_count > 0) {
      markAsReadMutation.mutate();
    }
  }, [conversationId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (content: string) => {
    if (apiMessagesData) {
      sendMessageMutation.mutate({ content });
    } else {
      const newMessage: Message = {
        id: Date.now(),
        conversation_id: conversationId,
        sender_id: currentUser.id,
        content,
        is_read: false,
        created_at: new Date().toISOString(),
        sender: currentUser,
      };
      setLocalMessages((prev) => [...prev, newMessage]);
    }
  };

  const isLoading = conversationLoading || messagesLoading;

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <Card className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex items-center gap-3 p-4 border-b border-slate-200 dark:border-slate-700">
          <Button
            variant="ghost"
            size="icon"
            asChild
            className="lg:hidden"
          >
            <Link href="/messages">
              <ArrowLeft className="h-5 w-5" />
            </Link>
          </Button>

          {conversationLoading ? (
            <div className="flex items-center gap-3 flex-1">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="space-y-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            </div>
          ) : (
            <>
              <Avatar
                src={otherParticipant?.avatar_url}
                name={displayName}
                size="md"
              />
              <div className="flex-1 min-w-0">
                <h2 className="font-semibold text-slate-900 dark:text-white truncate">
                  {displayName}
                </h2>
                <p className="text-sm text-slate-500 dark:text-slate-400 capitalize">
                  {otherParticipant?.role || 'User'}
                </p>
              </div>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-5 w-5" />
              </Button>
            </>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messagesLoading ? (
            <MessageSkeleton />
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <p className="text-slate-500 dark:text-slate-400">
                No messages yet
              </p>
              <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
                Send a message to start the conversation
              </p>
            </div>
          ) : (
            <>
              {messages.map((message, index) => {
                const prevMessage = messages[index - 1];
                const showAvatar =
                  !prevMessage || prevMessage.sender_id !== message.sender_id;

                return (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    showAvatar={showAvatar}
                  />
                );
              })}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <MessageInput
          onSend={handleSendMessage}
          isLoading={sendMessageMutation.isPending}
          disabled={isLoading}
        />
      </Card>
    </div>
  );
}
