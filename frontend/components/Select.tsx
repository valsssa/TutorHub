"use client";

import { SelectHTMLAttributes, forwardRef, useId } from "react";
import clsx from "clsx";
import { ChevronDown, AlertCircle } from "lucide-react";

type SelectSize = "sm" | "md" | "lg";

interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "children" | "size"> {
  /** Select label */
  label?: string;
  /** Error message */
  error?: string;
  /** Helper text shown below select */
  helperText?: string;
  /** Options to display */
  options: SelectOption[];
  /** Placeholder text */
  placeholder?: string;
  /** Size variant */
  size?: SelectSize;
  /** Full width */
  fullWidth?: boolean;
  /** Loading state */
  isLoading?: boolean;
}

const sizeClasses: Record<SelectSize, { select: string; label: string }> = {
  sm: {
    select: "px-3 py-2 text-sm pr-8",
    label: "text-xs",
  },
  md: {
    select: "px-4 py-3 text-base pr-10",
    label: "text-sm",
  },
  lg: {
    select: "px-4 py-3.5 text-base pr-10",
    label: "text-sm",
  },
};

const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  {
    label,
    error,
    helperText,
    options,
    placeholder,
    className,
    id,
    size = "md",
    fullWidth = true,
    isLoading = false,
    disabled,
    required,
    ...props
  },
  ref
) {
  const generatedId = useId();
  const selectId = id || generatedId;
  const errorId = `${selectId}-error`;
  const helperId = `${selectId}-helper`;

  const describedBy = [
    error && errorId,
    helperText && !error && helperId,
  ].filter(Boolean).join(" ") || undefined;

  const sizes = sizeClasses[size];

  return (
    <div className={clsx("w-full", !fullWidth && "w-auto")}>
      {label && (
        <label
          htmlFor={selectId}
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
        <select
          ref={ref}
          id={selectId}
          disabled={disabled || isLoading}
          required={required}
          aria-invalid={!!error}
          aria-describedby={describedBy}
          aria-required={required}
          className={clsx(
            // Base styles
            "w-full border rounded-lg transition-all duration-150 appearance-none cursor-pointer",
            "bg-slate-50 dark:bg-slate-900",
            "text-slate-900 dark:text-white",
            // Focus styles
            "focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500",
            // Size
            sizes.select,
            // Error state
            error
              ? "border-red-500 dark:border-red-500 focus:ring-red-500/20 focus:border-red-500"
              : "border-slate-200 dark:border-slate-700",
            // Disabled state
            (disabled || isLoading) && "opacity-60 cursor-not-allowed bg-slate-100 dark:bg-slate-800",
            className
          )}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>

        {/* Custom dropdown arrow */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-slate-300 border-t-emerald-500 rounded-full animate-spin" />
          ) : (
            <ChevronDown
              className={clsx(
                "w-4 h-4 transition-colors",
                error
                  ? "text-red-400"
                  : "text-slate-400 dark:text-slate-500"
              )}
              aria-hidden="true"
            />
          )}
        </div>
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

export default Select;
