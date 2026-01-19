'use client'

import { Palette, Settings, Shield } from 'lucide-react'

export default function AppearanceSettings() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
              <Palette className="w-5 h-5" />
              Theme Settings
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Color Theme</label>
                <div className="grid grid-cols-3 gap-3">
                  <button className="border-2 border-pink-500 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="w-full h-16 bg-gradient-to-r from-pink-500 to-purple-600 rounded-lg mb-2"></div>
                    <p className="text-sm font-medium text-gray-800">Pink & Purple</p>
                    <p className="text-xs text-gray-600">Current</p>
                  </button>
                  <button className="border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="w-full h-16 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg mb-2"></div>
                    <p className="text-sm font-medium text-gray-800">Blue & Indigo</p>
                    <p className="text-xs text-gray-600">Default</p>
                  </button>
                  <button className="border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="w-full h-16 bg-gradient-to-r from-green-500 to-teal-600 rounded-lg mb-2"></div>
                    <p className="text-sm font-medium text-gray-800">Green & Teal</p>
                    <p className="text-xs text-gray-600">Fresh</p>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Display Mode</label>
                <div className="grid grid-cols-2 gap-3">
                  <button className="border-2 border-pink-500 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="w-full h-20 bg-white border border-gray-200 rounded-lg mb-2 flex items-center justify-center">
                      <div className="text-gray-800">
                        <div className="w-12 h-2 bg-gray-800 rounded mb-1"></div>
                        <div className="w-8 h-2 bg-gray-400 rounded"></div>
                      </div>
                    </div>
                    <p className="text-sm font-medium text-gray-800">Light Mode</p>
                  </button>
                  <button className="border-2 border-gray-200 rounded-lg p-4 hover:shadow-md transition-all">
                    <div className="w-full h-20 bg-gray-900 border border-gray-700 rounded-lg mb-2 flex items-center justify-center">
                      <div className="text-white">
                        <div className="w-12 h-2 bg-white rounded mb-1"></div>
                        <div className="w-8 h-2 bg-gray-400 rounded"></div>
                      </div>
                    </div>
                    <p className="text-sm font-medium text-gray-800">Dark Mode</p>
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-800">Compact Mode</p>
                  <p className="text-sm text-gray-600">Reduce spacing for more content</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-pink-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-pink-500 peer-checked:to-purple-600"></div>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
              <Settings className="w-5 h-5" />
              Display Settings
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Font Size</label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent">
                  <option>Small</option>
                  <option>Medium (Default)</option>
                  <option>Large</option>
                  <option>Extra Large</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Custom Branding</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-pink-300 transition-colors cursor-pointer">
                  <div className="w-16 h-16 bg-gradient-to-r from-pink-500 to-purple-600 rounded-lg mx-auto mb-3 flex items-center justify-center">
                    <Shield className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-sm font-medium text-gray-700">Current Logo</p>
                  <button className="text-xs text-pink-600 hover:text-pink-700 mt-2">Change Logo</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center">
        <button className="border border-gray-300 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-50 transition-colors">
          Reset to Defaults
        </button>
        <button className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-6 py-2 rounded-lg hover:from-pink-600 hover:to-purple-700 transition-all">
          Save Appearance Settings
        </button>
      </div>
    </div>
  )
}
