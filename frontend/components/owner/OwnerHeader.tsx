'use client'

import { type Dispatch, type SetStateAction } from 'react'
import { ChevronDown, Menu } from 'lucide-react'
import type { User } from '@/types'

interface OwnerHeaderProps {
  activeTab: string
  sidebarOpen: boolean
  setSidebarOpen: Dispatch<SetStateAction<boolean>>
  isMenuOpen: boolean
  setIsMenuOpen: Dispatch<SetStateAction<boolean>>
  onLogout: () => void
  user: User | null
  periodDays: number
  setPeriodDays: (days: number) => void
}

const formatTabTitle = (tab: string): string => {
  const titles: Record<string, string> = {
    dashboard: 'Dashboard Overview',
    revenue: 'Revenue Analytics',
    growth: 'Growth Metrics',
    health: 'Marketplace Health',
    commission: 'Commission Tiers',
  }
  return titles[tab] || tab
}

const periodOptions = [
  { value: 30, label: '30 Days' },
  { value: 90, label: '90 Days' },
  { value: 180, label: '180 Days' },
  { value: 365, label: '1 Year' },
]

export default function OwnerHeader({
  activeTab,
  sidebarOpen,
  setSidebarOpen,
  isMenuOpen,
  setIsMenuOpen,
  onLogout,
  user,
  periodDays,
  setPeriodDays,
}: OwnerHeaderProps) {
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
            <h2 className="text-xl font-bold text-gray-800">{formatTabTitle(activeTab)}</h2>
          </div>

          <div className="flex items-center space-x-4">
            {/* Period Selector */}
            {(activeTab === 'dashboard' || activeTab === 'revenue' || activeTab === 'growth') && (
              <div className="relative">
                <select
                  value={periodDays}
                  onChange={(e) => setPeriodDays(Number(e.target.value))}
                  className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors cursor-pointer appearance-none pr-10"
                >
                  {periodOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600 pointer-events-none" />
              </div>
            )}

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen((prev) => !prev)}
                className="flex items-center space-x-2"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-xs">
                  OW
                </div>
                <span className="text-sm font-medium hidden md:inline">Owner</span>
                <ChevronDown
                  className={`w-4 h-4 text-gray-600 transition-transform ${isMenuOpen ? 'rotate-180' : ''}`}
                />
              </button>

              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border py-2 z-[10001]">
                  <div className="px-4 py-2 border-b">
                    <p className="text-sm font-medium">{user?.email}</p>
                    <p className="text-xs text-gray-500">Owner</p>
                  </div>
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
