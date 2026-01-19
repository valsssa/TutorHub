'use client'

import { motion } from 'framer-motion'
import { FiInfo } from 'react-icons/fi'
import { useState } from 'react'

interface ReceiptRowProps {
  label: string
  amount: number | string
  tooltip?: string
  isBold?: boolean
  isTotal?: boolean
  color?: 'default' | 'success' | 'muted'
  currency?: string
}

export default function ReceiptRow({
  label,
  amount,
  tooltip,
  isBold = false,
  isTotal = false,
  color = 'default',
  currency = '$'
}: ReceiptRowProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const textColor = {
    default: 'text-text-primary',
    success: 'text-green-600',
    muted: 'text-text-secondary'
  }[color]

  const formattedAmount = typeof amount === 'number'
    ? `${currency}${amount.toFixed(2)}`
    : amount

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ backgroundColor: 'rgba(0,0,0,0.02)' }}
      className={`
        flex items-center justify-between py-3 px-4 rounded-lg transition-colors
        ${isTotal ? 'border-t-2 border-gray-200 mt-2 pt-4' : ''}
      `}
    >
      <div className="flex items-center gap-2">
        <span className={`
          ${isBold || isTotal ? 'font-semibold' : 'font-medium'}
          ${textColor}
          ${isTotal ? 'text-lg' : 'text-sm'}
        `}>
          {label}
        </span>
        
        {tooltip && (
          <div className="relative">
            <button
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              onFocus={() => setShowTooltip(true)}
              onBlur={() => setShowTooltip(false)}
              className="text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
              aria-label="More information"
            >
              <FiInfo className="w-4 h-4" />
            </button>
            
            {showTooltip && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="absolute left-0 top-full mt-2 z-50 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-lg"
              >
                {tooltip}
                <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45" />
              </motion.div>
            )}
          </div>
        )}
      </div>
      
      <span className={`
        ${isBold || isTotal ? 'font-bold' : 'font-semibold'}
        ${textColor}
        ${isTotal ? 'text-xl' : 'text-sm'}
      `}>
        {formattedAmount}
      </span>
    </motion.div>
  )
}
