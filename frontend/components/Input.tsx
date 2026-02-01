"use client";

import { InputHTMLAttributes, forwardRef, useId, useState } from "react";
import clsx from "clsx";
import { Eye, EyeOff, AlertCircle } from "lucide-react";

type InputSize = "sm" | "md" | "lg";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  /** Input label */
  label?: string;
  /** Error message */
  error?: string;
  /** Helper text shown below input */
  helperText?: string;
  /** Size variant */
  size?: InputSize;
  /** Show password toggle for password inputs */
  showPasswordToggle?: boolean;
  /** Left icon or element */
  leftElement?: React.ReactNode;
  /** Right icon or element */
  rightElement?: React.ReactNode;
  /** Full width */
  fullWidth?: boolean;
  /** Loading state */
  isLoading?: boolean;
}

const sizeClasses: Record<InputSize, { input: string; label: string }> = {
  sm: {
    input: "px-3 py-2 text-sm",
    label: "text-xs",
  },
  md: {
    input: "px-4 py-3 text-base",
    label: "text-sm",
  },
  lg: {
    input: "px-4 py-3.5 text-base",
    label: "text-sm",
  },
};

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    label,
    error,
    helperText,
    className,
    id,
    size = "md",
    showPasswordToggle = false,
    leftElement,
    rightElement,
    fullWidth = true,
    isLoading = false,
    type,
    disabled,
    ...props
  },
  ref
) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;
  const helperId = `${inputId}-helper`;

  const [showPassword, setShowPassword] = useState(false);
  const isPasswordInput = type === "password";
  const actualType = isPasswordInput && showPassword ? "text" : type;

  const describedBy = [
    error && errorId,
    helperText && !error && helperId,
  ].filter(Boolean).join(" ") || undefined;

  const sizes = sizeClasses[size];

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
          {props.required && (
            <span className="text-red-500 ml-1" aria-hidden="true">*</span>
          )}
        </label>
      )}

      <div className="relative">
        {/* Left element */}
        {leftElement && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none">
            {leftElement}
          </div>
        )}

        <input
          ref={ref}
          id={inputId}
          type={actualType}
          disabled={disabled || isLoading}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          aria-required={props.required}
          className={clsx(
            // Base styles
            "w-full border rounded-lg transition-all duration-150",
            "bg-slate-50 dark:bg-slate-900",
            "text-slate-900 dark:text-white",
            "placeholder-slate-400 dark:placeholder-slate-500",
            // Focus styles
            "focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500",
            // Size
            sizes.input,
            // Left padding for icon
            leftElement && "pl-10",
            // Right padding for icon/toggle
            (rightElement || (isPasswordInput && showPasswordToggle)) && "pr-10",
            // Error state
            error
              ? "border-red-500 dark:border-red-500 focus:ring-red-500/20 focus:border-red-500"
              : "border-slate-200 dark:border-slate-700",
            // Disabled state
            (disabled || isLoading) && "opacity-60 cursor-not-allowed bg-slate-100 dark:bg-slate-800",
            className
          )}
          {...props}
        />

        {/* Right element / Password toggle */}
        {(rightElement || (isPasswordInput && showPasswordToggle)) && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
            {rightElement}
            {isPasswordInput && showPasswordToggle && (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors p-1 tap-target"
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex={-1}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            )}
          </div>
        )}

        {/* Loading spinner */}
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-slate-300 border-t-emerald-500 rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p
          id={errorId}
          className="mt-1.5 text-sm text-red-600 dark:text-red-400 flex items-start gap-1.5"
          role="alert"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
          <span>{typeof error === "string" ? error : String(error)}</span>
        </p>
      )}

      {/* Helper text */}
      {helperText && !error && (
        <p
          id={helperId}
          className="mt-1.5 text-sm text-slate-500 dark:text-slate-400"
        >
          {helperText}
        </p>
      )}
    </div>
  );
});

export default Input;
