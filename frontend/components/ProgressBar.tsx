'use client'

import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface ProgressBarProps {
  value: number // 0-100
  label?: string
  showPercentage?: boolean
  color?: 'blue' | 'green' | 'amber' | 'rose' | 'purple'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  icon?: string
}

const colorClasses = {
  blue: 'bg-gradient-to-r from-blue-500 to-sky-500',
  green: 'bg-gradient-to-r from-green-500 to-emerald-500',
  amber: 'bg-gradient-to-r from-amber-500 to-orange-500',
  rose: 'bg-gradient-to-r from-rose-500 to-pink-500',
  purple: 'bg-gradient-to-r from-purple-500 to-pink-500'
}

const sizeClasses = {
  sm: 'h-2',
  md: 'h-3',
  lg: 'h-4'
}

export default function ProgressBar({
  value,
  label,
  showPercentage = true,
  color = 'blue',
  size = 'md',
  className = '',
  icon
}: ProgressBarProps) {
  const [animatedValue, setAnimatedValue] = useState(0)

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedValue(Math.min(100, Math.max(0, value)))
    }, 100)
    return () => clearTimeout(timer)
  }, [value])

  return (
    <div className={className}>
      {(label || showPercentage || icon) && (
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {icon && <span className="text-lg">{icon}</span>}
            {label && (
              <span className="text-sm font-medium text-text-secondary">
                {label}
              </span>
            )}
          </div>
          {showPercentage && (
            <span className="text-sm font-bold text-text-primary">
              {Math.round(animatedValue)}%
            </span>
          )}
        </div>
      )}
      
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${animatedValue}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`${colorClasses[color]} ${sizeClasses[size]} rounded-full relative overflow-hidden`}
        >
          {/* Shimmer effect */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30"
            animate={{
              x: ['-100%', '100%']
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        </motion.div>
      </div>
    </div>
  )
}
