/**
 * User Identity Display Utilities
 *
 * Centralized utilities for formatting and displaying user names consistently
 * across the application. This is the single source of truth for display name logic.
 *
 * User Identity Contract:
 * - All registered users MUST have first_name and last_name
 * - full_name is computed as "{first_name} {last_name}"
 * - Legacy users with missing names should show email as fallback
 *   but will be prompted to complete their profile
 */

import { User } from "@/types";

/**
 * Format a full name from first and last name.
 *
 * @param firstName - User's first name
 * @param lastName - User's last name
 * @returns Formatted full name or empty string if both are missing
 */
export function formatFullName(
  firstName?: string | null,
  lastName?: string | null
): string {
  const first = firstName?.trim() || "";
  const last = lastName?.trim() || "";

  if (first && last) {
    return `${first} ${last}`;
  }
  if (first) {
    return first;
  }
  if (last) {
    return last;
  }
  return "";
}

/**
 * Get display name for a user with intelligent fallback.
 *
 * Priority:
 * 1. Full name (first + last name)
 * 2. First name only
 * 3. Fallback (usually email or "User")
 *
 * @param user - User object or partial user data
 * @param fallback - Fallback value if no name is available
 * @returns Display name string
 */
export function getDisplayName(
  user: Partial<User> | null | undefined,
  fallback?: string
): string {
  if (!user) {
    return fallback || "User";
  }

  // Check if full_name is already computed by backend
  if (user.full_name?.trim()) {
    return user.full_name.trim();
  }

  // Compute from first_name and last_name
  const fullName = formatFullName(user.first_name, user.last_name);
  if (fullName) {
    return fullName;
  }

  // Fallback to provided value or email
  return fallback || user.email || "User";
}

/**
 * Get user's initials for avatar display.
 *
 * @param user - User object or partial user data
 * @returns 1-2 character initials string
 */
export function getInitials(
  user: Partial<User> | null | undefined
): string {
  if (!user) {
    return "?";
  }

  const first = user.first_name?.trim();
  const last = user.last_name?.trim();

  if (first && last) {
    return `${first[0]}${last[0]}`.toUpperCase();
  }
  if (first) {
    return first[0].toUpperCase();
  }
  if (last) {
    return last[0].toUpperCase();
  }
  if (user.email) {
    return user.email[0].toUpperCase();
  }
  return "?";
}

/**
 * Get greeting name (first name only) for personalized messages.
 *
 * @param user - User object or partial user data
 * @param fallback - Fallback value if no first name is available
 * @returns First name or fallback
 */
export function getGreetingName(
  user: Partial<User> | null | undefined,
  fallback?: string
): string {
  if (!user) {
    return fallback || "there";
  }

  const firstName = user.first_name?.trim();
  if (firstName) {
    return firstName;
  }

  // Fallback to email prefix if no first name
  if (user.email) {
    return user.email.split("@")[0];
  }

  return fallback || "there";
}

/**
 * Check if a user's profile is complete (has required name fields).
 *
 * @param user - User object or partial user data
 * @returns True if profile is complete, false if names are missing
 */
export function isProfileComplete(
  user: Partial<User> | null | undefined
): boolean {
  if (!user) {
    return false;
  }

  // Check the profile_incomplete flag from backend if available
  if (user.profile_incomplete !== undefined) {
    return !user.profile_incomplete;
  }

  // Otherwise check manually
  return Boolean(user.first_name?.trim() && user.last_name?.trim());
}

/**
 * Format tutor or other entity name from various field combinations.
 * Handles both snake_case and camelCase field names.
 *
 * @param entity - Object with name fields
 * @returns Formatted display name
 */
export function formatEntityName(entity: {
  first_name?: string | null;
  last_name?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  name?: string | null;
  title?: string;
  email?: string;
}): string {
  // Try snake_case fields first (API response)
  const firstName = entity.first_name?.trim() || entity.firstName?.trim();
  const lastName = entity.last_name?.trim() || entity.lastName?.trim();

  if (firstName && lastName) {
    return `${firstName} ${lastName}`;
  }
  if (firstName) {
    return firstName;
  }
  if (lastName) {
    return lastName;
  }

  // Fallback to name or title
  if (entity.name?.trim()) {
    return entity.name.trim();
  }
  if (entity.title?.trim()) {
    return entity.title.trim();
  }
  if (entity.email) {
    return entity.email.split("@")[0];
  }

  return "Unknown";
}
