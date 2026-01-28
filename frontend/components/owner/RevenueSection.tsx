'use client'

import { DollarSign, TrendingUp, Users, BarChart3 } from 'lucide-react'
import StatCard from '@/components/admin/StatCard'
import { formatCents, formatPercentage } from '@/lib/currency'
import type { RevenueMetrics } from '@/types/owner'

interface RevenueSectionProps {
  data: RevenueMetrics
}

export default function RevenueSection({ data }: RevenueSectionProps) {
  const takeRate = data.total_gmv_cents > 0
    ? (data.total_platform_fees_cents / data.total_gmv_cents) * 100
    : 0

  return (
    <div className="space-y-8">
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Revenue Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Gross Merchandise Value"
            value={formatCents(data.total_gmv_cents)}
            icon={DollarSign}
            color="from-emerald-500 to-green-600"
            trend={`Last ${data.period_days} days`}
          />
          <StatCard
            title="Platform Revenue"
            value={formatCents(data.total_platform_fees_cents)}
            icon={TrendingUp}
            color="from-green-500 to-emerald-600"
            trend={`${formatPercentage(takeRate)} of GMV`}
          />
          <StatCard
            title="Tutor Earnings"
            value={formatCents(data.total_tutor_payouts_cents)}
            icon={Users}
            color="from-blue-500 to-cyan-600"
            trend={`${formatPercentage(100 - takeRate)} of GMV`}
          />
          <StatCard
            title="Average Transaction"
            value={formatCents(data.average_booking_value_cents)}
            icon={BarChart3}
            color="from-purple-500 to-indigo-600"
            trend="Per booking"
          />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Financial Summary</h3>
        <div className="bg-white rounded-2xl shadow-md p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-4">Revenue Distribution</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-700">Platform Fees</span>
                    <span className="text-lg font-bold text-emerald-600">{formatCents(data.total_platform_fees_cents)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-green-600 h-2 rounded-full"
                      style={{ width: `${takeRate}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-700">Tutor Payouts</span>
                    <span className="text-lg font-bold text-blue-600">{formatCents(data.total_tutor_payouts_cents)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-cyan-600 h-2 rounded-full"
                      style={{ width: `${100 - takeRate}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-4">Key Metrics</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Platform Take Rate</span>
                  <span className="text-lg font-bold text-gray-900">{formatPercentage(takeRate)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Total GMV</span>
                  <span className="text-lg font-bold text-gray-900">{formatCents(data.total_gmv_cents)}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Avg Booking Value</span>
                  <span className="text-lg font-bold text-gray-900">{formatCents(data.average_booking_value_cents)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
