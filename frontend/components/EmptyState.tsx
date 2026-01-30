"use client";

import { ReactNode } from "react";
import clsx from "clsx";
import {
  Search,
  FileQuestion,
  AlertCircle,
  Inbox,
  MessageSquare,
  Calendar,
  BookOpen,
  Users,
  CreditCard,
  Bell,
  Heart,
  Package,
  LucideIcon,
} from "lucide-react";
import Button from "./Button";

type EmptyStateVariant =
  | "no-data"
  | "no-results"
  | "error"
  | "first-time"
  | "no-messages"
  | "no-bookings"
  | "no-favorites"
  | "no-packages"
  | "no-notifications"
  | "no-students"
  | "no-earnings";

interface EmptyStateAction {
  label: string;
  onClick: () => void;
  variant?: "primary" | "secondary" | "ghost";
}

interface EmptyStateProps {
  /** Predefined variant with default icon and messaging */
  variant?: EmptyStateVariant;
  /** Custom icon (overrides variant icon) */
  icon?: LucideIcon;
  /** Custom icon element (for complex icons) */
  iconElement?: ReactNode;
  /** Main title */
  title: string;
  /** Description text */
  description?: string;
  /** Helpful hint or next steps */
  hint?: string;
  /** Primary action button */
  action?: EmptyStateAction;
  /** Secondary action button */
  secondaryAction?: EmptyStateAction;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Custom className */
  className?: string;
  /** Show illustration background */
  showBackground?: boolean;
}

const variantConfig: Record<
  EmptyStateVariant,
  { icon: LucideIcon; iconColor: string; bgColor: string }
> = {
  "no-data": {
    icon: Inbox,
    iconColor: "text-slate-400 dark:text-slate-500",
    bgColor: "bg-slate-100 dark:bg-slate-800",
  },
  "no-results": {
    icon: Search,
    iconColor: "text-amber-500 dark:text-amber-400",
    bgColor: "bg-amber-100 dark:bg-amber-900/30",
  },
  error: {
    icon: AlertCircle,
    iconColor: "text-red-500 dark:text-red-400",
    bgColor: "bg-red-100 dark:bg-red-900/30",
  },
  "first-time": {
    icon: BookOpen,
    iconColor: "text-emerald-500 dark:text-emerald-400",
    bgColor: "bg-emerald-100 dark:bg-emerald-900/30",
  },
  "no-messages": {
    icon: MessageSquare,
    iconColor: "text-blue-500 dark:text-blue-400",
    bgColor: "bg-blue-100 dark:bg-blue-900/30",
  },
  "no-bookings": {
    icon: Calendar,
    iconColor: "text-purple-500 dark:text-purple-400",
    bgColor: "bg-purple-100 dark:bg-purple-900/30",
  },
  "no-favorites": {
    icon: Heart,
    iconColor: "text-rose-500 dark:text-rose-400",
    bgColor: "bg-rose-100 dark:bg-rose-900/30",
  },
  "no-packages": {
    icon: Package,
    iconColor: "text-indigo-500 dark:text-indigo-400",
    bgColor: "bg-indigo-100 dark:bg-indigo-900/30",
  },
  "no-notifications": {
    icon: Bell,
    iconColor: "text-orange-500 dark:text-orange-400",
    bgColor: "bg-orange-100 dark:bg-orange-900/30",
  },
  "no-students": {
    icon: Users,
    iconColor: "text-cyan-500 dark:text-cyan-400",
    bgColor: "bg-cyan-100 dark:bg-cyan-900/30",
  },
  "no-earnings": {
    icon: CreditCard,
    iconColor: "text-green-500 dark:text-green-400",
    bgColor: "bg-green-100 dark:bg-green-900/30",
  },
};

const sizeConfig = {
  sm: {
    container: "py-6 px-4",
    iconWrapper: "w-12 h-12",
    iconSize: "w-6 h-6",
    title: "text-base",
    description: "text-sm",
    hint: "text-xs",
    gap: "gap-3",
  },
  md: {
    container: "py-10 px-6",
    iconWrapper: "w-16 h-16",
    iconSize: "w-8 h-8",
    title: "text-lg",
    description: "text-base",
    hint: "text-sm",
    gap: "gap-4",
  },
  lg: {
    container: "py-16 px-8",
    iconWrapper: "w-20 h-20",
    iconSize: "w-10 h-10",
    title: "text-xl",
    description: "text-base",
    hint: "text-sm",
    gap: "gap-5",
  },
};

export default function EmptyState({
  variant = "no-data",
  icon,
  iconElement,
  title,
  description,
  hint,
  action,
  secondaryAction,
  size = "md",
  className,
  showBackground = true,
}: EmptyStateProps) {
  const config = variantConfig[variant];
  const sizes = sizeConfig[size];
  const IconComponent = icon || config.icon;

  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center text-center",
        sizes.container,
        sizes.gap,
        className
      )}
      role="status"
      aria-label={title}
    >
      {/* Icon */}
      <div
        className={clsx(
          "rounded-full flex items-center justify-center",
          sizes.iconWrapper,
          showBackground && config.bgColor
        )}
      >
        {iconElement || (
          <IconComponent
            className={clsx(sizes.iconSize, config.iconColor)}
            aria-hidden="true"
          />
        )}
      </div>

      {/* Text Content */}
      <div className="space-y-2 max-w-md">
        <h3
          className={clsx(
            "font-semibold text-slate-900 dark:text-white",
            sizes.title
          )}
        >
          {title}
        </h3>

        {description && (
          <p
            className={clsx(
              "text-slate-600 dark:text-slate-400 leading-relaxed",
              sizes.description
            )}
          >
            {description}
          </p>
        )}

        {hint && (
          <p
            className={clsx(
              "text-slate-500 dark:text-slate-500 mt-2",
              sizes.hint
            )}
          >
            {hint}
          </p>
        )}
      </div>

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3 mt-2">
          {action && (
            <Button
              onClick={action.onClick}
              variant={action.variant || "primary"}
              size={size === "lg" ? "md" : "sm"}
            >
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              onClick={secondaryAction.onClick}
              variant={secondaryAction.variant || "ghost"}
              size={size === "lg" ? "md" : "sm"}
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

// Pre-configured empty states for common use cases
export function NoResultsEmptyState({
  searchQuery,
  onClearSearch,
}: {
  searchQuery?: string;
  onClearSearch?: () => void;
}) {
  return (
    <EmptyState
      variant="no-results"
      title="No results found"
      description={
        searchQuery
          ? `We couldn't find anything matching "${searchQuery}"`
          : "Try adjusting your filters or search terms"
      }
      hint="Check your spelling or try different keywords"
      action={
        onClearSearch
          ? { label: "Clear search", onClick: onClearSearch, variant: "secondary" }
          : undefined
      }
    />
  );
}

export function ErrorEmptyState({
  message,
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      variant="error"
      title="Something went wrong"
      description={message || "We encountered an error loading this content"}
      hint="Please try again or contact support if the problem persists"
      action={
        onRetry
          ? { label: "Try again", onClick: onRetry, variant: "primary" }
          : undefined
      }
    />
  );
}

export function FirstTimeEmptyState({
  featureName,
  description,
  onGetStarted,
}: {
  featureName: string;
  description: string;
  onGetStarted?: () => void;
}) {
  return (
    <EmptyState
      variant="first-time"
      title={`Welcome to ${featureName}`}
      description={description}
      hint="Let's get you started"
      action={
        onGetStarted
          ? { label: "Get started", onClick: onGetStarted, variant: "primary" }
          : undefined
      }
    />
  );
}
