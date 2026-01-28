/**
 * Timezone utilities for global application
 */

import { formatDateTimeInTimezone } from "@/shared/utils/formatters";

export interface TimezoneInfo {
  value: string;
  label: string;
  offset: string;
}

/**
 * Common timezones grouped by region
 */
export const COMMON_TIMEZONES: TimezoneInfo[] = [
  // Americas
  { value: "America/New_York", label: "Eastern Time (US & Canada)", offset: "UTC-5/-4" },
  { value: "America/Chicago", label: "Central Time (US & Canada)", offset: "UTC-6/-5" },
  { value: "America/Denver", label: "Mountain Time (US & Canada)", offset: "UTC-7/-6" },
  { value: "America/Los_Angeles", label: "Pacific Time (US & Canada)", offset: "UTC-8/-7" },
  { value: "America/Anchorage", label: "Alaska", offset: "UTC-9/-8" },
  { value: "Pacific/Honolulu", label: "Hawaii", offset: "UTC-10" },
  { value: "America/Toronto", label: "Toronto", offset: "UTC-5/-4" },
  { value: "America/Mexico_City", label: "Mexico City", offset: "UTC-6/-5" },
  { value: "America/Sao_Paulo", label: "São Paulo", offset: "UTC-3" },
  { value: "America/Buenos_Aires", label: "Buenos Aires", offset: "UTC-3" },
  
  // Europe
  { value: "Europe/London", label: "London", offset: "UTC+0/+1" },
  { value: "Europe/Paris", label: "Paris, Berlin, Rome", offset: "UTC+1/+2" },
  { value: "Europe/Athens", label: "Athens, Helsinki", offset: "UTC+2/+3" },
  { value: "Europe/Moscow", label: "Moscow", offset: "UTC+3" },
  { value: "Europe/Istanbul", label: "Istanbul", offset: "UTC+3" },
  
  // Asia
  { value: "Asia/Dubai", label: "Dubai", offset: "UTC+4" },
  { value: "Asia/Karachi", label: "Karachi", offset: "UTC+5" },
  { value: "Asia/Kolkata", label: "Mumbai, New Delhi", offset: "UTC+5:30" },
  { value: "Asia/Dhaka", label: "Dhaka", offset: "UTC+6" },
  { value: "Asia/Bangkok", label: "Bangkok, Jakarta", offset: "UTC+7" },
  { value: "Asia/Singapore", label: "Singapore", offset: "UTC+8" },
  { value: "Asia/Hong_Kong", label: "Hong Kong", offset: "UTC+8" },
  { value: "Asia/Shanghai", label: "Beijing, Shanghai", offset: "UTC+8" },
  { value: "Asia/Tokyo", label: "Tokyo, Osaka", offset: "UTC+9" },
  { value: "Asia/Seoul", label: "Seoul", offset: "UTC+9" },
  
  // Australia & Pacific
  { value: "Australia/Sydney", label: "Sydney, Melbourne", offset: "UTC+10/+11" },
  { value: "Australia/Perth", label: "Perth", offset: "UTC+8" },
  { value: "Pacific/Auckland", label: "Auckland", offset: "UTC+12/+13" },
  
  // Africa
  { value: "Africa/Cairo", label: "Cairo", offset: "UTC+2" },
  { value: "Africa/Johannesburg", label: "Johannesburg", offset: "UTC+2" },
  { value: "Africa/Nairobi", label: "Nairobi", offset: "UTC+3" },
  { value: "Africa/Lagos", label: "Lagos", offset: "UTC+1" },
  
  // UTC
  { value: "UTC", label: "UTC (Coordinated Universal Time)", offset: "UTC+0" },
];

/**
 * Get user's browser timezone
 */
export function getBrowserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    return "UTC";
  }
}

/**
 * Validate timezone string
 */
export function isValidTimezone(timezone: string): boolean {
  try {
    Intl.DateTimeFormat(undefined, { timeZone: timezone });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Format date in user's timezone
 */
export function formatInUserTimezone(
  utcDate: string | Date,
  timezone: string = "UTC",
): string {
  return formatDateTimeInTimezone(utcDate, timezone);
}

/**
 * Convert local time to UTC for API
 */
export function localToUTC(date: Date): string {
  return date.toISOString();
}

/**
 * Get current time in user's timezone
 */
export function getCurrentTimeInTimezone(timezone: string = "UTC"): string {
  return new Date().toLocaleString("en-US", { timeZone: timezone });
}

/**
 * Get offset string for timezone
 */
export function getTimezoneOffset(timezone: string): string {
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat("en-US", {
      timeZone: timezone,
      timeZoneName: "short",
    });
    const parts = formatter.formatToParts(now);
    const timeZoneName = parts.find((part) => part.type === "timeZoneName");
    return timeZoneName?.value || "UTC";
  } catch (error) {
    return "UTC";
  }
}
