import { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

export interface MessageData {
  id: number;
  sender_id: number;
  recipient_id: number;
  message: string;
  created_at: string;
  is_read: boolean;
  delivery_state?: "sent" | "delivered" | "read";
}

interface MessageListProps {
  messages: MessageData[];
  currentUserId: number;
  showTyping?: boolean;
}

export default function MessageList({
  messages,
  currentUserId,
  showTyping = false,
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, showTyping]);

  const getMessageStatus = (msg: MessageData): "sent" | "delivered" | "read" => {
    if (msg.is_read || msg.delivery_state === "read") {
      return "read";
    }
    if (msg.delivery_state === "delivered") {
      return "delivered";
    }
    return "sent";
  };

  const groupMessagesByDate = (messages: MessageData[]) => {
    const groups: { [key: string]: MessageData[] } = {};

    messages.forEach((msg) => {
      const date = new Date(msg.created_at).toLocaleDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(msg);
    });

    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {Object.entries(messageGroups).map(([date, msgs]) => (
        <div key={date}>
          {/* Date separator */}
          <div className="flex items-center justify-center my-4">
            <div className="bg-gray-200 text-gray-600 text-xs px-3 py-1 rounded-full">
              {date}
            </div>
          </div>

          {/* Messages for this date */}
          <div className="space-y-4">
            {msgs.map((msg) => (
              <MessageBubble
                key={msg.id}
                body={msg.message}
                sender={msg.sender_id === currentUserId ? "user" : "otherUser"}
                sentAt={msg.created_at}
                status={
                  msg.sender_id === currentUserId
                    ? getMessageStatus(msg)
                    : undefined
                }
              />
            ))}
          </div>
        </div>
      ))}

      {/* Typing Indicator */}
      {showTyping && <TypingIndicator />}

      <div ref={messagesEndRef} />
    </div>
  );
}
