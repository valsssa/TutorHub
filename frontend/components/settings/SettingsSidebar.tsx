'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FiUser,
  FiLock,
  FiGlobe,
  FiBell,
  FiCreditCard,
  FiLink,
  FiShield,
  FiHelpCircle,
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
  { id: 'locale', label: 'Language & Currency', icon: FiGlobe, href: '/settings/locale' },
  { id: 'notifications', label: 'Notifications', icon: FiBell, href: '/settings/notifications' },
  { id: 'payments', label: 'Payments & Billing', icon: FiCreditCard, href: '/settings/payments' },
  { id: 'integrations', label: 'Integrations', icon: FiLink, href: '/settings/integrations' },
  { id: 'privacy', label: 'Privacy & Security', icon: FiShield, href: '/settings/privacy' },
  { id: 'help', label: 'Help & Support', icon: FiHelpCircle, href: '/settings/help' },
  { id: 'danger', label: 'Danger Zone', icon: FiAlertTriangle, href: '/settings/danger' },
]

export default function SettingsSidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex flex-col gap-2 w-64 flex-shrink-0">
      {SIDEBAR_ITEMS.map((item) => {
        const Icon = item.icon
        const isActive = pathname === item.href
        const isDanger = item.id === 'danger'

        return (
          <Link
            key={item.id}
            href={item.href}
            className={`
              flex items-center gap-3 px-4 py-3 rounded-xl transition-all
              ${isActive
                ? 'bg-sky-100 text-sky-700 font-semibold shadow-sm'
                : isDanger
                ? 'text-red-600 hover:bg-red-50'
                : 'text-slate-700 hover:bg-sky-50'
              }
            `}
          >
            <Icon className="w-5 h-5" />
            <span className="text-sm">{item.label}</span>
          </Link>
        )
      })}
    </aside>
  )
}
