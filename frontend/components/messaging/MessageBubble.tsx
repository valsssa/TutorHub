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
            ? "bg-emerald-600 text-white"
            : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100"
        }`}
      >
        <p className="text-sm break-words">{body}</p>
        <div
          className={`flex items-center gap-1 mt-1 text-xs ${
            isFromUser ? "text-emerald-100" : "text-slate-500 dark:text-slate-400"
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
