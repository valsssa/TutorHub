import Image from 'next/image'

interface AvatarProps {
  /** Display name or email to generate initial from */
  name?: string
  /** Optional avatar image URL */
  avatarUrl?: string | null
  /** Size variants */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  /** Color scheme */
  variant?: 'blue' | 'emerald' | 'purple' | 'orange' | 'gradient'
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

const variantClasses = {
  gradient: 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white',
  blue: 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800',
  emerald: 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800',
  purple: 'bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800',
  orange: 'bg-orange-100 dark:bg-orange-900/50 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-800',
}

/**
 * Avatar component with automatic initial generation
 * 
 * Features:
 * - Displays profile image or fallback to initial
 * - Multiple size variants (xs, sm, md, lg, xl)
 * - Color variants (gradient, blue, emerald, purple, orange)
 * - Optional online indicator
 * - Dark mode support
 * 
 * @example
 * ```tsx
 * // Image avatar
 * <Avatar name="John Doe" avatarUrl="/path/to/image.jpg" size="md" />
 * 
 * // Initial avatar with gradient
 * <Avatar name="Jane Smith" variant="gradient" size="lg" />
 * 
 * // With online indicator
 * <Avatar name="Bob" variant="emerald" showOnline />
 * ```
 */
export default function Avatar({
  name = 'User',
  avatarUrl = null,
  size = 'md',
  variant = 'gradient',
  className = '',
  showOnline = false,
}: AvatarProps) {
  const initial = name?.charAt(0).toUpperCase() || 'U'
  const sizeClass = sizeClasses[size]
  const variantClass = variantClasses[variant]

  // Get numeric size for Image component
  const imageSizes = { xs: 32, sm: 40, md: 48, lg: 64, xl: 80 }
  const imageSize = imageSizes[size]

  if (avatarUrl && !avatarUrl.includes('ui-avatars.com')) {
    return (
      <div className={`relative ${className}`}>
        <Image
          src={avatarUrl}
          alt={name}
          width={imageSize}
          height={imageSize}
          className={`${sizeClass} rounded-full object-cover border border-slate-200 dark:border-slate-700 shadow-sm`}
          unoptimized
        />
        {showOnline && (
          <div
            className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white dark:border-slate-900"
            title="Online"
            aria-label="Online"
            role="status"
          >
            <div className="w-full h-full bg-emerald-500 rounded-full animate-pulse" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <div className={`${sizeClass} rounded-full ${variantClass} flex items-center justify-center font-bold shadow-sm`}>
        {initial}
      </div>
      {showOnline && (
        <div
          className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-white dark:border-slate-900"
          title="Online"
        >
          <div className="w-full h-full bg-emerald-500 rounded-full animate-pulse" />
        </div>
      )}
    </div>
  )
}
