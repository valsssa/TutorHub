"use client";

import { TextareaHTMLAttributes, useRef, useEffect, useCallback, useId, forwardRef, useImperativeHandle } from "react";
import clsx from "clsx";
import { AlertCircle } from "lucide-react";

type TextAreaSize = "sm" | "md" | "lg";

interface TextAreaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "size"> {
  /** Clear intent label explaining who will read this and where it appears */
  label?: string;
  /** Error message to display */
  error?: string;
  /** Helper text shown below textarea (below error if both present) */
  helperText?: string;
  /** Maximum character limit - enforced with live counter */
  maxLength?: number;
  /** Minimum character limit for validation */
  minLength?: number;
  /** Show character counter (auto-enabled when maxLength is set) */
  showCounter?: boolean;
  /** Warning threshold percentage (default: 80) */
  warningThreshold?: number;
  /** Minimum number of visible rows (default: 3) */
  minRows?: number;
  /** Maximum number of visible rows before scrolling (default: 10) */
  maxRows?: number;
  /** Enable auto-resize based on content */
  autoResize?: boolean;
  /** Size variant */
  size?: TextAreaSize;
  /** Full width */
  fullWidth?: boolean;
  /** Loading state */
  isLoading?: boolean;
}

const sizeClasses: Record<TextAreaSize, { textarea: string; label: string }> = {
  sm: {
    textarea: "px-3 py-2 text-sm",
    label: "text-xs",
  },
  md: {
    textarea: "px-4 py-3 text-base",
    label: "text-sm",
  },
  lg: {
    textarea: "px-4 py-3.5 text-base",
    label: "text-sm",
  },
};

/**
 * TextArea component following global textarea rules:
 * - Character limits with live counters (warning at 80%, error at 100%)
 * - Clear intent labeling (who reads this + where it appears)
 * - Placeholders describe structure, not content
 * - Auto-resize (min 3 lines, max 10-12 lines, then scroll)
 * - Line height ≥ 1.5 for readability
 * - Accessible with proper labels and ARIA attributes
 */
const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(function TextArea(
  {
    label,
    error,
    helperText,
    className,
    id,
    maxLength,
    minLength,
    showCounter,
    warningThreshold = 80,
    minRows = 3,
    maxRows = 10,
    autoResize = true,
    size = "md",
    fullWidth = true,
    isLoading = false,
    value,
    onChange,
    disabled,
    required,
    ...props
  },
  ref
) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Forward the ref
  useImperativeHandle(ref, () => textareaRef.current!, []);

  const sizes = sizeClasses[size];

  // Calculate character count status
  const currentLength = typeof value === 'string' ? value.length : 0;
  const shouldShowCounter = showCounter || maxLength !== undefined;
  const warningLimit = maxLength ? Math.floor(maxLength * warningThreshold / 100) : 0;
  const isWarning = maxLength ? currentLength >= warningLimit && currentLength < maxLength : false;
  const isAtLimit = maxLength ? currentLength >= maxLength : false;

  // Auto-resize logic
  const adjustHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea || !autoResize) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';

    // Calculate line height (approximation based on font size)
    const computedStyle = window.getComputedStyle(textarea);
    const lineHeight = parseFloat(computedStyle.lineHeight) || 24;
    const paddingTop = parseFloat(computedStyle.paddingTop) || 0;
    const paddingBottom = parseFloat(computedStyle.paddingBottom) || 0;

    const minHeight = (lineHeight * minRows) + paddingTop + paddingBottom;
    const maxHeight = (lineHeight * maxRows) + paddingTop + paddingBottom;

    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
    textarea.style.height = `${newHeight}px`;
  }, [autoResize, minRows, maxRows]);

  // Adjust height on mount and value change
  useEffect(() => {
    adjustHeight();
  }, [value, adjustHeight]);

  // Handle change with maxLength enforcement
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;

    // Enforce maxLength in JS as well (for safety)
    if (maxLength && newValue.length > maxLength) {
      return;
    }

    onChange?.(e);
  };

  // Build aria-describedby for accessibility
  const ariaDescribedBy: string[] = [];
  if (error) ariaDescribedBy.push(`${inputId}-error`);
  if (helperText && !error) ariaDescribedBy.push(`${inputId}-helper`);
  if (shouldShowCounter) ariaDescribedBy.push(`${inputId}-counter`);

  return (
    <div className={clsx("w-full", !fullWidth && "w-auto")}>
      {label && (
        <label
          htmlFor={inputId}
          className={clsx(
            "block font-medium text-slate-700 dark:text-slate-300 mb-1.5",
            sizes.label
          )}
        >
          {label}
          {required && (
            <span className="text-red-500 ml-1" aria-hidden="true">*</span>
          )}
        </label>
      )}
      <div className="relative">
        <textarea
          ref={textareaRef}
          id={inputId}
          value={value}
          onChange={handleChange}
          maxLength={maxLength}
          minLength={minLength}
          rows={minRows}
          disabled={disabled || isLoading}
          required={required}
          aria-invalid={!!error}
          aria-required={required}
          aria-describedby={ariaDescribedBy.length > 0 ? ariaDescribedBy.join(' ') : undefined}
          className={clsx(
            // Base styles with proper line height (≥1.5)
            "w-full border rounded-lg transition-all duration-150",
            "leading-relaxed", // line-height: 1.625
            "bg-slate-50 dark:bg-slate-900",
            "text-slate-900 dark:text-white",
            "placeholder-slate-400 dark:placeholder-slate-500",
            "focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500",
            "resize-none", // Disable manual resize, use auto-resize
            "overflow-y-auto", // Enable scroll when exceeding max height
            // Size
            sizes.textarea,
            // Error state
            error
              ? "border-red-500 dark:border-red-500 focus:ring-red-500/20 focus:border-red-500"
              : "border-slate-200 dark:border-slate-700",
            // Warning state (near limit)
            isWarning && !error && "border-amber-500 dark:border-amber-500 focus:ring-amber-500/20",
            // At limit state
            isAtLimit && !error && "border-red-400 dark:border-red-400",
            // Disabled state
            (disabled || isLoading) && "opacity-60 cursor-not-allowed bg-slate-100 dark:bg-slate-800",
            className,
          )}
          {...props}
        />
        {/* Loading spinner */}
        {isLoading && (
          <div className="absolute right-3 top-3">
            <div className="w-4 h-4 border-2 border-slate-300 border-t-emerald-500 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Character counter */}
      {shouldShowCounter && (
        <p
          id={`${inputId}-counter`}
          className={clsx(
            "mt-1 text-sm text-right",
            isAtLimit ? "text-red-600 dark:text-red-400 font-medium" :
            isWarning ? "text-amber-600 dark:text-amber-400" :
            "text-slate-500 dark:text-slate-400"
          )}
          aria-live="polite"
        >
          {currentLength}{maxLength ? `/${maxLength}` : ''} characters
          {isAtLimit && " (limit reached)"}
        </p>
      )}

      {/* Error message */}
      {error && (
        <p
          id={`${inputId}-error`}
          className="mt-1.5 text-sm text-red-600 dark:text-red-400 flex items-start gap-1.5"
          role="alert"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{typeof error === 'string' ? error : String(error)}</span>
        </p>
      )}

      {/* Helper text (shown when no error) */}
      {helperText && !error && (
        <p
          id={`${inputId}-helper`}
          className="mt-1.5 text-sm text-slate-500 dark:text-slate-400"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

export default TextArea;
