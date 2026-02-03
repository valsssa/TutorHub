'use client';

import Link from 'next/link';
import { Avatar, Badge } from '@/components/ui';
import type { Conversation } from '@/types';
import { useAuth } from '@/lib/hooks';
import { cn, formatRelativeTime } from '@/lib/utils';

interface ConversationListItemProps {
  conversation: Conversation;
  isActive?: boolean;
}

export function ConversationListItem({
  conversation,
  isActive = false,
}: ConversationListItemProps) {
  const { user } = useAuth();

  const otherParticipant = conversation.participants.find(
    (p) => p.id !== user?.id
  );

  const displayName = otherParticipant
    ? `${otherParticipant.first_name} ${otherParticipant.last_name}`
    : 'Unknown User';

  const lastMessagePreview = conversation.last_message?.content
    ? conversation.last_message.content.length > 50
      ? `${conversation.last_message.content.substring(0, 50)}...`
      : conversation.last_message.content
    : 'No messages yet';

  const timeAgo = conversation.last_message?.created_at
    ? formatRelativeTime(conversation.last_message.created_at)
    : formatRelativeTime(conversation.created_at);

  return (
    <Link
      href={`/messages/${conversation.id}`}
      className={cn(
        'flex items-center gap-3 p-4 rounded-xl transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50',
        isActive && 'bg-primary-50 dark:bg-primary-900/20',
        conversation.unread_count > 0 && 'bg-slate-50 dark:bg-slate-800/30'
      )}
    >
      <Avatar
        src={otherParticipant?.avatar_url}
        name={displayName}
        size="lg"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p
            className={cn(
              'font-medium text-slate-900 dark:text-white truncate',
              conversation.unread_count > 0 && 'font-semibold'
            )}
          >
            {displayName}
          </p>
          <span className="text-xs text-slate-500 dark:text-slate-400 shrink-0">
            {timeAgo}
          </span>
        </div>
        <div className="flex items-center justify-between gap-2 mt-1">
          <p
            className={cn(
              'text-sm truncate',
              conversation.unread_count > 0
                ? 'text-slate-700 dark:text-slate-300 font-medium'
                : 'text-slate-500 dark:text-slate-400'
            )}
          >
            {lastMessagePreview}
          </p>
          {conversation.unread_count > 0 && (
            <Badge variant="primary" className="shrink-0">
              {conversation.unread_count}
            </Badge>
          )}
        </div>
      </div>
    </Link>
  );
}
