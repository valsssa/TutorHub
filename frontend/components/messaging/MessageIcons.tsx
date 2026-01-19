/**
 * MessageIcons Component - Message status indicators
 * 
 * KISS Design:
 * - Simple SVG icons for message states
 * - Clear visual feedback for delivery status
 * - Accessible with proper ARIA labels
 */

export function SentIcon() {
  return (
    <svg
      className="w-4 h-4 text-current"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-label="Message sent"
    >
      <path
        fillRule="evenodd"
        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export function DeliveredIcon() {
  return (
    <svg
      className="w-4 h-4 text-current"
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      aria-label="Message delivered"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 13l4 4L23 7"
      />
    </svg>
  );
}

export function ReadIcon() {
  return (
    <svg
      className="w-4 h-4 text-blue-400"
      viewBox="0 0 20 20"
      fill="currentColor"
      aria-label="Message read"
    >
      <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
      <path
        fillRule="evenodd"
        d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  );
}
