'use client'

import { ReactNode } from 'react'
import { FiSettings } from 'react-icons/fi'
import ProtectedRoute from '@/components/ProtectedRoute'
import SettingsSidebar from '@/components/settings/SettingsSidebar'

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-sky-500 to-blue-600 p-3 rounded-xl shadow-md">
              <FiSettings className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Settings</h1>
              <p className="text-slate-600 text-sm mt-0.5">
                Manage your account and preferences
              </p>
            </div>
          </div>
        </div>

        {/* Layout */}
        <div className="flex gap-6">
          <SettingsSidebar />
          <main className="flex-1 min-w-0">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
