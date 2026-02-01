/**
 * ConnectionStatus Component - Production-Ready WebSocket Status Indicator
 *
 * Features:
 * - Clear visual states: Connected, Connecting, Reconnecting, Offline, Failed
 * - Reconnection attempt counter and progress
 * - Time until next retry display
 * - Manual reconnect button when failed
 * - Network offline detection
 * - Queued message indicator
 * - Accessible design (ARIA labels, color + text)
 */

import { useEffect, useState } from "react";
import type { ConnectionState } from "@/lib/websocket";

interface ConnectionStatusProps {
  isConnected: boolean;
  connectionState?: ConnectionState;
  reconnectAttempts?: number;
  maxReconnectAttempts?: number;
  nextReconnectMs?: number | null;
  queuedMessages?: number;
  isOnline?: boolean;
  onReconnect?: () => void;
  compact?: boolean;
}

export default function ConnectionStatus({
  isConnected,
  connectionState = isConnected ? "connected" : "disconnected",
  reconnectAttempts = 0,
  maxReconnectAttempts = 10,
  nextReconnectMs = null,
  queuedMessages = 0,
  isOnline = true,
  onReconnect,
  compact = false,
}: ConnectionStatusProps) {
  const [countdown, setCountdown] = useState<number | null>(null);

  // Countdown timer for next reconnect
  useEffect(() => {
    if (nextReconnectMs && connectionState === "reconnecting") {
      setCountdown(Math.ceil(nextReconnectMs / 1000));

      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev === null || prev <= 1) {
            clearInterval(interval);
            return null;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    } else {
      setCountdown(null);
    }
  }, [nextReconnectMs, connectionState]);

  // Determine visual state
  const getStateConfig = () => {
    if (!isOnline) {
      return {
        dotClass: "bg-gray-400",
        textClass: "text-gray-600",
        label: "Offline",
        description: "No internet connection",
        showReconnect: false,
        animate: false,
      };
    }

    switch (connectionState) {
      case "connected":
        return {
          dotClass: "bg-green-500",
          textClass: "text-green-700",
          label: "Live",
          description: "Real-time messaging active",
          showReconnect: false,
          animate: true,
        };
      case "connecting":
        return {
          dotClass: "bg-yellow-500",
          textClass: "text-yellow-700",
          label: "Connecting",
          description: "Establishing connection...",
          showReconnect: false,
          animate: true,
        };
      case "reconnecting":
        return {
          dotClass: "bg-yellow-500",
          textClass: "text-yellow-700",
          label: compact ? "Reconnecting" : `Reconnecting (${reconnectAttempts}/${maxReconnectAttempts})`,
          description: countdown
            ? `Retrying in ${countdown}s...`
            : "Attempting to reconnect...",
          showReconnect: false,
          animate: true,
        };
      case "failed":
        return {
          dotClass: "bg-red-500",
          textClass: "text-red-700",
          label: "Connection Failed",
          description: "Could not connect to server",
          showReconnect: true,
          animate: false,
        };
      case "disconnected":
      default:
        return {
          dotClass: "bg-gray-400",
          textClass: "text-gray-600",
          label: "Disconnected",
          description: "Not connected to messaging",
          showReconnect: true,
          animate: false,
        };
    }
  };

  const config = getStateConfig();

  // Compact mode for inline display
  if (compact) {
    return (
      <div
        className="inline-flex items-center gap-1.5"
        role="status"
        aria-live="polite"
        aria-label={config.description}
      >
        <div
          className={`w-2 h-2 rounded-full transition-colors duration-300 ${config.dotClass} ${
            config.animate ? "animate-pulse" : ""
          }`}
          aria-hidden="true"
        />
        <span className={`text-xs font-medium ${config.textClass}`}>
          {config.label}
        </span>
      </div>
    );
  }

  return (
    <div
      className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white border shadow-sm"
      role="status"
      aria-live="polite"
      aria-label={config.description}
    >
      {/* Status Indicator */}
      <div className="flex items-center gap-2">
        <div
          className={`w-2.5 h-2.5 rounded-full transition-colors duration-300 ${config.dotClass} ${
            config.animate ? "animate-pulse" : ""
          }`}
          aria-hidden="true"
        />
        <span
          className={`text-sm font-medium transition-colors duration-300 ${config.textClass}`}
        >
          {config.label}
        </span>
      </div>

      {/* Countdown Timer */}
      {countdown !== null && connectionState === "reconnecting" && (
        <span className="text-xs text-gray-500">
          Retrying in {countdown}s
        </span>
      )}

      {/* Queued Messages Indicator */}
      {queuedMessages > 0 && (
        <span
          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
          title={`${queuedMessages} message${queuedMessages > 1 ? "s" : ""} queued`}
        >
          {queuedMessages} queued
        </span>
      )}

      {/* Reconnect Button */}
      {config.showReconnect && onReconnect && (
        <button
          onClick={onReconnect}
          className="ml-auto px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
          aria-label="Reconnect to messaging"
        >
          Reconnect
        </button>
      )}

      {/* Screen reader description */}
      <span className="sr-only">{config.description}</span>
    </div>
  );
}

/**
 * Minimal status dot for use in headers/nav
 */
export function ConnectionStatusDot({
  isConnected,
  connectionState,
  isOnline = true,
}: Pick<ConnectionStatusProps, "isConnected" | "connectionState" | "isOnline">) {
  const getColor = () => {
    if (!isOnline) return "bg-gray-400";

    switch (connectionState) {
      case "connected":
        return "bg-green-500";
      case "connecting":
      case "reconnecting":
        return "bg-yellow-500";
      case "failed":
        return "bg-red-500";
      default:
        return isConnected ? "bg-green-500" : "bg-gray-400";
    }
  };

  const shouldAnimate =
    isOnline &&
    (connectionState === "connected" ||
      connectionState === "connecting" ||
      connectionState === "reconnecting");

  const getLabel = () => {
    if (!isOnline) return "Offline";
    switch (connectionState) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting";
      case "reconnecting":
        return "Reconnecting";
      case "failed":
        return "Connection failed";
      default:
        return isConnected ? "Connected" : "Disconnected";
    }
  };

  return (
    <div
      className={`w-2 h-2 rounded-full ${getColor()} ${shouldAnimate ? "animate-pulse" : ""}`}
      role="status"
      aria-label={getLabel()}
      title={getLabel()}
    />
  );
}

/**
 * Connection status banner for showing at top of messaging area
 */
export function ConnectionStatusBanner({
  connectionState,
  reconnectAttempts = 0,
  maxReconnectAttempts = 10,
  nextReconnectMs = null,
  isOnline = true,
  onReconnect,
}: Omit<ConnectionStatusProps, "isConnected" | "compact">) {
  const [countdown, setCountdown] = useState<number | null>(null);

  useEffect(() => {
    if (nextReconnectMs && connectionState === "reconnecting") {
      setCountdown(Math.ceil(nextReconnectMs / 1000));

      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev === null || prev <= 1) {
            clearInterval(interval);
            return null;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    } else {
      setCountdown(null);
    }
  }, [nextReconnectMs, connectionState]);

  // Only show banner for problem states
  if (
    isOnline &&
    (connectionState === "connected" || connectionState === "connecting")
  ) {
    return null;
  }

  const getBannerConfig = () => {
    if (!isOnline) {
      return {
        bgClass: "bg-gray-100 border-gray-300",
        textClass: "text-gray-700",
        icon: (
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3"
            />
          </svg>
        ),
        message: "You are offline. Messages will be sent when you reconnect.",
      };
    }

    switch (connectionState) {
      case "reconnecting":
        return {
          bgClass: "bg-yellow-50 border-yellow-300",
          textClass: "text-yellow-800",
          icon: (
            <svg
              className="w-4 h-4 animate-spin"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          ),
          message: countdown
            ? `Reconnecting in ${countdown}s (attempt ${reconnectAttempts}/${maxReconnectAttempts})`
            : `Reconnecting (attempt ${reconnectAttempts}/${maxReconnectAttempts})...`,
        };
      case "failed":
        return {
          bgClass: "bg-red-50 border-red-300",
          textClass: "text-red-800",
          icon: (
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          ),
          message: "Connection failed. Real-time messaging is unavailable.",
        };
      default:
        return {
          bgClass: "bg-gray-50 border-gray-300",
          textClass: "text-gray-700",
          icon: null,
          message: "Disconnected from messaging.",
        };
    }
  };

  const config = getBannerConfig();

  return (
    <div
      className={`flex items-center justify-between px-4 py-2 border-b ${config.bgClass}`}
      role="alert"
    >
      <div className="flex items-center gap-2">
        {config.icon && <span className={config.textClass}>{config.icon}</span>}
        <span className={`text-sm ${config.textClass}`}>{config.message}</span>
      </div>
      {(connectionState === "failed" || connectionState === "disconnected") &&
        isOnline &&
        onReconnect && (
          <button
            onClick={onReconnect}
            className="px-3 py-1 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors"
          >
            Reconnect
          </button>
        )}
    </div>
  );
}
