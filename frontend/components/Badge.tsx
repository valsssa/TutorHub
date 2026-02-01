"use client";

import { ReactNode } from "react";
import { FiShield } from "react-icons/fi";
import clsx from "clsx";

interface BadgeProps {
  children: ReactNode;
  variant?: "default" | "verified" | "pending" | "rejected" | "approved" | "admin" | "tutor" | "student";
  className?: string;
}

export default function Badge({ children, variant = "default", className }: BadgeProps) {
  const variantStyles = {
    default: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
    verified: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-400 dark:border-emerald-800",
    approved: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-400 dark:border-emerald-800",
    pending: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/50 dark:text-amber-400 dark:border-amber-800",
    rejected: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/50 dark:text-red-400 dark:border-red-800",
    admin: "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/50 dark:text-red-400 dark:border-red-800",
    tutor: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/50 dark:text-blue-400 dark:border-blue-800",
    student: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/50 dark:text-emerald-400 dark:border-emerald-800",
  };

  const showShield = variant === "verified" || variant === "approved";

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        variantStyles[variant],
        className
      )}
    >
      {showShield && (
        <FiShield className="w-3 h-3 mr-1 fill-emerald-500/20" />
      )}
      {children}
    </span>
  );
}
