'use client'

import { type Dispatch, type SetStateAction, useEffect } from 'react'
import { Bell, ChevronDown, Globe, Menu } from 'lucide-react'
import { useLocale } from '@/contexts/LocaleContext'

import type { UserData } from '@/types/admin'

interface AdminHeaderProps {
  activeTab: string
  sidebarOpen: boolean
  setSidebarOpen: Dispatch<SetStateAction<boolean>>
  isMenuOpen: boolean
  setIsMenuOpen: Dispatch<SetStateAction<boolean>>
  onLogout: () => void
  user: UserData | null
}

const formatTabTitle = (tab: string): string => tab.replace(/([A-Z])/g, ' $1').trim()

export default function AdminHeader({
  activeTab,
  sidebarOpen,
  setSidebarOpen,
  isMenuOpen,
  setIsMenuOpen,
  onLogout,
  user
}: AdminHeaderProps) {
  const { currency } = useLocale()
  // Context currency is the source of truth for real-time updates
  const currencyCode = currency || user?.currency || 'USD'

  // Debug logging to track currency changes
  useEffect(() => {
    console.log('[AdminHeader] Currency context updated:', currency)
    console.log('[AdminHeader] User currency:', user?.currency)
    console.log('[AdminHeader] Display currency:', currencyCode)
  }, [currency, user?.currency, currencyCode])

  return (
    <header className="bg-white shadow-sm border-b relative z-[10000]">
      <div className="px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 text-gray-600 hover:text-gray-900"
              >
                <Menu className="h-6 w-6" />
              </button>
            )}
            <h2 className="text-xl font-bold text-gray-800 capitalize">{formatTabTitle(activeTab)}</h2>
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-2 text-gray-600 hover:text-gray-900 relative">
              <Bell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
            </button>

            <div
              key={`currency-${currencyCode}`}
              className="flex items-center space-x-2 px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 transition-all"
            >
              <Globe className="w-5 h-5 text-gray-600" />
              <span className="font-semibold">{currencyCode}</span>
            </div>

            <div className="relative">
              <button
                onClick={() => setIsMenuOpen((prev) => !prev)}
                className="flex items-center space-x-2"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-pink-500 to-purple-600 flex items-center justify-center text-white font-bold">
                  AD
                </div>
                <span className="text-sm font-medium hidden md:inline">Admin</span>
                <ChevronDown
                  className={`w-4 h-4 text-gray-600 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-2 z-[10001]">
                  <div className="px-4 py-2 border-b">
                    <p className="text-sm font-medium">Account Settings</p>
                  </div>
                  <button className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100">
                    Profile
                  </button>
                  <button
                    className="w-full text-left px-4 py-2 text-sm hover:bg-gray-100"
                    onClick={() => {
                      setIsMenuOpen(false)
                      onLogout()
                    }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
