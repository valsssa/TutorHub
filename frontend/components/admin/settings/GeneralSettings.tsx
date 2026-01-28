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
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-200' : 'bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200'}`}>
          {message.text}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Platform Settings
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Platform Name</label>
              <input
                type="text"
                defaultValue="EduStream"
                className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Default Currency</label>
              <div className="relative">
                <select
                  value={selectedCurrency}
                  onChange={(e) => handleCurrencyChange(e.target.value)}
                  className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer"
                >
                  {CURRENCIES.map(curr => (
                    <option key={curr.code} value={curr.code}>
                      {curr.code} - {curr.label}
                    </option>
                  ))}
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 1.5L6 6.5L11 1.5"/>
                  </svg>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Default Language</label>
              <div className="relative">
                <select className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer">
                  <option>English</option>
                  <option>Spanish</option>
                  <option>French</option>
                  <option>German</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 1.5L6 6.5L11 1.5"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Regional Settings
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Timezone</label>
              <div className="relative">
                <select className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer">
                  <option>UTC+0 (London)</option>
                  <option>UTC+1 (Berlin)</option>
                  <option>UTC+2 (Athens)</option>
                  <option>UTC-5 (New York)</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 1.5L6 6.5L11 1.5"/>
                  </svg>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Date Format</label>
              <div className="relative">
                <select className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer">
                  <option>MM/DD/YYYY</option>
                  <option>DD/MM/YYYY</option>
                  <option>YYYY-MM-DD</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 1.5L6 6.5L11 1.5"/>
                  </svg>
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">Number Format</label>
              <div className="relative">
                <select className="w-full p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 appearance-none transition-all cursor-pointer">
                  <option>1,000.00 (US)</option>
                  <option>1.000,00 (EU)</option>
                </select>
                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                  <svg width="12" height="8" viewBox="0 0 12 8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 1.5L6 6.5L11 1.5"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-6 py-2.5 rounded-lg shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}
