/**
 * Application-wide constants
 */

import { getApiBaseUrl } from "./url";

// API Configuration
export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL),
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
} as const;

// User Roles
export const ROLES = {
  STUDENT: "student",
  TUTOR: "tutor",
  ADMIN: "admin",
} as const;

export type Role = (typeof ROLES)[keyof typeof ROLES];

// Session State (Four-field booking status system)
// Primary lifecycle state for bookings
export const SESSION_STATE = {
  REQUESTED: "REQUESTED",   // Waiting for tutor response
  SCHEDULED: "SCHEDULED",   // Confirmed, session upcoming
  ACTIVE: "ACTIVE",         // Session happening now
  ENDED: "ENDED",           // Session lifecycle complete
  EXPIRED: "EXPIRED",       // Request timed out (24h)
  CANCELLED: "CANCELLED",   // Explicitly cancelled
} as const;

export type SessionState = (typeof SESSION_STATE)[keyof typeof SESSION_STATE];

// Session Outcome (How the session ended - only for terminal states)
export const SESSION_OUTCOME = {
  COMPLETED: "COMPLETED",       // Session happened successfully
  NOT_HELD: "NOT_HELD",         // Session didn't happen
  NO_SHOW_STUDENT: "NO_SHOW_STUDENT",
  NO_SHOW_TUTOR: "NO_SHOW_TUTOR",
} as const;

export type SessionOutcome = (typeof SESSION_OUTCOME)[keyof typeof SESSION_OUTCOME];

// Payment State
export const PAYMENT_STATE = {
  PENDING: "PENDING",
  AUTHORIZED: "AUTHORIZED",
  CAPTURED: "CAPTURED",
  VOIDED: "VOIDED",
  REFUNDED: "REFUNDED",
  PARTIALLY_REFUNDED: "PARTIALLY_REFUNDED",
} as const;

export type PaymentState = (typeof PAYMENT_STATE)[keyof typeof PAYMENT_STATE];

// Dispute State
export const DISPUTE_STATE = {
  NONE: "NONE",
  OPEN: "OPEN",
  RESOLVED_UPHELD: "RESOLVED_UPHELD",
  RESOLVED_REFUNDED: "RESOLVED_REFUNDED",
} as const;

export type DisputeState = (typeof DISPUTE_STATE)[keyof typeof DISPUTE_STATE];

/**
 * @deprecated Use SESSION_STATE instead. Kept for backward compatibility.
 */
export const BOOKING_STATUS = {
  PENDING: "pending",
  CONFIRMED: "confirmed",
  CANCELLED: "cancelled",
  COMPLETED: "completed",
} as const;

/**
 * @deprecated Use SessionState instead.
 */
export type BookingStatus =
  (typeof BOOKING_STATUS)[keyof typeof BOOKING_STATUS];

// Proficiency Levels
export const PROFICIENCY_LEVELS = {
  BEGINNER: "beginner",
  INTERMEDIATE: "intermediate",
  ADVANCED: "advanced",
  EXPERT: "expert",
} as const;

export type ProficiencyLevel =
  (typeof PROFICIENCY_LEVELS)[keyof typeof PROFICIENCY_LEVELS];

// Validation Rules
export const VALIDATION = {
  PASSWORD_MIN_LENGTH: 6,
  PASSWORD_MAX_LENGTH: 128,
  EMAIL_MAX_LENGTH: 254,
  MAX_BOOKING_HOURS: 8,
} as const;

// UI Constants
export const UI = {
  TOAST_DURATION: 5000,
  DEBOUNCE_DELAY: 300,
  ITEMS_PER_PAGE: 20,
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
} as const;

// Color Schemes for Roles
export const ROLE_COLORS = {
  [ROLES.ADMIN]: {
    bg: "bg-red-100",
    text: "text-red-800",
    border: "border-red-200",
  },
  [ROLES.TUTOR]: {
    bg: "bg-blue-100",
    text: "text-blue-800",
    border: "border-blue-200",
  },
  [ROLES.STUDENT]: {
    bg: "bg-green-100",
    text: "text-green-800",
    border: "border-green-200",
  },
} as const;

// Session State Colors (Four-field system)
export const SESSION_STATE_COLORS = {
  [SESSION_STATE.REQUESTED]: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    border: "border-yellow-200",
  },
  [SESSION_STATE.SCHEDULED]: {
    bg: "bg-green-100",
    text: "text-green-800",
    border: "border-green-200",
  },
  [SESSION_STATE.ACTIVE]: {
    bg: "bg-blue-100",
    text: "text-blue-800",
    border: "border-blue-200",
  },
  [SESSION_STATE.ENDED]: {
    bg: "bg-slate-100",
    text: "text-slate-800",
    border: "border-slate-200",
  },
  [SESSION_STATE.CANCELLED]: {
    bg: "bg-gray-100",
    text: "text-gray-800",
    border: "border-gray-200",
  },
  [SESSION_STATE.EXPIRED]: {
    bg: "bg-orange-100",
    text: "text-orange-800",
    border: "border-orange-200",
  },
} as const;

/**
 * @deprecated Use SESSION_STATE_COLORS instead. Kept for backward compatibility.
 */
export const STATUS_COLORS = {
  [BOOKING_STATUS.PENDING]: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    border: "border-yellow-200",
  },
  [BOOKING_STATUS.CONFIRMED]: {
    bg: "bg-green-100",
    text: "text-green-800",
    border: "border-green-200",
  },
  [BOOKING_STATUS.CANCELLED]: {
    bg: "bg-gray-100",
    text: "text-gray-800",
    border: "border-gray-200",
  },
  [BOOKING_STATUS.COMPLETED]: {
    bg: "bg-blue-100",
    text: "text-blue-800",
    border: "border-blue-200",
  },
} as const;

// Days of Week
export const DAYS_OF_WEEK = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 2, label: "Tuesday" },
  { value: 3, label: "Wednesday" },
  { value: 4, label: "Thursday" },
  { value: 5, label: "Friday" },
  { value: 6, label: "Saturday" },
] as const;

// Routes
export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  REGISTER: "/register",
  DASHBOARD: "/dashboard",
  TUTORS: "/tutors",
  BOOKINGS: "/bookings",
  ADMIN: "/admin",
  TUTOR_PROFILE: "/tutor/profile",
  UNAUTHORIZED: "/unauthorized",
} as const;
