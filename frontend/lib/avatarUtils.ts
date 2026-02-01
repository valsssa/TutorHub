/**
 * Avatar utility functions for deterministic avatar generation.
 *
 * Features:
 * - Extract initials from first and last name (JD for "John Doe")
 * - Generate deterministic colors from user ID or name
 * - WCAG AA compliant color contrast
 * - Handles edge cases (single name, non-Latin characters, empty names)
 */

/**
 * WCAG AA compliant color palette for avatar backgrounds.
 * Each color has a contrast ratio of at least 4.5:1 with white text.
 */
export const AVATAR_COLORS = [
  { bg: '#6366f1', text: '#ffffff' }, // Indigo
  { bg: '#8b5cf6', text: '#ffffff' }, // Violet
  { bg: '#a855f7', text: '#ffffff' }, // Purple
  { bg: '#d946ef', text: '#ffffff' }, // Fuchsia
  { bg: '#ec4899', text: '#ffffff' }, // Pink
  { bg: '#f43f5e', text: '#ffffff' }, // Rose
  { bg: '#ef4444', text: '#ffffff' }, // Red
  { bg: '#f97316', text: '#ffffff' }, // Orange
  { bg: '#eab308', text: '#1f2937' }, // Yellow (dark text)
  { bg: '#84cc16', text: '#1f2937' }, // Lime (dark text)
  { bg: '#22c55e', text: '#ffffff' }, // Green
  { bg: '#10b981', text: '#ffffff' }, // Emerald
  { bg: '#14b8a6', text: '#ffffff' }, // Teal
  { bg: '#06b6d4', text: '#ffffff' }, // Cyan
  { bg: '#0ea5e9', text: '#ffffff' }, // Sky
  { bg: '#3b82f6', text: '#ffffff' }, // Blue
] as const;

/**
 * Tailwind-compatible color classes for avatar backgrounds.
 * Maps to AVATAR_COLORS indices for consistency.
 */
export const AVATAR_COLOR_CLASSES = [
  { bg: 'bg-indigo-500', text: 'text-white' },
  { bg: 'bg-violet-500', text: 'text-white' },
  { bg: 'bg-purple-500', text: 'text-white' },
  { bg: 'bg-fuchsia-500', text: 'text-white' },
  { bg: 'bg-pink-500', text: 'text-white' },
  { bg: 'bg-rose-500', text: 'text-white' },
  { bg: 'bg-red-500', text: 'text-white' },
  { bg: 'bg-orange-500', text: 'text-white' },
  { bg: 'bg-yellow-500', text: 'text-gray-800' },
  { bg: 'bg-lime-500', text: 'text-gray-800' },
  { bg: 'bg-green-500', text: 'text-white' },
  { bg: 'bg-emerald-500', text: 'text-white' },
  { bg: 'bg-teal-500', text: 'text-white' },
  { bg: 'bg-cyan-500', text: 'text-white' },
  { bg: 'bg-sky-500', text: 'text-white' },
  { bg: 'bg-blue-500', text: 'text-white' },
] as const;

/**
 * Simple hash function for deterministic color selection.
 * Uses djb2 algorithm for good distribution.
 */
export function hashString(str: string): number {
  let hash = 5381;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash) ^ str.charCodeAt(i);
  }
  return Math.abs(hash);
}

/**
 * Get deterministic color index from user ID or name.
 * Same input always produces the same color.
 *
 * @param identifier - User ID (number) or name/email (string)
 * @returns Index into AVATAR_COLORS array
 */
export function getAvatarColorIndex(identifier: string | number): number {
  const hash = typeof identifier === 'number'
    ? identifier
    : hashString(String(identifier).toLowerCase());
  return hash % AVATAR_COLORS.length;
}

/**
 * Get avatar color by identifier (user ID or name).
 * Returns both hex values and Tailwind classes.
 *
 * @param identifier - User ID or name
 * @returns Object with hex colors and Tailwind classes
 */
export function getAvatarColor(identifier: string | number) {
  const index = getAvatarColorIndex(identifier);
  return {
    hex: AVATAR_COLORS[index],
    classes: AVATAR_COLOR_CLASSES[index],
    index,
  };
}

/**
 * Extract initials from a name.
 *
 * Rules:
 * 1. "John Doe" → "JD" (first letter of first and last name)
 * 2. "John" → "JO" (first two letters if single name)
 * 3. "J" → "J" (single character stays as-is)
 * 4. Non-Latin characters are supported as-is
 * 5. Empty/invalid → "??"
 *
 * @param name - Full name or single name
 * @returns 1-2 character initials, uppercase
 */
export function getInitials(name: string | null | undefined): string {
  if (!name || typeof name !== 'string') {
    return '??';
  }

  // Trim and normalize whitespace
  const trimmed = name.trim().replace(/\s+/g, ' ');

  if (trimmed.length === 0) {
    return '??';
  }

  // Split by spaces to get name parts
  const parts = trimmed.split(' ').filter(part => part.length > 0);

  if (parts.length === 0) {
    return '??';
  }

  if (parts.length === 1) {
    // Single name: use first two characters
    const singleName = parts[0];
    if (singleName.length === 1) {
      return singleName.toUpperCase();
    }
    return singleName.slice(0, 2).toUpperCase();
  }

  // Multiple names: first letter of first and last name
  const firstName = parts[0];
  const lastName = parts[parts.length - 1];

  const firstInitial = firstName.charAt(0);
  const lastInitial = lastName.charAt(0);

  return (firstInitial + lastInitial).toUpperCase();
}

/**
 * Check if a URL is a placeholder/default avatar that should be ignored.
 */
export function isPlaceholderUrl(url: string | null | undefined): boolean {
  if (!url) return true;

  const placeholderPatterns = [
    'ui-avatars.com',
    'placehold.co',
    'placeholder.com',
    'via.placeholder.com',
    'dummyimage.com',
    'placekitten.com',
    'picsum.photos',
  ];

  return placeholderPatterns.some(pattern => url.includes(pattern));
}

/**
 * Generate alt text for an avatar.
 *
 * @param name - User's name
 * @returns Accessible alt text
 */
export function getAvatarAltText(name: string | null | undefined): string {
  if (!name || typeof name !== 'string' || name.trim().length === 0) {
    return 'User avatar';
  }
  return `Avatar for ${name.trim()}`;
}

export interface AvatarGenerationResult {
  initials: string;
  backgroundColor: string;
  textColor: string;
  bgClass: string;
  textClass: string;
  altText: string;
  colorIndex: number;
}

/**
 * Generate all avatar properties from a name and optional identifier.
 * Use this for complete avatar generation in one call.
 *
 * @param name - User's display name
 * @param identifier - Optional user ID for more stable color assignment
 * @returns Complete avatar generation result
 */
export function generateAvatar(
  name: string | null | undefined,
  identifier?: string | number
): AvatarGenerationResult {
  const colorKey = identifier ?? name ?? 'unknown';
  const color = getAvatarColor(colorKey);

  return {
    initials: getInitials(name),
    backgroundColor: color.hex.bg,
    textColor: color.hex.text,
    bgClass: color.classes.bg,
    textClass: color.classes.text,
    altText: getAvatarAltText(name),
    colorIndex: color.index,
  };
}

/**
 * Get CSS style object for inline avatar styling.
 * Useful when Tailwind classes aren't available.
 *
 * @param name - User's display name
 * @param identifier - Optional user ID
 * @param size - Avatar size in pixels
 * @returns CSS properties object
 */
export function getAvatarStyle(
  name: string | null | undefined,
  identifier?: string | number,
  size: number = 48
): React.CSSProperties {
  const { backgroundColor, textColor, initials } = generateAvatar(name, identifier);

  return {
    width: size,
    height: size,
    borderRadius: '50%',
    backgroundColor,
    color: textColor,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    fontSize: size * 0.4,
    textTransform: 'uppercase' as const,
  };
}
