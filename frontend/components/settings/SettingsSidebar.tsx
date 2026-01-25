'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FiUser,
  FiLock,
  FiBell,
  FiCreditCard,
  FiLink,
  FiAlertTriangle,
} from 'react-icons/fi'

interface SidebarItem {
  id: string
  label: string
  icon: any
  href: string
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { id: 'profile', label: 'Profile', icon: FiUser, href: '/settings' },
  { id: 'account', label: 'Account', icon: FiLock, href: '/settings/account' },
  { id: 'notifications', label: 'Notifications', icon: FiBell, href: '/settings/notifications' },
  { id: 'payments', label: 'Payments & Billing', icon: FiCreditCard, href: '/settings/payments' },
  { id: 'integrations', label: 'Integrations', icon: FiLink, href: '/settings/integrations' },
  { id: 'danger', label: 'Danger Zone', icon: FiAlertTriangle, href: '/settings/danger' },
]

export default function SettingsSidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-full md:w-64 flex-shrink-0">
      <div className="space-y-1 md:sticky md:top-24 overflow-x-auto md:overflow-visible flex md:block pb-2 md:pb-0 gap-2 md:gap-0 snap-x snap-mandatory md:snap-none">
        {SIDEBAR_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          const isDanger = item.id === 'danger'

          return (
            <Link
              key={item.id}
              href={item.href}
              className={`
                flex-shrink-0 md:w-full text-left px-4 py-3 text-sm font-medium transition-all rounded-lg md:rounded-none md:border-l-[3px] border-l-0 snap-center
                ${isActive
                  ? 'border-emerald-500 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/10'
                  : isDanger
                  ? 'border-transparent text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/10'
                  : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                }
              `}
            >
              <div className="flex items-center gap-3">
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </div>
            </Link>
          )
        })}
      </div>
    </aside>
  )
}
