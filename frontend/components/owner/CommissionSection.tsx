'use client'

import { Award, DollarSign } from 'lucide-react'
import StatCard from '@/components/admin/StatCard'
import { formatPercentage } from '@/lib/currency'
import type { CommissionTierBreakdown } from '@/types/owner'

interface CommissionSectionProps {
  data: CommissionTierBreakdown
}

export default function CommissionSection({ data }: CommissionSectionProps) {
  const standardPct = (data.standard_tutors / data.total_tutors) * 100
  const silverPct = (data.silver_tutors / data.total_tutors) * 100
  const goldPct = (data.gold_tutors / data.total_tutors) * 100

  return (
    <div className="space-y-8">
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Tier Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Tutors"
            value={data.total_tutors.toLocaleString()}
            icon={Award}
            color="from-purple-500 to-indigo-600"
            trend="All tiers"
          />
          <StatCard
            title="Standard (20%)"
            value={data.standard_tutors.toLocaleString()}
            icon={DollarSign}
            color="from-amber-500 to-orange-600"
            trend={`${formatPercentage(standardPct)}`}
          />
          <StatCard
            title="Silver (15%)"
            value={data.silver_tutors.toLocaleString()}
            icon={Award}
            color="from-gray-400 to-gray-600"
            trend={`${formatPercentage(silverPct)}`}
          />
          <StatCard
            title="Gold (10%)"
            value={data.gold_tutors.toLocaleString()}
            icon={Award}
            color="from-yellow-500 to-amber-600"
            trend={`${formatPercentage(goldPct)}`}
          />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Tier Distribution</h3>
        <div className="bg-white rounded-2xl shadow-md p-8">
          <div className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-base font-semibold text-gray-800">Standard Tier</h4>
                  <p className="text-sm text-gray-600">20% commission • &lt; $1,000 lifetime earnings</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-amber-600">{data.standard_tutors}</p>
                  <p className="text-sm text-gray-600">{formatPercentage(standardPct)}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-amber-500 to-orange-600 h-4 rounded-full transition-all"
                  style={{ width: `${standardPct}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-base font-semibold text-gray-800">Silver Tier</h4>
                  <p className="text-sm text-gray-600">15% commission • $1,000-$4,999 lifetime earnings</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-600">{data.silver_tutors}</p>
                  <p className="text-sm text-gray-600">{formatPercentage(silverPct)}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-gray-400 to-gray-600 h-4 rounded-full transition-all"
                  style={{ width: `${silverPct}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-base font-semibold text-gray-800">Gold Tier</h4>
                  <p className="text-sm text-gray-600">10% commission • $5,000+ lifetime earnings</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-yellow-600">{data.gold_tutors}</p>
                  <p className="text-sm text-gray-600">{formatPercentage(goldPct)}</p>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-gradient-to-r from-yellow-500 to-amber-600 h-4 rounded-full transition-all"
                  style={{ width: `${goldPct}%` }}
                />
              </div>
            </div>

            <div className="pt-6 border-t border-gray-200">
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4">
                <p className="text-sm text-gray-700 mb-2">
                  <strong>Commission Structure:</strong> Tutors earn lower commission rates as they achieve higher lifetime earnings milestones.
                  This incentivizes retention and rewards successful tutors.
                </p>
                <p className="text-xs text-gray-600">
                  Tiers are automatically calculated based on lifetime tutor earnings (after platform fees).
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
