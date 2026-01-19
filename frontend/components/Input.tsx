"use client";

import { InputHTMLAttributes } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export default function Input({
  label,
  error,
  helperText,
  className,
  id,
  ...props
}: InputProps) {
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, "-")}` : crypto.randomUUID());

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-slate-500 dark:text-slate-400 mb-1.5"
        >
          {label}
          {props.required && <span className="text-red-500 ml-1" aria-label="required">*</span>}
        </label>
      )}
      <input
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined}
        aria-required={props.required}
        className={clsx(
          "w-full px-4 py-3 bg-slate-50 dark:bg-slate-950 border rounded-lg focus:outline-none focus:border-emerald-500 transition-colors text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500",
          error 
            ? "border-red-500 dark:border-red-500" 
            : "border-slate-200 dark:border-slate-800",
          className,
        )}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="mt-1.5 text-sm text-red-600 dark:text-red-400" role="alert">
          {typeof error === 'string' ? error : String(error)}
        </p>
      )}
      {helperText && !error && (
        <p id={`${inputId}-helper`} className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">{helperText}</p>
      )}
    </div>
  );
}
