"use client";

import { useState, useEffect } from 'react';
import { FiClock, FiX } from 'react-icons/fi';
import { getRateLimitStatus, clearRateLimitWarning } from '@/hooks/useRateLimitHandler';

export default function RateLimitBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);

  useEffect(() => {
    // Check rate limit status every second
    const interval = setInterval(() => {
      const status = getRateLimitStatus();
      if (status) {
        setIsVisible(true);
        setTimeRemaining(status.retryAfter);
      } else {
        setIsVisible(false);
        setTimeRemaining(0);
      }
    }, 1000);

    // Initial check
    const status = getRateLimitStatus();
    if (status) {
      setIsVisible(true);
      setTimeRemaining(status.retryAfter);
    }

    return () => clearInterval(interval);
  }, []);

  const handleDismiss = () => {
    clearRateLimitWarning();
    setIsVisible(false);
  };

  if (!isVisible) {
    return null;
  }

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 animate-fade-in">
      <div className="bg-gradient-to-r from-red-500 to-orange-500 text-white px-4 py-3 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <FiClock className="w-5 h-5" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm md:text-base">
                ⏱️ Rate Limit Reached
              </p>
              <p className="text-sm text-white/90 mt-0.5">
                Too many requests. Please wait{' '}
                {minutes > 0 && (
                  <span className="font-bold">
                    {minutes} minute{minutes !== 1 ? 's' : ''}
                    {seconds > 0 && ` ${seconds} second${seconds !== 1 ? 's' : ''}`}
                  </span>
                )}
                {minutes === 0 && (
                  <span className="font-bold">
                    {seconds} second{seconds !== 1 ? 's' : ''}
                  </span>
                )}{' '}
                before trying again.
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="flex-shrink-0 p-2 hover:bg-white/10 rounded-lg transition-colors"
            aria-label="Dismiss rate limit warning"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
