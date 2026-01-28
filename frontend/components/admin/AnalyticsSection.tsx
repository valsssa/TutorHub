'use client'

import { TrendingUp, BarChart3, PieChart, LineChart } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart as RechartsLineChart, Line,
  PieChart as RechartsPieChart, Pie, Cell
} from 'recharts'

interface AnalyticsSectionProps {
  monthlyRevenueData: any[]
  subjectDistribution: any[]
  userGrowthData: any[]
  sessionMetrics: any[]
}

export default function AnalyticsSection({
  monthlyRevenueData,
  subjectDistribution,
  userGrowthData,
  sessionMetrics
}: AnalyticsSectionProps) {
  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {sessionMetrics.map((metric, index) => (
          <div key={index} className="bg-white rounded-2xl shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{metric.metric}</p>
                <p className="text-2xl font-bold text-gray-800 mt-1">{metric.value}</p>
              </div>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                metric.change.startsWith('+') ? 'bg-green-100' : 'bg-blue-100'
              }`}>
                <TrendingUp className={`w-5 h-5 ${
                  metric.change.startsWith('+') ? 'text-green-600' : 'text-blue-600'
                }`} />
              </div>
            </div>
            <p className={`text-sm mt-2 ${
              metric.change.startsWith('+') ? 'text-green-600' : 'text-blue-600'
            }`}>
              {metric.change} from last month
            </p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue & Sessions Chart */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Revenue & Sessions Growth</h3>
            <BarChart3 className="w-6 h-6 text-purple-600" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsLineChart data={monthlyRevenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis yAxisId="left" stroke="#8b5cf6" />
                <YAxis yAxisId="right" orientation="right" stroke="#ec4899" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="revenue"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Revenue (€)"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="sessions"
                  stroke="#ec4899"
                  strokeWidth={2}
                  name="Sessions"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </RechartsLineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Subject Distribution */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Subject Distribution</h3>
            <PieChart className="w-6 h-6 text-pink-600" />
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPieChart>
                <Pie
                  data={subjectDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {subjectDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* User Growth Chart */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-800">User Growth Over Time</h3>
          <LineChart className="w-6 h-6 text-blue-600" />
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={userGrowthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend />
              <Bar dataKey="tutors" name="Tutors" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="students" name="Students" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl p-6 text-white">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <h4 className="text-lg font-semibold mb-2">Platform Health</h4>
            <div className="text-3xl font-bold">94%</div>
            <p className="text-purple-100 text-sm">Overall satisfaction score</p>
          </div>
          <div className="text-center">
            <h4 className="text-lg font-semibold mb-2">Growth Rate</h4>
            <div className="text-3xl font-bold">+28%</div>
            <p className="text-purple-100 text-sm">Month-over-month user growth</p>
          </div>
          <div className="text-center">
            <h4 className="text-lg font-semibold mb-2">Revenue Trend</h4>
            <div className="text-3xl font-bold">€31k</div>
            <p className="text-purple-100 text-sm">Projected next month</p>
          </div>
        </div>
      </div>
    </div>
  )
}
