'use client';

import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MoreVertical, AlertCircle, Loader2, WifiOff } from 'lucide-react';
import {
  useConversation,
  useMessages,
  useSendMessage,
  useMarkAsRead,
  useAuth,
  useRealtimeMessages,
  useTypingIndicator,
} from '@/lib/hooks';
import {
  Card,
  Avatar,
  Button,
  Skeleton,
} from '@/components/ui';
import { MessageBubble, MessageInput } from '@/components/messages';
import type { Message } from '@/types';
import type { NewMessageMessage } from '@/types/websocket';

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

  // Scroll to bottom helper
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior });
    });
  }, []);

  // Determine the other participant's user ID for real-time features
  const otherParticipantId = useMemo(() => {
    if (!currentUser) return undefined;
    const participants =
      conversationData?.participants ?? messagesData?.participants ?? [];
    const other = participants.find((p) => p.id !== currentUser.id);
    return other?.id;
  }, [currentUser, conversationData, messagesData]);

  // Ref to hold markAsRead so onNewMessage callback doesn't create circular dependency
  const wsMarkAsReadRef = useRef<(messageId: number) => void>(() => {});

  // Handle incoming real-time messages
  const handleNewMessage = useCallback(
    (msg: NewMessageMessage) => {
      const newMessage: Message = {
        id: msg.message_id,
        sender_id: msg.sender_id,
        recipient_id: msg.recipient_id,
        message: msg.content,
        booking_id: msg.booking_id,
        conversation_id: msg.conversation_id,
        is_read: false,
        created_at: msg.created_at,
      };

      setAllMessages((prev) => {
        const exists = prev.some((m) => m.id === newMessage.id);
        if (exists) return prev;
        return [...prev, newMessage];
      });

      // Mark incoming messages as read immediately if from the other user
      if (msg.sender_id !== currentUser?.id) {
        wsMarkAsReadRef.current(msg.message_id);
      }

      // Auto-scroll to the new message
      scrollToBottom();
    },
    [currentUser?.id, scrollToBottom]
  );

  // Real-time messaging via WebSocket
  const {
    isConnected,
    isReconnecting,
    isUserOnline,
    isUserTyping,
    sendTyping,
    markAsRead: wsMarkAsRead,
    error: wsError,
    reconnect,
  } = useRealtimeMessages({
    conversationId,
    otherUserId: otherParticipantId,
    onNewMessage: handleNewMessage,
    enabled: !!currentUser,
  });

  // Keep the ref in sync with the latest markAsRead function
  useEffect(() => {
    wsMarkAsReadRef.current = wsMarkAsRead;
  }, [wsMarkAsRead]);

  // Typing indicator with debounce
  const { startTyping, stopTyping } = useTypingIndicator(sendTyping);

  // Calculate if there are more messages to load
  const hasMoreMessages = useMemo(() => {
    if (!messagesData) return false;
    const totalPages = Math.ceil(messagesData.total / messagesData.page_size);
    return currentPage < totalPages;
  }, [messagesData, currentPage]);

  // Merge new messages with existing ones when page data changes
  useEffect(() => {
    if (!messagesData?.messages) return;

    if (currentPage === 1) {
      if (!hasInitialLoad) {
        // First load - set all messages
        setAllMessages(messagesData.messages);
        setHasInitialLoad(true);
      } else {
        // Page 1 cache was updated (e.g. by WebSocket or refetch)
        // Merge with existing older messages to avoid losing loaded pages
        setAllMessages((prev) => {
          const freshIds = new Set(messagesData.messages.map((m) => m.id));
          // Keep older messages that aren't in the fresh page 1 data
          const olderMessages = prev.filter((m) => !freshIds.has(m.id));
          return [...olderMessages, ...messagesData.messages];
        });
      }
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
  }, [messagesData, currentPage, hasInitialLoad]);

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
      <div className="h-[calc(100dvh-4rem)] sm:h-[calc(100dvh-8rem)] flex flex-col">
        <Card className="flex-1 flex flex-col overflow-hidden p-0">
          <div className="flex items-center justify-center h-full">
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-[calc(100dvh-4rem)] sm:h-[calc(100dvh-8rem)] flex flex-col">
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
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {otherParticipantId && isUserTyping(otherParticipantId) ? (
                    <span className="text-primary-500 dark:text-primary-400">typing...</span>
                  ) : otherParticipantId && isUserOnline(otherParticipantId) ? (
                    <span className="flex items-center gap-1.5">
                      <span className="inline-block h-2 w-2 rounded-full bg-green-500" />
                      Online
                    </span>
                  ) : (
                    <span className="capitalize">{otherParticipant?.role || 'User'}</span>
                  )}
                </p>
              </div>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-5 w-5" />
              </Button>
            </>
          )}
        </div>

        {/* Connection status banner */}
        {!isConnected && (
          <div className="flex items-center justify-center gap-2 px-3 py-2 text-sm bg-amber-50 dark:bg-amber-900/20 border-b border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400">
            {isReconnecting ? (
              <>
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span>Reconnecting...</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5" />
                <span>Disconnected{wsError ? ` - ${wsError}` : ''}</span>
                <button
                  onClick={reconnect}
                  className="ml-1 underline font-medium hover:text-amber-900 dark:hover:text-amber-300"
                >
                  Retry
                </button>
              </>
            )}
          </div>
        )}

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
              {/* Typing indicator */}
              {otherParticipantId && isUserTyping(otherParticipantId) && (
                <div className="flex gap-2 sm:gap-3 max-w-[90%] sm:max-w-[80%] md:max-w-[70%] mr-auto">
                  <div className="flex items-center gap-1 px-4 py-2.5 rounded-2xl bg-slate-100 dark:bg-slate-800 rounded-bl-sm">
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:0ms]" />
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:150ms]" />
                    <span className="inline-block h-1.5 w-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <MessageInput
          onSend={handleSendMessage}
          onTyping={startTyping}
          onStopTyping={stopTyping}
          isLoading={sendMessageMutation.isPending}
          disabled={isLoading}
        />
      </Card>
    </div>
  );
}
