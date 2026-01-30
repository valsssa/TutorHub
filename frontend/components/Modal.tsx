"use client";

import { useEffect, useRef, useId } from "react";
import { X } from "lucide-react";
import clsx from "clsx";

type ModalSize = "sm" | "md" | "lg" | "xl" | "full";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  /** Modal size variant */
  size?: ModalSize;
  /** Show close button in header */
  showCloseButton?: boolean;
  /** Allow closing by clicking backdrop */
  closeOnBackdropClick?: boolean;
  /** Custom footer content */
  footer?: React.ReactNode;
  /** Additional class for modal content */
  className?: string;
  /** Prevent body scroll when modal is open */
  preventScroll?: boolean;
}

const sizeClasses: Record<ModalSize, string> = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
  full: "max-w-[calc(100vw-2rem)] sm:max-w-[calc(100vw-4rem)]",
};

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  showCloseButton = true,
  closeOnBackdropClick = true,
  footer,
  className,
  preventScroll = true,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<Element | null>(null);
  const titleId = useId();

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (!isOpen || !preventScroll) return;

    const originalOverflow = document.body.style.overflow;
    const originalPaddingRight = document.body.style.paddingRight;

    // Calculate scrollbar width to prevent layout shift
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;

    document.body.style.overflow = "hidden";
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }

    return () => {
      document.body.style.overflow = originalOverflow;
      document.body.style.paddingRight = originalPaddingRight;
    };
  }, [isOpen, preventScroll]);

  useEffect(() => {
    if (!isOpen) return;

    previouslyFocused.current = document.activeElement;

    const focusable = modalRef.current?.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const first = focusable?.[0];
    // Small delay to ensure modal is rendered
    requestAnimationFrame(() => first?.focus());

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopPropagation();
        onClose();
      }

      if (event.key === "Tab" && focusable && focusable.length > 0) {
        const focusArray = Array.from(focusable).filter((el) => !el.hasAttribute("disabled"));
        const last = focusArray[focusArray.length - 1];
        const current = document.activeElement as HTMLElement;

        if (event.shiftKey) {
          if (current === first || !focusArray.includes(current)) {
            event.preventDefault();
            last?.focus();
          }
        } else if (current === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (previouslyFocused.current instanceof HTMLElement) {
        previouslyFocused.current.focus();
      }
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdropClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={handleBackdropClick}
        aria-hidden="true"
      />

      {/* Modal Container - handles mobile sheet behavior */}
      <div
        ref={modalRef}
        className={clsx(
          // Base styles
          "relative bg-white dark:bg-slate-900 shadow-xl w-full",
          // Mobile: bottom sheet with rounded top
          "rounded-t-2xl sm:rounded-xl",
          // Size constraint
          sizeClasses[size],
          // Height constraints - critical for mobile
          "max-h-[90vh] sm:max-h-[85vh]",
          // Safe area for notched devices
          "pb-safe",
          // Animation
          "animate-in slide-in-from-bottom-full sm:slide-in-from-bottom-2 sm:zoom-in-95 duration-200",
          // Flex layout for proper scroll handling
          "flex flex-col",
          className
        )}
      >
        {/* Header - Sticky */}
        <div className="flex items-center justify-between p-4 sm:p-6 border-b border-slate-200 dark:border-slate-700 shrink-0">
          {/* Mobile drag indicator */}
          <div className="absolute top-2 left-1/2 -translate-x-1/2 w-10 h-1 rounded-full bg-slate-300 dark:bg-slate-600 sm:hidden" />

          <h2
            id={titleId}
            className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white pr-8"
          >
            {title}
          </h2>
          {showCloseButton && (
            <button
              onClick={onClose}
              className="absolute right-4 sm:right-6 top-4 sm:top-6 p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors tap-target touch-manipulation"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5 text-slate-500 dark:text-slate-400" />
            </button>
          )}
        </div>

        {/* Content - Scrollable */}
        <div className="p-4 sm:p-6 overflow-y-auto overscroll-contain flex-1">
          {children}
        </div>

        {/* Footer - Sticky */}
        {footer && (
          <div className="p-4 sm:p-6 border-t border-slate-200 dark:border-slate-700 shrink-0 safe-area-inset-bottom">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
