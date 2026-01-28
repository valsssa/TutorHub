'use client'

import { ReactNode } from 'react'
import ProtectedRoute from '@/components/ProtectedRoute'
import SettingsSidebar from '@/components/settings/SettingsSidebar'

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="flex flex-col md:flex-row gap-8">
          <SettingsSidebar />
          <div className="flex-1 min-w-0">
            {children}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
