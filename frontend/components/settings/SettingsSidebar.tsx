'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  FiUser,
  FiLock,
  FiBell,
  FiCreditCard,
  FiLink,
  FiAlertTriangle,
  FiVideo,
  FiGlobe,
} from 'react-icons/fi'
import { auth } from '@/lib/api'

interface SidebarItem {
  id: string
  label: string
  icon: any
  href: string
  tutorOnly?: boolean
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  { id: 'profile', label: 'Profile', icon: FiUser, href: '/settings' },
  { id: 'account', label: 'Account', icon: FiLock, href: '/settings/account' },
  { id: 'video', label: 'Video Meetings', icon: FiVideo, href: '/settings/video', tutorOnly: true },
  { id: 'notifications', label: 'Notifications', icon: FiBell, href: '/settings/notifications' },
  { id: 'payments', label: 'Payments & Billing', icon: FiCreditCard, href: '/settings/payments' },
  { id: 'integrations', label: 'Integrations', icon: FiLink, href: '/settings/integrations' },
  { id: 'locale', label: 'Language & Region', icon: FiGlobe, href: '/settings/locale' },
  { id: 'danger', label: 'Danger Zone', icon: FiAlertTriangle, href: '/settings/danger' },
]

export default function SettingsSidebar() {
  const pathname = usePathname()
  const [userRole, setUserRole] = useState<string | null>(null)

  useEffect(() => {
    const loadUserRole = async () => {
      try {
        const user = await auth.getCurrentUser()
        setUserRole(user.role)
      } catch (error) {
        console.error('Failed to load user role:', error)
      }
    }
    loadUserRole()
  }, [])

  // Filter items based on user role
  const visibleItems = SIDEBAR_ITEMS.filter(item => {
    if (item.tutorOnly && userRole !== 'tutor') {
      return false
    }
    return true
  })

  return (
    <aside className="w-full md:w-64 flex-shrink-0">
      <nav className="md:sticky md:top-24 flex flex-col gap-1">
        {visibleItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          const isDanger = item.id === 'danger'

          let linkClasses = 'flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors rounded-lg'

          if (isActive) {
            linkClasses += ' text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20'
          } else if (isDanger) {
            linkClasses += ' text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/10'
          } else {
            linkClasses += ' text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50'
          }

          return (
            <Link
              key={item.id}
              href={item.href}
              className={linkClasses}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
