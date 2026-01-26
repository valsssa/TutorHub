'use client'

import { ReactNode } from 'react'
import { User } from '@/types'
import Navbar from './Navbar'
import Footer from './Footer'
import StudentBottomDock from './StudentBottomDock'
import RateLimitBanner from './RateLimitBanner'
import { useRateLimitHandler } from '@/hooks/useRateLimitHandler'

interface AppShellProps {
  user: User
  children: ReactNode
  showFooter?: boolean
}

export default function AppShell({ user, children, showFooter = true }: AppShellProps) {
  // Initialize rate limit handler
  useRateLimitHandler()

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col transition-colors duration-200">
      <RateLimitBanner />
      <Navbar user={user} />

      <main role="main" className="flex-1 pb-20 md:pb-0">
        {children}
      </main>

      <StudentBottomDock user={user} />
      
      {showFooter && <Footer />}
    </div>
  )
}
