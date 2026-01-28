'use client'

import { DollarSign, Users, TrendingUp, Activity, Award, BookOpen, CheckCircle, Star } from 'lucide-react'
import StatCard from '@/components/admin/StatCard'
import { formatCents, formatPercentage } from '@/lib/currency'
import type { OwnerDashboard } from '@/types/owner'

interface DashboardOverviewProps {
  data: OwnerDashboard
}

export default function DashboardOverview({ data }: DashboardOverviewProps) {
  const { revenue, growth, health, commission_tiers } = data

  // Calculate platform take rate
  const takeRate = revenue.total_gmv_cents > 0
    ? (revenue.total_platform_fees_cents / revenue.total_gmv_cents) * 100
    : 0

  return (
    <div className="space-y-8">
      {/* Revenue Metrics */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Revenue Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total GMV"
            value={formatCents(revenue.total_gmv_cents)}
            icon={DollarSign}
            color="from-emerald-500 to-green-600"
            trend={`Last ${revenue.period_days} days`}
          />
          <StatCard
            title="Platform Fees"
            value={formatCents(revenue.total_platform_fees_cents)}
            icon={TrendingUp}
            color="from-green-500 to-emerald-600"
            trend={`${formatPercentage(takeRate)} take rate`}
          />
          <StatCard
            title="Tutor Payouts"
            value={formatCents(revenue.total_tutor_payouts_cents)}
            icon={Users}
            color="from-blue-500 to-cyan-600"
            trend={`${formatPercentage(100 - takeRate)} to tutors`}
          />
          <StatCard
            title="Avg Booking Value"
            value={formatCents(revenue.average_booking_value_cents)}
            icon={Activity}
            color="from-purple-500 to-indigo-600"
            trend="Per transaction"
          />
        </div>
      </section>

      {/* Growth Metrics */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Growth Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Total Users"
            value={growth.total_users.toLocaleString()}
            icon={Users}
            color="from-blue-500 to-indigo-600"
            trend={`+${growth.new_users_period} last ${growth.period_days} days`}
          />
          <StatCard
            title="Tutors"
            value={growth.total_tutors.toLocaleString()}
            icon={Award}
            color="from-amber-500 to-orange-600"
            trend={`${growth.approved_tutors} approved`}
          />
          <StatCard
            title="Students"
            value={growth.total_students.toLocaleString()}
            icon={BookOpen}
            color="from-cyan-500 to-blue-600"
            trend="Active learners"
          />
          <StatCard
            title="Total Bookings"
            value={growth.total_bookings.toLocaleString()}
            icon={CheckCircle}
            color="from-green-500 to-emerald-600"
            trend={`${growth.completed_bookings} completed`}
          />
          <StatCard
            title="Completion Rate"
            value={formatPercentage(growth.completion_rate)}
            icon={Activity}
            color="from-emerald-500 to-green-600"
            trend="Success metric"
          />
        </div>
      </section>

      {/* Marketplace Health */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Marketplace Health</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Average Rating"
            value={health.average_tutor_rating.toFixed(1)}
            icon={Star}
            color="from-yellow-500 to-amber-600"
            trend="Tutor quality"
          />
          <StatCard
            title="Tutor Utilization"
            value={formatPercentage(health.tutors_with_bookings_pct)}
            icon={Activity}
            color="from-blue-500 to-cyan-600"
            trend="Tutors with bookings"
          />
          <StatCard
            title="Repeat Booking Rate"
            value={formatPercentage(health.repeat_booking_rate)}
            icon={TrendingUp}
            color="from-green-500 to-emerald-600"
            trend="Student retention"
          />
          <StatCard
            title="Cancellation Rate"
            value={formatPercentage(health.cancellation_rate)}
            icon={Activity}
            color="from-amber-500 to-orange-600"
            trend="Lower is better"
          />
          <StatCard
            title="No-Show Rate"
            value={formatPercentage(health.no_show_rate)}
            icon={Activity}
            color="from-red-500 to-orange-600"
            trend="Lower is better"
          />
          {health.average_response_time_hours !== null && (
            <StatCard
              title="Avg Response Time"
              value={`${health.average_response_time_hours.toFixed(1)}h`}
              icon={Activity}
              color="from-cyan-500 to-blue-600"
              trend="Message response"
            />
          )}
        </div>
      </section>

      {/* Commission Tiers */}
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Commission Tier Distribution</h3>
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Standard (20%)</span>
                <span className="text-sm text-gray-600">{commission_tiers.standard_tutors} tutors</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-amber-500 to-orange-600 h-3 rounded-full"
                  style={{ width: `${(commission_tiers.standard_tutors / commission_tiers.total_tutors) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Silver (15%)</span>
                <span className="text-sm text-gray-600">{commission_tiers.silver_tutors} tutors</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-gray-400 to-gray-500 h-3 rounded-full"
                  style={{ width: `${(commission_tiers.silver_tutors / commission_tiers.total_tutors) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Gold (10%)</span>
                <span className="text-sm text-gray-600">{commission_tiers.gold_tutors} tutors</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-yellow-500 to-amber-600 h-3 rounded-full"
                  style={{ width: `${(commission_tiers.gold_tutors / commission_tiers.total_tutors) * 100}%` }}
                />
              </div>
            </div>
            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-gray-800">Total Tutors</span>
                <span className="text-lg font-bold text-gray-900">{commission_tiers.total_tutors}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
