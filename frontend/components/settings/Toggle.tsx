'use client'

import { ReactNode } from 'react'

interface ToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  label?: string
  description?: string
  icon?: ReactNode
}

export default function Toggle({ enabled, onChange, label, description, icon }: ToggleProps) {
  return (
    <div className="flex items-start justify-between pb-6 border-b border-slate-100 dark:border-slate-800 last:border-b-0 last:pb-0">
      <div className="flex items-start gap-3 flex-1 pr-4">
        {icon && (
          <div className="flex-shrink-0 mt-0.5 text-slate-400 dark:text-slate-500">
            {icon}
          </div>
        )}
        <div className="flex-1">
          {label && <h4 className="font-bold text-slate-900 dark:text-white mb-1">{label}</h4>}
          {description && <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>}
        </div>
      </div>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`
          w-12 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out relative flex-shrink-0
          ${enabled ? 'bg-slate-900 dark:bg-white' : 'bg-slate-200 dark:bg-slate-700'}
        `}
        role="switch"
        aria-checked={enabled}
      >
        <div
          className={`
            w-4 h-4 rounded-full bg-white dark:bg-slate-900 shadow-sm transform transition-transform duration-200
            ${enabled ? 'translate-x-6' : 'translate-x-0'}
          `}
        />
      </button>
    </div>
  )
}
