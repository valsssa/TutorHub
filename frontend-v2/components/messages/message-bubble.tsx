'use client';

import { Avatar } from '@/components/ui';
import type { Message } from '@/types';
import { useAuth } from '@/lib/hooks';
import { cn, formatTime } from '@/lib/utils';

interface MessageBubbleProps {
  message: Message;
  showAvatar?: boolean;
}

export function MessageBubble({ message, showAvatar = true }: MessageBubbleProps) {
  const { user } = useAuth();
  const isSent = message.sender_id === user?.id;

  const senderName = message.sender
    ? `${message.sender.first_name} ${message.sender.last_name}`
    : 'Unknown';

  const formattedTime = formatTime(message.created_at);

  return (
    <div
      className={cn(
        'flex gap-3 max-w-[80%]',
        isSent ? 'ml-auto flex-row-reverse' : 'mr-auto'
      )}
    >
      {showAvatar && !isSent && (
        <Avatar
          src={message.sender?.avatar_url}
          name={senderName}
          size="sm"
          className="shrink-0 mt-1"
        />
      )}
      {showAvatar && isSent && <div className="w-8 shrink-0" />}
      <div
        className={cn(
          'flex flex-col',
          isSent ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'px-4 py-2.5 rounded-2xl',
            isSent
              ? 'bg-primary-500 text-white rounded-br-sm'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-bl-sm'
          )}
        >
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.message}
          </p>
        </div>
        <span
          className={cn(
            'text-xs mt-1 px-1',
            isSent
              ? 'text-slate-400 dark:text-slate-500'
              : 'text-slate-400 dark:text-slate-500'
          )}
        >
          {formattedTime}
        </span>
      </div>
    </div>
  );
}
