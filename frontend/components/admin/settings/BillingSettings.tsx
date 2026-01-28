'use client'

import { CreditCard, Database, MoreVertical, Plus, CheckCircle, Server } from 'lucide-react'

export default function BillingSettings() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
              <CreditCard className="w-5 h-5" />
              Payment Methods
            </h3>
            <div className="space-y-3">
              <div className="border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-purple-50 to-pink-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-800 rounded flex items-center justify-center text-white text-xs font-bold">
                      VISA
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">•••• •••• •••• 4242</p>
                      <p className="text-sm text-gray-600">Expires 12/2025</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Primary</span>
                    <button className="text-gray-600 hover:text-gray-900">
                      <MoreVertical className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-8 bg-gradient-to-r from-red-600 to-orange-600 rounded flex items-center justify-center text-white text-xs font-bold">
                      MC
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">•••• •••• •••• 8888</p>
                      <p className="text-sm text-gray-600">Expires 08/2026</p>
                    </div>
                  </div>
                  <button className="text-gray-600 hover:text-gray-900">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
              </div>
              <button className="w-full border-2 border-dashed border-gray-300 rounded-lg p-4 text-gray-600 hover:border-pink-300 hover:text-pink-600 transition-colors flex items-center justify-center gap-2">
                <Plus className="w-5 h-5" />
                Add New Payment Method
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-4">
              <Database className="w-5 h-5" />
              Billing History
            </h3>
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Date</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Description</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Amount</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Invoice</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">Oct 15, 2025</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">Monthly Subscription</td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-800">€199.00</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Paid</span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Download</button>
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">Sep 15, 2025</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">Monthly Subscription</td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-800">€199.00</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Paid</span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Download</button>
                    </td>
                  </tr>
                  <tr className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600">Aug 15, 2025</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-800">Monthly Subscription</td>
                    <td className="px-4 py-3 text-sm font-semibold text-gray-800">€199.00</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Paid</span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-pink-600 hover:text-pink-700 text-sm font-medium">Download</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="border border-gray-200 rounded-lg p-6 bg-gradient-to-br from-purple-50 to-pink-50">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Current Plan</h3>
            <div className="mb-4">
              <div className="text-3xl font-bold text-gray-800">€199</div>
              <div className="text-sm text-gray-600">per month</div>
            </div>
            <div className="space-y-2 mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Unlimited users</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Advanced analytics</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Priority support</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Custom branding</span>
              </div>
            </div>
            <button className="w-full bg-gradient-to-r from-pink-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-pink-600 hover:to-purple-700 transition-all">
              Upgrade Plan
            </button>
          </div>

          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Next Billing Date</h3>
            <div className="text-2xl font-bold text-gray-800 mb-2">Nov 15, 2025</div>
            <p className="text-sm text-gray-600 mb-4">You will be charged €199.00</p>
            <button className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors">
              Cancel Subscription
            </button>
          </div>

          <div className="border border-gray-200 rounded-lg p-6 bg-blue-50">
            <div className="flex items-start gap-3">
              <Server className="w-5 h-5 text-blue-600 mt-1" />
              <div>
                <h4 className="font-semibold text-gray-800 mb-1">Platform Commission</h4>
                <p className="text-sm text-gray-600 mb-2">Current rate: 15% per transaction</p>
                <p className="text-xs text-gray-500">Total collected this month: €3,675.00</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
