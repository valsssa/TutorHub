import { SentIcon, DeliveredIcon, ReadIcon } from "./MessageIcons";

interface MessageBubbleProps {
  body: string;
  sender: "user" | "opponent";
  sentAt: string;
  status?: "sent" | "delivered" | "read";
}

export default function MessageBubble({
  body,
  sender,
  sentAt,
  status,
}: MessageBubbleProps) {
  const isFromUser = sender === "user";

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const renderStatusIcon = () => {
    if (!isFromUser || !status) return null;

    switch (status) {
      case "read":
        return <ReadIcon />;
      case "delivered":
        return <DeliveredIcon />;
      case "sent":
        return <SentIcon />;
      default:
        return null;
    }
  };

  return (
    <div className={`flex ${isFromUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-lg p-3 ${
          isFromUser
            ? "bg-primary-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        <p className="text-sm break-words">{body}</p>
        <div
          className={`flex items-center gap-1 mt-1 text-xs ${
            isFromUser ? "text-primary-100" : "text-gray-500"
          }`}
        >
          <span>{formatTime(sentAt)}</span>
          {isFromUser && status && (
            <>
              <span>•</span>
              {renderStatusIcon()}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
