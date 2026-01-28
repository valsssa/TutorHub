'use client'

import { Star, Activity, TrendingUp, AlertCircle, Clock } from 'lucide-react'
import StatCard from '@/components/admin/StatCard'
import { formatPercentage } from '@/lib/currency'
import type { MarketplaceHealth } from '@/types/owner'

interface HealthSectionProps {
  data: MarketplaceHealth
}

export default function HealthSection({ data }: HealthSectionProps) {
  // Calculate overall health score (0-100)
  const healthScore = (
    (data.average_tutor_rating / 5) * 20 + // Rating (0-20 points)
    (data.tutors_with_bookings_pct / 100) * 20 + // Utilization (0-20 points)
    (data.repeat_booking_rate / 100) * 30 + // Repeat rate (0-30 points)
    ((100 - data.cancellation_rate) / 100) * 15 + // Cancellation (0-15 points)
    ((100 - data.no_show_rate) / 100) * 15 // No-show (0-15 points)
  )

  const getHealthColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-amber-600'
    return 'text-red-600'
  }

  const getHealthLabel = (score: number) => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    return 'Needs Attention'
  }

  return (
    <div className="space-y-8">
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Quality Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Average Rating"
            value={data.average_tutor_rating.toFixed(1)}
            icon={Star}
            color="from-yellow-500 to-amber-600"
            trend="Tutor quality"
          />
          <StatCard
            title="Tutor Utilization"
            value={formatPercentage(data.tutors_with_bookings_pct)}
            icon={Activity}
            color="from-blue-500 to-cyan-600"
            trend="Tutors with bookings"
          />
          <StatCard
            title="Repeat Booking Rate"
            value={formatPercentage(data.repeat_booking_rate)}
            icon={TrendingUp}
            color="from-green-500 to-emerald-600"
            trend="Student retention"
          />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Cancellation Rate"
            value={formatPercentage(data.cancellation_rate)}
            icon={AlertCircle}
            color="from-amber-500 to-orange-600"
            trend="Lower is better"
          />
          <StatCard
            title="No-Show Rate"
            value={formatPercentage(data.no_show_rate)}
            icon={AlertCircle}
            color="from-red-500 to-orange-600"
            trend="Lower is better"
          />
          {data.average_response_time_hours !== null && (
            <StatCard
              title="Avg Response Time"
              value={`${data.average_response_time_hours.toFixed(1)}h`}
              icon={Clock}
              color="from-cyan-500 to-blue-600"
              trend="Message response"
            />
          )}
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Overall Health Score</h3>
        <div className="bg-white rounded-2xl shadow-md p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="flex flex-col items-center justify-center">
              <div className="relative w-48 h-48">
                <svg className="w-full h-full" viewBox="0 0 100 100">
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="40"
                    fill="none"
                    stroke={healthScore >= 80 ? '#10b981' : healthScore >= 60 ? '#f59e0b' : '#ef4444'}
                    strokeWidth="8"
                    strokeDasharray={`${(healthScore / 100) * 251.2} 251.2`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className={`text-4xl font-bold ${getHealthColor(healthScore)}`}>
                    {healthScore.toFixed(0)}
                  </span>
                  <span className="text-sm text-gray-600 mt-1">{getHealthLabel(healthScore)}</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-4">Health Breakdown</h4>
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-700">Quality (Rating)</span>
                    <span className="text-sm font-semibold text-gray-900">{data.average_tutor_rating.toFixed(1)}/5.0</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-yellow-500 h-1.5 rounded-full"
                      style={{ width: `${(data.average_tutor_rating / 5) * 100}%` }}
                    />
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-700">Utilization</span>
                    <span className="text-sm font-semibold text-gray-900">{formatPercentage(data.tutors_with_bookings_pct)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full"
                      style={{ width: `${data.tutors_with_bookings_pct}%` }}
                    />
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-700">Retention (Repeat Rate)</span>
                    <span className="text-sm font-semibold text-gray-900">{formatPercentage(data.repeat_booking_rate)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-green-500 h-1.5 rounded-full"
                      style={{ width: `${data.repeat_booking_rate}%` }}
                    />
                  </div>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-700">Reliability (Low Cancellation)</span>
                    <span className="text-sm font-semibold text-gray-900">{formatPercentage(100 - data.cancellation_rate)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-emerald-500 h-1.5 rounded-full"
                      style={{ width: `${100 - data.cancellation_rate}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
