/**
 * ConnectionStatus Component - Production-Ready WebSocket Status Indicator
 * 
 * KISS Design:
 * - Simple visual indicator for WebSocket connection state
 * - Clear status messages for user understanding
 * - Minimal dependencies
 * - Accessible design (ARIA labels, color + text)
 */

interface ConnectionStatusProps {
  isConnected: boolean;
}

export default function ConnectionStatus({ isConnected }: ConnectionStatusProps) {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white border"
      role="status"
      aria-live="polite"
      aria-label={isConnected ? "Connected to chat" : "Disconnected from chat"}
    >
      {/* Status Indicator Dot */}
      <div
        className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${
          isConnected ? "bg-green-500 animate-pulse" : "bg-gray-400"
        }`}
        aria-hidden="true"
      />

      {/* Status Text */}
      <span
        className={`text-sm font-medium transition-colors duration-300 ${
          isConnected ? "text-green-700" : "text-gray-600"
        }`}
      >
        {isConnected ? "Live" : "Offline"}
      </span>

      {/* Tooltip on hover */}
      <span className="sr-only">
        {isConnected
          ? "Real-time messaging is active"
          : "Reconnecting to real-time messaging..."}
      </span>
    </div>
  );
}
