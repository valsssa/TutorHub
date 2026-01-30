"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Clock, AlertTriangle, RefreshCw } from "lucide-react";
import Modal from "./Modal";
import Button from "./Button";

interface SessionWarningProps {
  /** Warning threshold in minutes before session expires */
  warningMinutes?: number;
  /** Session duration in minutes */
  sessionDuration?: number;
  /** Called when session is extended */
  onExtend?: () => Promise<void>;
  /** Called when session expires */
  onExpire?: () => void;
  /** Called when user chooses to logout */
  onLogout?: () => void;
  /** Last activity timestamp */
  lastActivity?: number;
}

export default function SessionWarning({
  warningMinutes = 5,
  sessionDuration = 30,
  onExtend,
  onExpire,
  onLogout,
  lastActivity: externalLastActivity,
}: SessionWarningProps) {
  const [showWarning, setShowWarning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [extending, setExtending] = useState(false);
  const lastActivityRef = useRef(Date.now());
  const warningShownRef = useRef(false);

  // Update last activity on user interaction
  const updateActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    // Hide warning if user is active
    if (showWarning && !warningShownRef.current) {
      setShowWarning(false);
    }
  }, [showWarning]);

  // Listen for user activity
  useEffect(() => {
    const events = ["mousedown", "keydown", "scroll", "touchstart"];

    events.forEach((event) => {
      window.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, updateActivity);
      });
    };
  }, [updateActivity]);

  // Check session status periodically
  useEffect(() => {
    const checkSession = () => {
      const now = Date.now();
      const lastActivity = externalLastActivity || lastActivityRef.current;
      const elapsed = (now - lastActivity) / 1000 / 60; // minutes
      const remaining = sessionDuration - elapsed;

      if (remaining <= 0) {
        // Session expired
        setShowWarning(false);
        onExpire?.();
        return;
      }

      if (remaining <= warningMinutes && !showWarning) {
        // Show warning
        setShowWarning(true);
        warningShownRef.current = true;
        setTimeLeft(Math.ceil(remaining * 60)); // Convert to seconds
      }

      if (showWarning && remaining > warningMinutes) {
        // Session was extended
        setShowWarning(false);
        warningShownRef.current = false;
      }
    };

    const interval = setInterval(checkSession, 1000);
    checkSession();

    return () => clearInterval(interval);
  }, [sessionDuration, warningMinutes, showWarning, onExpire, externalLastActivity]);

  // Countdown timer
  useEffect(() => {
    if (!showWarning) return;

    const countdown = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(countdown);
          onExpire?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdown);
  }, [showWarning, onExpire]);

  const handleExtend = async () => {
    setExtending(true);
    try {
      await onExtend?.();
      lastActivityRef.current = Date.now();
      setShowWarning(false);
      warningShownRef.current = false;
    } catch (error) {
      console.error("Failed to extend session:", error);
    } finally {
      setExtending(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!showWarning) return null;

  return (
    <Modal
      isOpen={showWarning}
      onClose={() => {}} // Prevent closing by clicking outside
      title="Session Expiring"
      size="sm"
      closeOnOverlayClick={false}
      showCloseButton={false}
      footer={
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="ghost"
            onClick={onLogout}
            className="flex-1"
          >
            Log Out
          </Button>
          <Button
            onClick={handleExtend}
            isLoading={extending}
            className="flex-1"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Stay Logged In
          </Button>
        </div>
      }
    >
      <div className="flex flex-col items-center text-center">
        {/* Warning Icon */}
        <div className="w-16 h-16 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center mb-4">
          <AlertTriangle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
        </div>

        {/* Countdown */}
        <div className="mb-4">
          <div className="text-4xl font-bold text-slate-900 dark:text-white mb-1">
            {formatTime(timeLeft)}
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            until automatic logout
          </p>
        </div>

        {/* Message */}
        <p className="text-slate-600 dark:text-slate-400">
          Your session is about to expire due to inactivity. Click "Stay Logged In" to continue working.
        </p>

        {/* Progress indicator */}
        <div className="w-full mt-4">
          <div className="h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-amber-500 transition-all duration-1000"
              style={{
                width: `${(timeLeft / (warningMinutes * 60)) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>
    </Modal>
  );
}

// Hook to manage session timeout
export function useSessionTimeout({
  warningMinutes = 5,
  sessionDuration = 30,
  onExpire,
}: {
  warningMinutes?: number;
  sessionDuration?: number;
  onExpire?: () => void;
}) {
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [showWarning, setShowWarning] = useState(false);

  const updateActivity = useCallback(() => {
    setLastActivity(Date.now());
  }, []);

  const extendSession = useCallback(async () => {
    setLastActivity(Date.now());
    setShowWarning(false);
    // In a real app, this would call an API to refresh the session token
  }, []);

  useEffect(() => {
    const checkSession = () => {
      const now = Date.now();
      const elapsed = (now - lastActivity) / 1000 / 60;
      const remaining = sessionDuration - elapsed;

      if (remaining <= 0) {
        onExpire?.();
      } else if (remaining <= warningMinutes && !showWarning) {
        setShowWarning(true);
      }
    };

    const interval = setInterval(checkSession, 10000);
    return () => clearInterval(interval);
  }, [lastActivity, sessionDuration, warningMinutes, showWarning, onExpire]);

  return {
    lastActivity,
    showWarning,
    updateActivity,
    extendSession,
    setShowWarning,
  };
}
