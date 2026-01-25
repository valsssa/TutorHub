'use client'

import { ReactNode } from 'react'
import ProtectedRoute from '@/components/ProtectedRoute'
import SettingsSidebar from '@/components/settings/SettingsSidebar'

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="flex flex-col md:flex-row gap-12">
          {/* Sidebar */}
          <SettingsSidebar />
          
          {/* Main Content */}
          <div className="flex-1 max-w-5xl">
            {children}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}
