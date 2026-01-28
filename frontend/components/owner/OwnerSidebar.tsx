'use client'

import { Shield, DollarSign, TrendingUp, Activity, Award } from 'lucide-react'

interface SidebarItem {
  id: string
  label: string
  icon: React.ElementType
}

interface OwnerSidebarProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  activeTab: string
  setActiveTab: (tab: string) => void
}

const sidebarItems: SidebarItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: Shield },
  { id: 'revenue', label: 'Revenue Analytics', icon: DollarSign },
  { id: 'growth', label: 'Growth Metrics', icon: TrendingUp },
  { id: 'health', label: 'Marketplace Health', icon: Activity },
  { id: 'commission', label: 'Commission Tiers', icon: Award },
]

export default function OwnerSidebar({
  sidebarOpen,
  setSidebarOpen,
  activeTab,
  setActiveTab,
}: OwnerSidebarProps) {
  if (!sidebarOpen) return null

  return (
    <div className="w-64 bg-white shadow-lg border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold text-gray-800">Owner Portal</h1>
        </div>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {sidebarItems.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.id}>
                <button
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-left transition-colors ${
                    activeTab === item.id
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </nav>
    </div>
  )
}
