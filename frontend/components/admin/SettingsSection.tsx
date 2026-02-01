'use client'

import { Settings } from 'lucide-react'
import { type SettingsTab, type UserData } from '@/types/admin'
import NotificationSettings from './settings/NotificationSettings'
import BillingSettings from './settings/BillingSettings'
import SecuritySettings from './settings/SecuritySettings'
import AppearanceSettings from './settings/AppearanceSettings'
import IntegrationSettings from './settings/IntegrationSettings'
import GeneralSettings from './settings/GeneralSettings'

interface SettingsSectionProps {
  activeSettingsTab: string
  setActiveSettingsTab: (tab: string) => void
  settingsTabs: SettingsTab[]
  user: UserData | null
  onUserUpdated: (user: UserData) => void
}

export default function SettingsSection({
  activeSettingsTab,
  setActiveSettingsTab,
  settingsTabs,
  user,
  onUserUpdated
}: SettingsSectionProps) {
  return (
    <div className="space-y-6">
      {/* Settings Navigation */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="flex flex-wrap gap-2 mb-6">
          {settingsTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveSettingsTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSettingsTab === tab.id
                    ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* General Settings */}
        {activeSettingsTab === 'general' && (
          <GeneralSettings currentUser={user} onUserUpdated={onUserUpdated} />
        )}

        {/* Notifications Settings */}
        {activeSettingsTab === 'notifications' && <NotificationSettings />}

        {/* Billing Settings */}
        {activeSettingsTab === 'billing' && <BillingSettings />}

        {/* Security Settings */}
        {activeSettingsTab === 'security' && <SecuritySettings />}

        {/* Appearance Settings */}
        {activeSettingsTab === 'appearance' && <AppearanceSettings />}

        {/* Integrations Settings */}
        {activeSettingsTab === 'integrations' && <IntegrationSettings />}

        {/* Other settings tabs */}
        {!['general', 'notifications', 'billing', 'security', 'appearance', 'integrations'].includes(activeSettingsTab) && (
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              {settingsTabs.find(tab => tab.id === activeSettingsTab)?.label} Settings
            </h3>
            <p className="text-gray-600">
              This section is under development. Coming soon!
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
