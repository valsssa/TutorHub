import Image from 'next/image'
import {
  getInitials,
  getAvatarColor,
  isPlaceholderUrl,
  getAvatarAltText,
} from '@/lib/avatarUtils'

interface AvatarProps {
  /** Display name for generating initials (supports "First Last" format) */
  name?: string
  /** Optional avatar image URL */
  avatarUrl?: string | null
  /** Size variants */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  /**
   * Color scheme - 'auto' uses deterministic color based on userId/name
   * @default 'auto'
   */
  variant?: 'auto' | 'blue' | 'emerald' | 'purple' | 'orange' | 'gradient'
  /** User ID for deterministic color generation (more stable than name) */
  userId?: string | number
  /** Optional custom className */
  className?: string
  /** Whether to show online indicator */
  showOnline?: boolean
}

const sizeClasses = {
  xs: 'w-8 h-8 text-xs',
  sm: 'w-10 h-10 text-sm',
  md: 'w-12 h-12 text-base',
  lg: 'w-16 h-16 text-xl',
  xl: 'w-20 h-20 text-2xl',
}

const imageSizes = { xs: 32, sm: 40, md: 48, lg: 64, xl: 80 }

const legacyVariantClasses = {
  gradient: 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white',
  blue: 'bg-blue-500 text-white',
  emerald: 'bg-emerald-500 text-white',
  purple: 'bg-purple-500 text-white',
  orange: 'bg-orange-500 text-white',
}

/**
 * Avatar component with automatic initial generation and deterministic colors.
 *
 * Features:
 * - Displays profile image or fallback to initials
 * - Extracts initials from full name ("John Doe" → "JD")
 * - Deterministic color based on userId or name
 * - WCAG AA compliant color contrast
 * - Multiple size variants (xs, sm, md, lg, xl)
 * - Optional online indicator
 * - Dark mode support
 *
 * @example
 * ```tsx
 * // Image avatar
 * <Avatar name="John Doe" avatarUrl="/path/to/image.jpg" size="md" />
 *
 * // Auto-color based on user ID (recommended)
 * <Avatar name="Jane Smith" userId={42} size="lg" />
 *
 * // Auto-color based on name
 * <Avatar name="Bob Wilson" variant="auto" />
 *
 * // Legacy fixed color
 * <Avatar name="Admin" variant="gradient" />
 *
 * // With online indicator
 * <Avatar name="Alice" userId={1} showOnline />
 * ```
 */
export default function Avatar({
  name = 'User',
  avatarUrl = null,
  size = 'md',
  variant = 'auto',
  userId,
  className = '',
  showOnline = false,
}: AvatarProps) {
  const initials = getInitials(name)
  const sizeClass = sizeClasses[size]
  const imageSize = imageSizes[size]
  const altText = getAvatarAltText(name)

  // Determine color classes
  let colorClasses: string
  if (variant === 'auto') {
    // Use deterministic color based on userId or name
    const colorKey = userId ?? name ?? 'unknown'
    const { classes } = getAvatarColor(colorKey)
    colorClasses = `${classes.bg} ${classes.text}`
  } else {
    // Use legacy fixed color variant
    colorClasses = legacyVariantClasses[variant]
  }

  // Check if we should show image or initials
  const shouldShowImage = avatarUrl && !isPlaceholderUrl(avatarUrl)

  // Online indicator component
  const OnlineIndicator = () => (
    <div
      className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white dark:border-slate-900"
      title="Online"
      aria-label="Online"
      role="status"
    >
      <div className="w-full h-full bg-emerald-500 rounded-full animate-pulse" />
    </div>
  )

  if (shouldShowImage) {
    return (
      <div className={`relative inline-block ${className}`}>
        <Image
          src={avatarUrl}
          alt={altText}
          width={imageSize}
          height={imageSize}
          className={`${sizeClass} rounded-full object-cover border border-slate-200 dark:border-slate-700 shadow-sm`}
          loading="lazy"
        />
        {showOnline && <OnlineIndicator />}
      </div>
    )
  }

  return (
    <div className={`relative inline-block ${className}`}>
      <div
        className={`${sizeClass} rounded-full ${colorClasses} flex items-center justify-center font-semibold shadow-sm`}
        role="img"
        aria-label={altText}
      >
        {initials}
      </div>
      {showOnline && <OnlineIndicator />}
    </div>
  )
}
