import { useState } from "react";
import { FiSend } from "react-icons/fi";
import Button from "@/components/Button";
import TextArea from "@/components/TextArea";

interface MessageInputProps {
  onSend: (message: string) => void;
  onTyping?: () => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export default function MessageInput({
  onSend,
  onTyping,
  disabled = false,
  isLoading = false,
}: MessageInputProps) {
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (!message.trim() || disabled || isLoading) return;
    onSend(message);
    setMessage("");
  };

  return (
    <div className="p-4 bg-gray-50 border-t border-gray-200">
      <div className="flex gap-2">
        <TextArea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            if (e.target.value.length > 0 && onTyping) {
              onTyping();
            }
          }}
          placeholder="Write your message here..."
          minRows={2}
          maxRows={6}
          maxLength={2000}
          showCounter={message.length > 1600}
          onKeyPress={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          className="flex-1"
          disabled={disabled}
          autoResize={true}
        />
        <Button
          variant="primary"
          onClick={handleSend}
          disabled={!message.trim() || disabled || isLoading}
          isLoading={isLoading}
          className="flex-shrink-0"
        >
          <FiSend className="w-4 h-4" />
        </Button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}
