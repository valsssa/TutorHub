"use client";

import clsx from "clsx";
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Play,
  Calendar,
  Ban,
  Timer,
  HelpCircle,
  Shield,
  DollarSign,
  RefreshCw,
  LucideIcon,
} from "lucide-react";

// Session states from the booking system
type SessionState =
  | "REQUESTED"
  | "SCHEDULED"
  | "ACTIVE"
  | "ENDED"
  | "EXPIRED"
  | "CANCELLED";

type SessionOutcome =
  | "COMPLETED"
  | "NOT_HELD"
  | "NO_SHOW_STUDENT"
  | "NO_SHOW_TUTOR"
  | null;

type PaymentState =
  | "PENDING"
  | "AUTHORIZED"
  | "CAPTURED"
  | "VOIDED"
  | "REFUNDED"
  | "PARTIALLY_REFUNDED";

type DisputeState =
  | "NONE"
  | "OPEN"
  | "RESOLVED_UPHELD"
  | "RESOLVED_REFUNDED";

// Generic status for other use cases
type GenericStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "active"
  | "inactive"
  | "verified"
  | "unverified"
  | "warning"
  | "error"
  | "success"
  | "info";

type StatusType =
  | "session"
  | "outcome"
  | "payment"
  | "dispute"
  | "generic"
  | "tutor-approval";

interface StatusConfig {
  label: string;
  icon: LucideIcon;
  colorClasses: string;
  bgClasses: string;
  borderClasses: string;
}

interface StatusBadgeProps {
  /** Status value */
  status: string;
  /** Type of status to determine styling */
  type?: StatusType;
  /** Override the default label */
  label?: string;
  /** Size variant */
  size?: "sm" | "md" | "lg";
  /** Show icon */
  showIcon?: boolean;
  /** Show as pill/rounded */
  variant?: "default" | "pill" | "outline" | "subtle";
  /** Additional className */
  className?: string;
}

// Configuration for session states
const sessionStateConfig: Record<SessionState, StatusConfig> = {
  REQUESTED: {
    label: "Pending",
    icon: Clock,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  SCHEDULED: {
    label: "Scheduled",
    icon: Calendar,
    colorClasses: "text-blue-700 dark:text-blue-300",
    bgClasses: "bg-blue-100 dark:bg-blue-900/30",
    borderClasses: "border-blue-200 dark:border-blue-800",
  },
  ACTIVE: {
    label: "In Progress",
    icon: Play,
    colorClasses: "text-emerald-700 dark:text-emerald-300",
    bgClasses: "bg-emerald-100 dark:bg-emerald-900/30",
    borderClasses: "border-emerald-200 dark:border-emerald-800",
  },
  ENDED: {
    label: "Completed",
    icon: CheckCircle,
    colorClasses: "text-green-700 dark:text-green-300",
    bgClasses: "bg-green-100 dark:bg-green-900/30",
    borderClasses: "border-green-200 dark:border-green-800",
  },
  EXPIRED: {
    label: "Expired",
    icon: Timer,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  CANCELLED: {
    label: "Cancelled",
    icon: XCircle,
    colorClasses: "text-red-700 dark:text-red-300",
    bgClasses: "bg-red-100 dark:bg-red-900/30",
    borderClasses: "border-red-200 dark:border-red-800",
  },
};

// Configuration for session outcomes
const sessionOutcomeConfig: Record<NonNullable<SessionOutcome>, StatusConfig> = {
  COMPLETED: {
    label: "Completed",
    icon: CheckCircle,
    colorClasses: "text-green-700 dark:text-green-300",
    bgClasses: "bg-green-100 dark:bg-green-900/30",
    borderClasses: "border-green-200 dark:border-green-800",
  },
  NOT_HELD: {
    label: "Not Held",
    icon: Ban,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  NO_SHOW_STUDENT: {
    label: "Student No-Show",
    icon: AlertCircle,
    colorClasses: "text-orange-700 dark:text-orange-300",
    bgClasses: "bg-orange-100 dark:bg-orange-900/30",
    borderClasses: "border-orange-200 dark:border-orange-800",
  },
  NO_SHOW_TUTOR: {
    label: "Tutor No-Show",
    icon: AlertCircle,
    colorClasses: "text-red-700 dark:text-red-300",
    bgClasses: "bg-red-100 dark:bg-red-900/30",
    borderClasses: "border-red-200 dark:border-red-800",
  },
};

// Configuration for payment states
const paymentStateConfig: Record<PaymentState, StatusConfig> = {
  PENDING: {
    label: "Pending",
    icon: Clock,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  AUTHORIZED: {
    label: "Authorized",
    icon: Shield,
    colorClasses: "text-blue-700 dark:text-blue-300",
    bgClasses: "bg-blue-100 dark:bg-blue-900/30",
    borderClasses: "border-blue-200 dark:border-blue-800",
  },
  CAPTURED: {
    label: "Paid",
    icon: DollarSign,
    colorClasses: "text-green-700 dark:text-green-300",
    bgClasses: "bg-green-100 dark:bg-green-900/30",
    borderClasses: "border-green-200 dark:border-green-800",
  },
  VOIDED: {
    label: "Voided",
    icon: XCircle,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  REFUNDED: {
    label: "Refunded",
    icon: RefreshCw,
    colorClasses: "text-purple-700 dark:text-purple-300",
    bgClasses: "bg-purple-100 dark:bg-purple-900/30",
    borderClasses: "border-purple-200 dark:border-purple-800",
  },
  PARTIALLY_REFUNDED: {
    label: "Partial Refund",
    icon: RefreshCw,
    colorClasses: "text-purple-700 dark:text-purple-300",
    bgClasses: "bg-purple-100 dark:bg-purple-900/30",
    borderClasses: "border-purple-200 dark:border-purple-800",
  },
};

// Configuration for dispute states
const disputeStateConfig: Record<DisputeState, StatusConfig> = {
  NONE: {
    label: "No Dispute",
    icon: CheckCircle,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  OPEN: {
    label: "Under Review",
    icon: AlertCircle,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  RESOLVED_UPHELD: {
    label: "Upheld",
    icon: Shield,
    colorClasses: "text-blue-700 dark:text-blue-300",
    bgClasses: "bg-blue-100 dark:bg-blue-900/30",
    borderClasses: "border-blue-200 dark:border-blue-800",
  },
  RESOLVED_REFUNDED: {
    label: "Refunded",
    icon: RefreshCw,
    colorClasses: "text-green-700 dark:text-green-300",
    bgClasses: "bg-green-100 dark:bg-green-900/30",
    borderClasses: "border-green-200 dark:border-green-800",
  },
};

// Configuration for generic statuses
const genericStatusConfig: Record<GenericStatus, StatusConfig> = {
  pending: {
    label: "Pending",
    icon: Clock,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  approved: {
    label: "Approved",
    icon: CheckCircle,
    colorClasses: "text-emerald-700 dark:text-emerald-300",
    bgClasses: "bg-emerald-100 dark:bg-emerald-900/30",
    borderClasses: "border-emerald-200 dark:border-emerald-800",
  },
  rejected: {
    label: "Rejected",
    icon: XCircle,
    colorClasses: "text-red-700 dark:text-red-300",
    bgClasses: "bg-red-100 dark:bg-red-900/30",
    borderClasses: "border-red-200 dark:border-red-800",
  },
  active: {
    label: "Active",
    icon: CheckCircle,
    colorClasses: "text-emerald-700 dark:text-emerald-300",
    bgClasses: "bg-emerald-100 dark:bg-emerald-900/30",
    borderClasses: "border-emerald-200 dark:border-emerald-800",
  },
  inactive: {
    label: "Inactive",
    icon: Ban,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  verified: {
    label: "Verified",
    icon: Shield,
    colorClasses: "text-emerald-700 dark:text-emerald-300",
    bgClasses: "bg-emerald-100 dark:bg-emerald-900/30",
    borderClasses: "border-emerald-200 dark:border-emerald-800",
  },
  unverified: {
    label: "Unverified",
    icon: HelpCircle,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  warning: {
    label: "Warning",
    icon: AlertCircle,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  error: {
    label: "Error",
    icon: XCircle,
    colorClasses: "text-red-700 dark:text-red-300",
    bgClasses: "bg-red-100 dark:bg-red-900/30",
    borderClasses: "border-red-200 dark:border-red-800",
  },
  success: {
    label: "Success",
    icon: CheckCircle,
    colorClasses: "text-green-700 dark:text-green-300",
    bgClasses: "bg-green-100 dark:bg-green-900/30",
    borderClasses: "border-green-200 dark:border-green-800",
  },
  info: {
    label: "Info",
    icon: HelpCircle,
    colorClasses: "text-blue-700 dark:text-blue-300",
    bgClasses: "bg-blue-100 dark:bg-blue-900/30",
    borderClasses: "border-blue-200 dark:border-blue-800",
  },
};

// Tutor approval status config
const tutorApprovalConfig: Record<string, StatusConfig> = {
  incomplete: {
    label: "Incomplete",
    icon: AlertCircle,
    colorClasses: "text-slate-600 dark:text-slate-400",
    bgClasses: "bg-slate-100 dark:bg-slate-800",
    borderClasses: "border-slate-200 dark:border-slate-700",
  },
  pending_approval: {
    label: "Pending Review",
    icon: Clock,
    colorClasses: "text-amber-700 dark:text-amber-300",
    bgClasses: "bg-amber-100 dark:bg-amber-900/30",
    borderClasses: "border-amber-200 dark:border-amber-800",
  },
  under_review: {
    label: "Under Review",
    icon: HelpCircle,
    colorClasses: "text-blue-700 dark:text-blue-300",
    bgClasses: "bg-blue-100 dark:bg-blue-900/30",
    borderClasses: "border-blue-200 dark:border-blue-800",
  },
  approved: {
    label: "Approved",
    icon: CheckCircle,
    colorClasses: "text-emerald-700 dark:text-emerald-300",
    bgClasses: "bg-emerald-100 dark:bg-emerald-900/30",
    borderClasses: "border-emerald-200 dark:border-emerald-800",
  },
  rejected: {
    label: "Rejected",
    icon: XCircle,
    colorClasses: "text-red-700 dark:text-red-300",
    bgClasses: "bg-red-100 dark:bg-red-900/30",
    borderClasses: "border-red-200 dark:border-red-800",
  },
};

function getStatusConfig(status: string, type: StatusType): StatusConfig {
  const normalizedStatus = status.toUpperCase();
  const lowerStatus = status.toLowerCase();

  switch (type) {
    case "session":
      return (
        sessionStateConfig[normalizedStatus as SessionState] ||
        genericStatusConfig.info
      );
    case "outcome":
      return (
        sessionOutcomeConfig[normalizedStatus as NonNullable<SessionOutcome>] ||
        genericStatusConfig.info
      );
    case "payment":
      return (
        paymentStateConfig[normalizedStatus as PaymentState] ||
        genericStatusConfig.info
      );
    case "dispute":
      return (
        disputeStateConfig[normalizedStatus as DisputeState] ||
        genericStatusConfig.info
      );
    case "tutor-approval":
      return (
        tutorApprovalConfig[lowerStatus] ||
        genericStatusConfig.info
      );
    case "generic":
    default:
      return (
        genericStatusConfig[lowerStatus as GenericStatus] ||
        genericStatusConfig.info
      );
  }
}

const sizeClasses = {
  sm: "text-xs px-2 py-0.5",
  md: "text-xs px-2.5 py-1",
  lg: "text-sm px-3 py-1.5",
};

const iconSizes = {
  sm: "w-3 h-3",
  md: "w-3.5 h-3.5",
  lg: "w-4 h-4",
};

export default function StatusBadge({
  status,
  type = "generic",
  label,
  size = "md",
  showIcon = true,
  variant = "default",
  className,
}: StatusBadgeProps) {
  const config = getStatusConfig(status, type);
  const Icon = config.icon;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 font-medium",
        sizeClasses[size],
        variant === "pill" && "rounded-full",
        variant === "default" && "rounded-md",
        variant === "outline" && "rounded-md border",
        variant === "subtle" && "rounded-md",
        variant === "outline"
          ? clsx(config.borderClasses, config.colorClasses, "bg-transparent")
          : variant === "subtle"
          ? clsx(config.colorClasses, "bg-transparent")
          : clsx(config.bgClasses, config.colorClasses),
        className
      )}
    >
      {showIcon && <Icon className={iconSizes[size]} aria-hidden="true" />}
      {label || config.label}
    </span>
  );
}

// Export configs for use in other components
export {
  sessionStateConfig,
  sessionOutcomeConfig,
  paymentStateConfig,
  disputeStateConfig,
  genericStatusConfig,
};
