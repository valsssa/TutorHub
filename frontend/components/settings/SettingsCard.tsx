import { ReactNode } from 'react'

interface SettingsCardProps {
  title: string
  description?: string
  children: ReactNode
  footer?: ReactNode
}

export default function SettingsCard({ title, description, children, footer }: SettingsCardProps) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 hover:shadow-md transition-all">
      <div className="p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-1">{title}</h3>
        {description && (
          <p className="text-sm text-slate-500 mb-4">{description}</p>
        )}
        {children}
      </div>
      {footer && (
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 rounded-b-2xl">
          {footer}
        </div>
      )}
    </div>
  )
}
