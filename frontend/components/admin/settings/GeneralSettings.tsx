'use client'

import { useState, useEffect } from 'react'
import { Settings, Globe } from 'lucide-react'
import { type UserData } from '@/types/admin'
import { useLocale } from '@/contexts/LocaleContext'
import { CURRENCIES } from '@/lib/locale'
import { auth } from '@/lib/api'

interface GeneralSettingsProps {
  currentUser: UserData | null
  onUserUpdated: (user: UserData) => void
}

export default function GeneralSettings({ currentUser, onUserUpdated }: GeneralSettingsProps) {
  const { currency: contextCurrency, setCurrency } = useLocale()
  const [selectedCurrency, setSelectedCurrency] = useState(contextCurrency)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  useEffect(() => {
    if (currentUser?.currency) {
      setSelectedCurrency(currentUser.currency)
    }
  }, [currentUser])

  const handleCurrencyChange = async (newCurrency: string) => {
    setSelectedCurrency(newCurrency)
  }

  const handleSave = async () => {
    if (saving) return // Prevent double-click

    setSaving(true)
    setMessage(null)

    try {
      console.log('[GeneralSettings] ===== SAVE STARTED =====')
      console.log('[GeneralSettings] Current currency in context:', contextCurrency)
      console.log('[GeneralSettings] Selected currency to save:', selectedCurrency)
      console.log('[GeneralSettings] User current currency:', currentUser?.currency)

      // Update context FIRST to ensure immediate UI update
      console.log('[GeneralSettings] Calling setCurrency with:', selectedCurrency)
      setCurrency(selectedCurrency)
      console.log('[GeneralSettings] setCurrency called - context should now be:', selectedCurrency)

      // Force a small delay to ensure context propagates
      await new Promise(resolve => setTimeout(resolve, 10))

      // Then update backend
      console.log('[GeneralSettings] Calling backend API...')
      const updatedUser = await auth.updatePreferences(selectedCurrency, currentUser?.timezone || 'UTC')
      console.log('[GeneralSettings] Backend updated successfully, response:', updatedUser)

      // Notify parent component with updated user data
      console.log('[GeneralSettings] Calling onUserUpdated...')
      onUserUpdated(updatedUser)

      setMessage({ type: 'success', text: 'Settings saved successfully!' })
      console.log('[GeneralSettings] ===== SAVE COMPLETED =====')
    } catch (error) {
      console.error('[GeneralSettings] ERROR during save:', error)
      // Revert context on error
      if (currentUser?.currency) {
        console.log('[GeneralSettings] Reverting currency to:', currentUser.currency)
        setCurrency(currentUser.currency)
      }
      setMessage({ type: 'error', text: 'Failed to save settings. Please try again.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message.text}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Platform Settings
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Platform Name</label>
              <input
                type="text"
                defaultValue="EduStream"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Default Currency</label>
              <select
                value={selectedCurrency}
                onChange={(e) => handleCurrencyChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              >
                {CURRENCIES.map(curr => (
                  <option key={curr.code} value={curr.code}>
                    {curr.code} - {curr.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Default Language</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent">
                <option>English</option>
                <option>Spanish</option>
                <option>French</option>
                <option>German</option>
              </select>
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Regional Settings
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Timezone</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent">
                <option>UTC+0 (London)</option>
                <option>UTC+1 (Berlin)</option>
                <option>UTC+2 (Athens)</option>
                <option>UTC-5 (New York)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date Format</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent">
                <option>MM/DD/YYYY</option>
                <option>DD/MM/YYYY</option>
                <option>YYYY-MM-DD</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Number Format</label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent">
                <option>1,000.00 (US)</option>
                <option>1.000,00 (EU)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-pink-600 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
