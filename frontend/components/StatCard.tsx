'use client'

import { motion } from 'framer-motion'
import { IconType } from 'react-icons'

interface StatCardProps {
  label: string
  value: string | number
  icon: IconType
  color?: 'blue' | 'green' | 'yellow' | 'purple' | 'rose' | 'amber'
  delta?: {
    value: string
    trend: 'up' | 'down' | 'neutral'
  }
  onClick?: () => void
  className?: string
}

const colorClasses = {
  blue: {
    bg: 'bg-gradient-to-br from-blue-50 to-sky-50',
    icon: 'text-blue-600',
    iconBg: 'bg-blue-100',
    hover: 'hover:shadow-lg hover:border-blue-200'
  },
  green: {
    bg: 'bg-gradient-to-br from-green-50 to-emerald-50',
    icon: 'text-green-600',
    iconBg: 'bg-green-100',
    hover: 'hover:shadow-lg hover:border-green-200'
  },
  yellow: {
    bg: 'bg-gradient-to-br from-yellow-50 to-amber-50',
    icon: 'text-yellow-600',
    iconBg: 'bg-yellow-100',
    hover: 'hover:shadow-lg hover:border-yellow-200'
  },
  purple: {
    bg: 'bg-gradient-to-br from-purple-50 to-pink-50',
    icon: 'text-purple-600',
    iconBg: 'bg-purple-100',
    hover: 'hover:shadow-lg hover:border-purple-200'
  },
  rose: {
    bg: 'bg-gradient-to-br from-rose-50 to-pink-50',
    icon: 'text-rose-600',
    iconBg: 'bg-rose-100',
    hover: 'hover:shadow-lg hover:border-rose-200'
  },
  amber: {
    bg: 'bg-gradient-to-br from-amber-50 to-orange-50',
    icon: 'text-amber-600',
    iconBg: 'bg-amber-100',
    hover: 'hover:shadow-lg hover:border-amber-200'
  }
}

export default function StatCard({
  label,
  value,
  icon: Icon,
  color = 'blue',
  delta,
  onClick,
  className = ''
}: StatCardProps) {
  const colors = colorClasses[color]

  const cardVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    hover: { scale: 1.02, y: -2 }
  }

  return (
    <motion.div
      variants={cardVariants}
      initial="initial"
      animate="animate"
      whileHover={onClick ? "hover" : undefined}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      className={`
        ${colors.bg}
        bg-white rounded-2xl shadow-soft p-6 border border-gray-100
        ${onClick ? `cursor-pointer ${colors.hover}` : ''}
        transition-all duration-200
        ${className}
      `}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`${colors.iconBg} p-3 rounded-xl`}>
          <Icon className={`w-6 h-6 ${colors.icon}`} />
        </div>
        {delta && (
          <div className={`
            flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-full
            ${delta.trend === 'up' ? 'bg-green-100 text-green-700' : ''}
            ${delta.trend === 'down' ? 'bg-red-100 text-red-700' : ''}
            ${delta.trend === 'neutral' ? 'bg-gray-100 text-gray-700' : ''}
          `}>
            {delta.trend === 'up' && '↗'}
            {delta.trend === 'down' && '↘'}
            {delta.trend === 'neutral' && '→'}
            <span>{delta.value}</span>
          </div>
        )}
      </div>
      
      <div>
        <p className="text-sm text-text-secondary font-medium mb-1">{label}</p>
        <motion.p
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1 }}
          className="text-3xl font-bold text-text-primary"
        >
          {value}
        </motion.p>
      </div>
    </motion.div>
  )
}
