/**
 * EmptyState Component - Messaging Empty State
 * 
 * KISS Design:
 * - Simple, clear message when no conversation is selected
 * - Friendly icon and messaging
 * - Accessible (proper semantic HTML)
 * - Responsive design
 */

import { FiMessageSquare } from "react-icons/fi";

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export default function EmptyState({
  title = "Select a conversation",
  message = "Choose a thread from the left to start messaging",
}: EmptyStateProps) {
  return (
    <div 
      className="flex-1 flex items-center justify-center p-8 bg-gray-50"
      role="status"
      aria-label="No conversation selected"
    >
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-100 dark:bg-emerald-900/30">
            <FiMessageSquare className="w-10 h-10 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          </div>
        </div>

        {/* Title */}
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-3">
          {title}
        </h3>

        {/* Message */}
        <p className="text-slate-600 dark:text-slate-400 text-base leading-relaxed">
          {message}
        </p>

        {/* Optional hint */}
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-4">
          Your messages will appear here once you select a conversation
        </p>
      </div>
    </div>
  );
}
