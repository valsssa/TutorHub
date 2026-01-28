/**
 * React hook for handling rate limit events and displaying user-friendly messages
 */
import { useEffect, useCallback } from 'react';
import { useToast } from '@/components/ToastContainer';
import { RateLimitInfo } from '@/lib/api';

interface RateLimitEvent extends CustomEvent {
  detail: {
    message: string;
    retryAfter: number;
    rateLimitInfo: RateLimitInfo | null;
  };
}

export function useRateLimitHandler() {
  const { showError } = useToast();

  const handleRateLimit = useCallback((event: Event) => {
    const rateLimitEvent = event as RateLimitEvent;
    const { message } = rateLimitEvent.detail;

    // Show toast notification
    showError(message);

    // Log to console for debugging
    console.warn('Rate limit reached:', rateLimitEvent.detail);
  }, [showError]);

  useEffect(() => {
    // Listen for rate limit events
    if (typeof window !== 'undefined') {
      window.addEventListener('rateLimit', handleRateLimit);

      // Check for stored rate limit warning on mount
      const stored = window.localStorage.getItem('rateLimitWarning');
      if (stored) {
        try {
          const warning = JSON.parse(stored);
          const now = Date.now();
          const age = now - warning.timestamp;

          // Only show if less than 5 minutes old
          if (age < 5 * 60 * 1000) {
            showError(warning.message);
          } else {
            // Clear expired warning
            window.localStorage.removeItem('rateLimitWarning');
          }
        } catch (e) {
          // Invalid JSON, clear it
          window.localStorage.removeItem('rateLimitWarning');
        }
      }
    }

    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('rateLimit', handleRateLimit);
      }
    };
  }, [handleRateLimit, showError]);
}

/**
 * Get current rate limit status from localStorage
 */
export function getRateLimitStatus(): {
  isLimited: boolean;
  retryAfter: number;
  message: string;
} | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const stored = window.localStorage.getItem('rateLimitWarning');
  if (!stored) {
    return null;
  }

  try {
    const warning = JSON.parse(stored);
    const now = Date.now();
    const elapsed = (now - warning.timestamp) / 1000; // seconds
    const remaining = Math.max(0, warning.retryAfter - elapsed);

    if (remaining <= 0) {
      // Rate limit expired
      window.localStorage.removeItem('rateLimitWarning');
      return null;
    }

    return {
      isLimited: true,
      retryAfter: Math.ceil(remaining),
      message: warning.message,
    };
  } catch (e) {
    window.localStorage.removeItem('rateLimitWarning');
    return null;
  }
}

/**
 * Clear rate limit warning manually
 */
export function clearRateLimitWarning() {
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem('rateLimitWarning');
  }
}
