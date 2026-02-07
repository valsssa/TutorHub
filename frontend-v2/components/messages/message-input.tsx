'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  onSend: (content: string) => void;
  onTyping?: () => void;
  onStopTyping?: () => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

const MAX_ROWS = 4;
const LINE_HEIGHT = 20;
const PADDING_Y = 10;
const MIN_HEIGHT = LINE_HEIGHT + PADDING_Y;
const MAX_HEIGHT = LINE_HEIGHT * MAX_ROWS + PADDING_Y;

export function MessageInput({
  onSend,
  onTyping,
  onStopTyping,
  isLoading = false,
  placeholder = 'Type a message...',
  disabled = false,
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    textarea.style.height = `${Math.min(scrollHeight, MAX_HEIGHT)}px`;
  }, []);

  useEffect(() => {
    adjustHeight();
  }, [message, adjustHeight]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onStopTyping?.();
      onSend(trimmedMessage);
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 sm:gap-3 p-3 sm:p-4 border-t border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
    >
      <div className="flex-1">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            if (e.target.value.trim()) {
              onTyping?.();
            } else {
              onStopTyping?.();
            }
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          style={{ minHeight: MIN_HEIGHT, maxHeight: MAX_HEIGHT }}
          className={cn(
            'flex w-full rounded-xl border bg-white px-4 py-2 text-sm resize-none',
            'border-slate-200 dark:border-slate-700 dark:bg-slate-800',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
            'placeholder:text-slate-400 dark:placeholder:text-slate-500',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'dark:text-white'
          )}
        />
      </div>
      <Button
        type="submit"
        size="icon"
        disabled={!message.trim() || isLoading || disabled}
        loading={isLoading}
        aria-label="Send message"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}
