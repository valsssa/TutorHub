'use client';

import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MoreVertical, AlertCircle, Loader2 } from 'lucide-react';
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
import type { Message } from '@/types';

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
  const conversationId = Number(params.conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasInitialLoad, setHasInitialLoad] = useState(false);

  const { user: currentUser } = useAuth();

  const { data: conversationData, isLoading: conversationLoading, error: conversationError } =
    useConversation(conversationId);
  const { data: messagesData, isLoading: messagesLoading, error: messagesError } =
    useMessages(conversationId, currentPage);
  const sendMessageMutation = useSendMessage(conversationId);
  const markAsReadMutation = useMarkAsRead(conversationId);

  // Calculate if there are more messages to load
  const hasMoreMessages = useMemo(() => {
    if (!messagesData) return false;
    const totalPages = Math.ceil(messagesData.total / messagesData.page_size);
    return currentPage < totalPages;
  }, [messagesData, currentPage]);

  // Merge new messages with existing ones when page changes
  useEffect(() => {
    if (!messagesData?.messages) return;

    if (currentPage === 1) {
      // Initial load or refresh - replace all messages
      setAllMessages(messagesData.messages);
      setHasInitialLoad(true);
    } else {
      // Loading older messages - prepend to existing
      // Older messages come from higher page numbers (reverse chronological)
      setAllMessages(prev => {
        const existingIds = new Set(prev.map(m => m.id));
        const newMessages = messagesData.messages.filter(m => !existingIds.has(m.id));
        return [...newMessages, ...prev];
      });
      setIsLoadingMore(false);
    }
  }, [messagesData, currentPage]);

  // Load older messages handler with scroll position preservation
  const loadOlderMessages = useCallback(() => {
    if (isLoadingMore || !hasMoreMessages) return;

    const container = messagesContainerRef.current;
    if (!container) return;

    // Store current scroll position from top
    const scrollHeightBefore = container.scrollHeight;
    const scrollTopBefore = container.scrollTop;

    setIsLoadingMore(true);
    setCurrentPage(prev => prev + 1);

    // After render, restore scroll position
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (container) {
          const scrollHeightAfter = container.scrollHeight;
          const heightDiff = scrollHeightAfter - scrollHeightBefore;
          container.scrollTop = scrollTopBefore + heightDiff;
        }
      });
    });
  }, [isLoadingMore, hasMoreMessages]);

  // Normalize messages for rendering (sorted by created_at ascending)
  const messages: Message[] = useMemo(() => {
    return [...allMessages].sort((a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
  }, [allMessages]);

  // Get conversation info (may come from conversation endpoint or messages response)
  const conversationParticipants = useMemo(() => {
    // Try to get participants from conversation data first
    if (conversationData?.participants && conversationData.participants.length > 0) {
      return conversationData.participants;
    }
    // Fall back to participants from messages response
    if (messagesData?.participants && messagesData.participants.length > 0) {
      return messagesData.participants;
    }
    return [];
  }, [conversationData, messagesData]);

  const unreadCount = conversationData?.unread_count ?? messagesData?.unread_count ?? 0;

  const otherParticipant = useMemo(() => {
    if (!currentUser) return undefined;
    return conversationParticipants.find((p) => p.id !== currentUser.id);
  }, [conversationParticipants, currentUser]);

  const displayName = otherParticipant
    ? `${otherParticipant.first_name} ${otherParticipant.last_name}`
    : 'Unknown User';

  useEffect(() => {
    if (unreadCount > 0) {
      markAsReadMutation.mutate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, unreadCount]);

  // Auto-scroll to bottom only on initial load or when sending new messages
  useEffect(() => {
    if (hasInitialLoad && currentPage === 1) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages.length, hasInitialLoad, currentPage]);

  const handleSendMessage = (content: string) => {
    sendMessageMutation.mutate({ message: content, recipient_id: conversationId });
  };

  const isLoading = conversationLoading || messagesLoading;
  const hasError = conversationError || messagesError;

  // If user is not authenticated, show loading (auth redirect will happen)
  if (!currentUser) {
    return (
      <div className="h-[calc(100vh-4rem)] sm:h-[calc(100vh-8rem)] flex flex-col">
        <Card className="flex-1 flex flex-col overflow-hidden p-0">
          <div className="flex items-center justify-center h-full">
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] sm:h-[calc(100vh-8rem)] flex flex-col">
      <Card className="flex-1 flex flex-col overflow-hidden p-0">
        <div className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b border-slate-200 dark:border-slate-700">
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

        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4"
        >
          {/* Load older messages button */}
          {hasMoreMessages && hasInitialLoad && (
            <div className="flex justify-center pb-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={loadOlderMessages}
                disabled={isLoadingMore}
                className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
              >
                {isLoadingMore ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  'Load older messages'
                )}
              </Button>
            </div>
          )}

          {messagesLoading && currentPage === 1 ? (
            <MessageSkeleton />
          ) : hasError ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <AlertCircle className="h-12 w-12 text-red-400 mb-3" />
              <p className="text-slate-700 dark:text-slate-300 font-medium">
                Failed to load messages
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Please try refreshing the page
              </p>
            </div>
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
