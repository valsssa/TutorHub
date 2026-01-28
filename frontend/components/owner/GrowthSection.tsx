'use client'

import { Users, Award, BookOpen, TrendingUp, CheckCircle, Activity } from 'lucide-react'
import StatCard from '@/components/admin/StatCard'
import { formatPercentage } from '@/lib/currency'
import type { GrowthMetrics } from '@/types/owner'

interface GrowthSectionProps {
  data: GrowthMetrics
}

export default function GrowthSection({ data }: GrowthSectionProps) {
  const approvalRate = data.total_tutors > 0
    ? (data.approved_tutors / data.total_tutors) * 100
    : 0

  return (
    <div className="space-y-8">
      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">User Growth</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Total Users"
            value={data.total_users.toLocaleString()}
            icon={Users}
            color="from-blue-500 to-indigo-600"
            trend={`+${data.new_users_period} last ${data.period_days} days`}
          />
          <StatCard
            title="Total Tutors"
            value={data.total_tutors.toLocaleString()}
            icon={Award}
            color="from-amber-500 to-orange-600"
            trend={`${data.approved_tutors} approved`}
          />
          <StatCard
            title="Total Students"
            value={data.total_students.toLocaleString()}
            icon={BookOpen}
            color="from-cyan-500 to-blue-600"
            trend="Active learners"
          />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Booking Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard
            title="Total Bookings"
            value={data.total_bookings.toLocaleString()}
            icon={CheckCircle}
            color="from-green-500 to-emerald-600"
            trend="All time"
          />
          <StatCard
            title="Completed Sessions"
            value={data.completed_bookings.toLocaleString()}
            icon={TrendingUp}
            color="from-emerald-500 to-green-600"
            trend="Successful"
          />
          <StatCard
            title="Completion Rate"
            value={formatPercentage(data.completion_rate)}
            icon={Activity}
            color="from-green-600 to-emerald-700"
            trend="Success metric"
          />
        </div>
      </section>

      <section>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Growth Analysis</h3>
        <div className="bg-white rounded-2xl shadow-md p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-4">User Composition</h4>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-700">Tutors</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {data.total_tutors} ({formatPercentage((data.total_tutors / data.total_users) * 100)})
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-amber-500 to-orange-600 h-2 rounded-full"
                      style={{ width: `${(data.total_tutors / data.total_users) * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-700">Students</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {data.total_students} ({formatPercentage((data.total_students / data.total_users) * 100)})
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-cyan-500 to-blue-600 h-2 rounded-full"
                      style={{ width: `${(data.total_students / data.total_users) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-4">Tutor Approval Funnel</h4>
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">Total Tutors</span>
                  <span className="text-lg font-bold text-gray-900">{data.total_tutors}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                  <span className="text-sm text-gray-700">Approved</span>
                  <span className="text-lg font-bold text-emerald-600">{data.approved_tutors}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                  <span className="text-sm text-gray-700">Approval Rate</span>
                  <span className="text-lg font-bold text-blue-600">{formatPercentage(approvalRate)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
