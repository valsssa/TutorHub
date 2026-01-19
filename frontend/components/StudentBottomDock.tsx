'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { FiHome, FiSearch, FiMessageSquare, FiHeart, FiUser, FiPackage, FiCalendar } from 'react-icons/fi'
import { User } from '@/types'
import { authUtils } from '@/lib/auth'

interface StudentBottomDockProps {
  user: User
}

export default function StudentBottomDock({ user }: StudentBottomDockProps) {
  const pathname = usePathname()

  const isStudent = authUtils.isStudent(user)
  const isTutor = authUtils.isTutor(user)

  // Different navigation items based on role
  const navItems = isStudent
    ? [
        { href: '/dashboard', icon: FiHome, label: 'Home' },
        { href: '/tutors', icon: FiSearch, label: 'Find' },
        { href: '/packages', icon: FiPackage, label: 'Packages' },
        { href: '/bookings', icon: FiCalendar, label: 'Sessions' },
        { href: '/profile', icon: FiUser, label: 'Profile' }
      ]
    : isTutor
    ? [
        { href: '/dashboard', icon: FiHome, label: 'Home' },
        { href: '/bookings', icon: FiCalendar, label: 'Bookings' },
        { href: '/messages', icon: FiMessageSquare, label: 'Messages' },
        { href: '/tutor/profile', icon: FiUser, label: 'Profile' },
        { href: '/settings', icon: FiUser, label: 'Settings' }
      ]
    : [
        { href: '/dashboard', icon: FiHome, label: 'Home' },
        { href: '/admin', icon: FiSearch, label: 'Admin' },
        { href: '/messages', icon: FiMessageSquare, label: 'Messages' },
        { href: '/settings', icon: FiUser, label: 'Settings' }
      ]

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 shadow-floating">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || (pathname?.startsWith(item.href + '/') ?? false)

          return (
            <Link
              key={item.href}
              href={item.href}
              className="relative flex-1 flex flex-col items-center justify-center gap-1 py-2"
            >
              <div className="relative">
                <Icon
                  className={`w-6 h-6 transition-colors ${
                    isActive ? 'text-brand-rose' : 'text-text-secondary'
                  }`}
                />
                {isActive && (
                  <motion.div
                    layoutId="bottomNavIndicator"
                    className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-brand-rose rounded-full"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
              </div>
              <span
                className={`text-xs font-medium transition-colors ${
                  isActive ? 'text-brand-rose' : 'text-text-secondary'
                }`}
              >
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
