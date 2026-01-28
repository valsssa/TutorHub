import { ReactNode } from 'react'

interface SettingsCardProps {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
}

export default function SettingsCard({ title, description, children, footer }: SettingsCardProps) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-1">{title}</h3>
        {description && (
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">{description}</p>
        )}
        {children}
      </div>
      {footer && (
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 rounded-b-lg">
          {footer}
        </div>
      )}
    </div>
  )
}
