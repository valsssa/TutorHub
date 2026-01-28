"use client";

import { useEffect } from "react";
import { FiX, FiCheckCircle, FiAlertCircle, FiInfo } from "react-icons/fi";

export type ToastType = "success" | "error" | "info";

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}

export default function Toast({
  message,
  type,
  onClose,
  duration = 5000,
}: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getStyles = () => {
    switch (type) {
      case "success":
        return "bg-emerald-50 dark:bg-emerald-900/30 border-emerald-500 text-emerald-800 dark:text-emerald-200";
      case "error":
        return "bg-red-50 dark:bg-red-900/30 border-red-500 text-red-800 dark:text-red-200";
      case "info":
        return "bg-blue-50 dark:bg-blue-900/30 border-blue-500 text-blue-800 dark:text-blue-200";
    }
  };

  const getIcon = () => {
    switch (type) {
      case "success":
        return <FiCheckCircle className="w-5 h-5 text-emerald-500" />;
      case "error":
        return <FiAlertCircle className="w-5 h-5 text-red-500" />;
      case "info":
        return <FiInfo className="w-5 h-5 text-blue-500" />;
    }
  };

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg ${getStyles()}`}
      role="alert"
      aria-live="assertive"
    >
      {getIcon()}
      <p className="flex-1 text-sm font-medium">{message}</p>
      <button
        onClick={onClose}
        className="p-1 rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
        aria-label="Dismiss notification"
      >
        <FiX className="w-4 h-4" />
      </button>
    </div>
  );
}
