"use client";

import {
  createContext,
  useContext,
  useState,
  ReactNode,
  useCallback,
} from "react";
import Toast, { ToastType } from "./Toast";

interface ToastMessage {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showSuccess: (message: string) => void;
  showError: (message: string) => void;
  showInfo: (message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

interface ToastProviderProps {
  children: ReactNode;
}

export function ToastProvider({ children }: ToastProviderProps) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [screenReaderMessage, setScreenReaderMessage] = useState<string>("");

  const addToast = useCallback((message: string, type: ToastType) => {
    console.info(`[toast:${type}] ${message}`);
    // keep state empty to suppress UI popups
    setToasts([]);
    setScreenReaderMessage(message);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showSuccess = useCallback(
    (message: string) => addToast(message, "success"),
    [addToast],
  );

  const showError = useCallback(
    (message: string) => addToast(message, "error"),
    [addToast],
  );

  const showInfo = useCallback(
    (message: string) => addToast(message, "info"),
    [addToast],
  );

  return (
    <ToastContext.Provider value={{ showSuccess, showError, showInfo }}>
      {children}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {screenReaderMessage}
      </div>
      {/* Toast UI suppressed by request */}
    </ToastContext.Provider>
  );
}
