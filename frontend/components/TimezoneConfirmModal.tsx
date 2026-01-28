'use client'

import React from 'react'
import { FiGlobe, FiRefreshCw, FiX } from 'react-icons/fi'
import Button from '@/components/Button'
import { getTimezoneDisplayName } from '@/lib/timezone'

interface TimezoneConfirmModalProps {
  /** Whether the modal is open */
  isOpen: boolean
  /** The timezone detected from the user's browser */
  detectedTimezone: string
  /** The user's currently saved timezone preference */
  savedTimezone: string
  /** Called when user confirms they want to update to the detected timezone */
  onConfirmUpdate: () => void
  /** Called when user wants to keep their current saved timezone */
  onKeepCurrent: () => void
  /** Whether the update request is in progress */
  isLoading?: boolean
}

export default function TimezoneConfirmModal({
  isOpen,
  detectedTimezone,
  savedTimezone,
  onConfirmUpdate,
  onKeepCurrent,
  isLoading = false,
}: TimezoneConfirmModalProps) {
  if (!isOpen) return null

  const detectedDisplay = getTimezoneDisplayName(detectedTimezone)
  const savedDisplay = getTimezoneDisplayName(savedTimezone)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onKeepCurrent}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <FiGlobe className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                Timezone Changed
              </h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                We detected a different timezone
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <p className="text-slate-700 dark:text-slate-300">
            Your browser timezone appears to be different from your saved preference.
          </p>

          {/* Timezone comparison */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <span className="text-sm text-slate-600 dark:text-slate-400">Detected:</span>
              <span className="font-medium text-blue-700 dark:text-blue-300">
                {detectedDisplay}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-sm text-slate-600 dark:text-slate-400">Current:</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">
                {savedDisplay}
              </span>
            </div>
          </div>

          <p className="text-sm text-slate-500 dark:text-slate-500">
            Would you like to update your timezone to match your current location?
          </p>
        </div>

        {/* Actions */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex gap-3">
          <Button
            variant="secondary"
            onClick={onKeepCurrent}
            disabled={isLoading}
            className="flex-1"
          >
            <FiX className="w-4 h-4 mr-2" />
            Keep {savedDisplay.split(' ')[0]}
          </Button>
          <Button
            variant="primary"
            onClick={onConfirmUpdate}
            isLoading={isLoading}
            className="flex-1"
          >
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Update
          </Button>
        </div>
      </div>
    </div>
  )
}
