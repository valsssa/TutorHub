'use client'

interface ToggleProps {
  enabled: boolean
  onChange: (enabled: boolean) => void
  label?: string
  description?: string
}

export default function Toggle({ enabled, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex-1">
        {label && <p className="font-medium text-slate-900 text-sm">{label}</p>}
        {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        className={`
          relative inline-flex h-6 w-11 items-center rounded-full transition-colors
          ${enabled ? 'bg-sky-500' : 'bg-slate-200'}
        `}
        role="switch"
        aria-checked={enabled}
      >
        <span
          className={`
            inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm
            ${enabled ? 'translate-x-6' : 'translate-x-1'}
          `}
        />
      </button>
    </div>
  )
}
