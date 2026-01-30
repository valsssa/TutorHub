'use client'

import { CreditCard, Database, MoreVertical, Plus, CheckCircle, Server } from 'lucide-react'

export default function BillingSettings() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2 mb-4">
              <CreditCard className="w-5 h-5" />
              Payment Methods
            </h3>
            <div className="space-y-3">
              <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      VISA
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 dark:text-white">•••• •••• •••• 4242</p>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Expires 12/2025</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium rounded-full">Primary</span>
                    <button className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
              <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-4 bg-white dark:bg-slate-800/50">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-red-600 to-orange-600 rounded flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      MC
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 dark:text-white">•••• •••• •••• 8888</p>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Expires 08/2026</p>
                    </div>
                  </div>
                  <button className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white min-w-[44px] min-h-[44px] flex items-center justify-center touch-manipulation">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <button className="w-full border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-4 text-slate-600 dark:text-slate-400 hover:border-emerald-400 dark:hover:border-emerald-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors flex items-center justify-center gap-2 min-h-[44px] touch-manipulation">
                <Plus className="w-5 h-5" />
                Add New Payment Method
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white flex items-center gap-2 mb-4">
              <Database className="w-5 h-5" />
              Billing History
            </h3>
            <div className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[600px]">
                  <thead className="bg-slate-50 dark:bg-slate-800/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 dark:text-slate-300">Date</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 dark:text-slate-300">Description</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 dark:text-slate-300">Amount</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 dark:text-slate-300">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-semibold text-slate-600 dark:text-slate-300">Invoice</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-700 bg-white dark:bg-slate-900">
                    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">Oct 15, 2025</td>
                      <td className="px-4 py-3 text-sm font-medium text-slate-800 dark:text-white">Monthly Subscription</td>
                      <td className="px-4 py-3 text-sm font-semibold text-slate-800 dark:text-white">€199.00</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium rounded-full">Paid</span>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 text-sm font-medium min-h-[44px] touch-manipulation">Download</button>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">Sep 15, 2025</td>
                      <td className="px-4 py-3 text-sm font-medium text-slate-800 dark:text-white">Monthly Subscription</td>
                      <td className="px-4 py-3 text-sm font-semibold text-slate-800 dark:text-white">€199.00</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium rounded-full">Paid</span>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 text-sm font-medium min-h-[44px] touch-manipulation">Download</button>
                      </td>
                    </tr>
                    <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-400">Aug 15, 2025</td>
                      <td className="px-4 py-3 text-sm font-medium text-slate-800 dark:text-white">Monthly Subscription</td>
                      <td className="px-4 py-3 text-sm font-semibold text-slate-800 dark:text-white">€199.00</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium rounded-full">Paid</span>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 text-sm font-medium min-h-[44px] touch-manipulation">Download</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4">Current Plan</h3>
            <div className="mb-4">
              <div className="text-3xl font-bold text-slate-800 dark:text-white">€199</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">per month</div>
            </div>
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Unlimited users</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Advanced analytics</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Priority support</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-emerald-500" />
                <span>Custom branding</span>
              </div>
            </div>
            <button className="w-full bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg transition-all min-h-[44px] font-semibold touch-manipulation">
              Upgrade Plan
            </button>
          </div>

          <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6 bg-white dark:bg-slate-800/50">
            <h3 className="text-lg font-semibold text-slate-800 dark:text-white mb-4">Next Billing Date</h3>
            <div className="text-2xl font-bold text-slate-800 dark:text-white mb-2">Nov 15, 2025</div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">You will be charged €199.00</p>
            <button className="w-full border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 px-4 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors min-h-[44px] font-medium touch-manipulation">
              Cancel Subscription
            </button>
          </div>

          <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6 bg-blue-50 dark:bg-blue-900/20">
            <div className="flex items-start gap-3">
              <Server className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-1 flex-shrink-0" />
              <div>
                <h4 className="font-semibold text-slate-800 dark:text-white mb-1">Platform Commission</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Current rate: 15% per transaction</p>
                <p className="text-xs text-slate-500 dark:text-slate-500">Total collected this month: €3,675.00</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
