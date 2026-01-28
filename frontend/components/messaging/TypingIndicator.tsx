/**
 * TypingIndicator Component - Animated typing indicator
 * 
 * KISS Design:
 * - Simple 3-dot animation
 * - Minimal CSS animation
 * - Accessible (screen reader friendly)
 */

export default function TypingIndicator() {
  return (
    <div
      className="flex items-center gap-2 px-4 py-2"
      role="status"
      aria-live="polite"
      aria-label="Someone is typing"
    >
      <div className="flex items-center gap-1 px-4 py-3 rounded-lg bg-gray-100">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-xs text-gray-500 italic">typing...</span>
    </div>
  );
}
