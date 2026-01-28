/**
 * Formatting utilities for dates, currency, etc.
 */

/**
 * Get locale for currency based on currency code
 */
function getLocaleForCurrency(currency: string): string {
  const localeMap: Record<string, string> = {
    USD: "en-US",
    EUR: "de-DE",
    GBP: "en-GB",
    JPY: "ja-JP",
    CNY: "zh-CN",
    INR: "en-IN",
    CAD: "en-CA",
    AUD: "en-AU",
    CHF: "de-CH",
    SEK: "sv-SE",
    NOK: "nb-NO",
    DKK: "da-DK",
    PLN: "pl-PL",
    RUB: "ru-RU",
    BRL: "pt-BR",
    MXN: "es-MX",
    ZAR: "en-ZA",
    KRW: "ko-KR",
    SGD: "en-SG",
    NZD: "en-NZ",
  };
  return localeMap[currency] || "en-US";
}

/**
 * Format currency value with automatic locale detection
 */
export function formatCurrency(
  amount: number | string,
  currency: string = "USD",
  locale?: string,
): string {
  const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  const effectiveLocale = locale || getLocaleForCurrency(currency);

  return new Intl.NumberFormat(effectiveLocale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numAmount);
}

/**
 * Format date to localized string with timezone support
 */
export function formatDate(
  date: string | Date,
  timezone?: string,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  },
): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  const formatOptions = timezone ? { ...options, timeZone: timezone } : options;
  return new Intl.DateTimeFormat("en-US", formatOptions).format(dateObj);
}

/**
 * Format time to localized string with timezone support
 */
export function formatTime(date: string | Date, timezone?: string): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  const options: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
  };
  if (timezone) {
    options.timeZone = timezone;
  }
  return new Intl.DateTimeFormat("en-US", options).format(dateObj);
}

/**
 * Format date and time with timezone support
 */
export function formatDateTime(date: string | Date, timezone?: string): string {
  return `${formatDate(date, timezone)} at ${formatTime(date, timezone)}`;
}

/**
 * Convert UTC time to user's timezone and format
 */
export function formatDateTimeInTimezone(
  utcDate: string | Date,
  timezone: string = "UTC",
): string {
  const dateObj = typeof utcDate === "string" ? new Date(utcDate) : utcDate;
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: timezone,
    timeZoneName: "short",
  }).format(dateObj);
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600)
    return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400)
    return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 2592000)
    return `${Math.floor(diffInSeconds / 86400)} days ago`;
  if (diffInSeconds < 31536000)
    return `${Math.floor(diffInSeconds / 2592000)} months ago`;
  return `${Math.floor(diffInSeconds / 31536000)} years ago`;
}

/**
 * Calculate duration in hours
 */
export function calculateDuration(
  start: string | Date,
  end: string | Date,
): number {
  const startDate = typeof start === "string" ? new Date(start) : start;
  const endDate = typeof end === "string" ? new Date(end) : end;
  const diffInMs = endDate.getTime() - startDate.getTime();
  return diffInMs / (1000 * 60 * 60);
}

/**
 * Format duration as human-readable string
 */
export function formatDuration(hours: number): string {
  if (hours < 1) {
    const minutes = Math.round(hours * 60);
    return `${minutes} minute${minutes !== 1 ? "s" : ""}`;
  }

  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);

  if (minutes === 0) {
    return `${wholeHours} hour${wholeHours !== 1 ? "s" : ""}`;
  }

  return `${wholeHours}h ${minutes}m`;
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Truncate text with ellipsis
 */
export function truncate(
  str: string,
  maxLength: number,
  suffix: string = "...",
): string {
  if (!str || str.length <= maxLength) return str;
  return str.substring(0, maxLength - suffix.length) + suffix;
}

/**
 * Format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}
