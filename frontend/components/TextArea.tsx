"use client";

import { TextareaHTMLAttributes } from "react";
import clsx from "clsx";

interface TextAreaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export default function TextArea({
  label,
  error,
  helperText,
  className,
  id,
  ...props
}: TextAreaProps) {
  const inputId = id || (label ? `textarea-${label.toLowerCase().replace(/\s+/g, "-")}` : crypto.randomUUID());

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={clsx(
          "w-full px-3 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors resize-none",
          error ? "border-red-500" : "border-gray-300",
          className,
        )}
        {...props}
      />
      {error && <p className="mt-1 text-sm text-red-600">{typeof error === 'string' ? error : String(error)}</p>}
      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
}
