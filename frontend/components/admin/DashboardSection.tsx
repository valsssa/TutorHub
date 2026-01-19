'use client'

import { Users, Award, Calendar, DollarSign, Star, CheckCircle, MessageCircle, ChevronDown, BarChart3 } from 'lucide-react'
import { Stats, Activity, Session } from '@/types/admin'
import StatCard from './StatCard'
import QuickAction from './QuickAction'

interface DashboardSectionProps {
  stats: Stats
  recentActivities: Activity[]
  upcomingSessions: Session[]
  setActiveTab: (tab: string) => void
}

export default function DashboardSection({
  stats,
  recentActivities,
  upcomingSessions,
  setActiveTab
}: DashboardSectionProps) {
  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Users"
          value={stats.totalUsers.toLocaleString()}
          icon={Users}
          color="from-blue-500 to-blue-600"
          trend="+12% this month"
        />
        <StatCard
          title="Active Tutors"
          value={stats.activeTutors.toString()}
          icon={Award}
          color="from-green-500 to-green-600"
          trend="+8% this month"
        />
        <StatCard
          title="Total Sessions"
          value={stats.totalSessions.toString()}
          icon={Calendar}
          color="from-purple-500 to-purple-600"
          trend="+15% this month"
        />
        <StatCard
          title="Revenue"
          value={`€${(stats.revenue / 1000).toFixed(1)}k`}
          icon={DollarSign}
          color="from-yellow-500 to-yellow-600"
          trend="+22% this month"
        />
        <StatCard
          title="Satisfaction"
          value={`${stats.satisfaction}/5`}
          icon={Star}
          color="from-pink-500 to-pink-600"
          trend="Excellent"
        />
        <StatCard
          title="Completion Rate"
          value={`${stats.completionRate}%`}
          icon={CheckCircle}
          color="from-indigo-500 to-indigo-600"
          trend="On track"
        />
      </div>

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">Recent Activity</h3>
            <button
              onClick={() => setActiveTab('activities')}
              className="text-pink-600 hover:text-pink-700 text-sm font-medium flex items-center gap-1"
            >
              View All
              <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
            </button>
          </div>
          <div className="space-y-2">
            {recentActivities.slice(0, 4).map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                  activity.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
                }`}></div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    <span className="text-pink-600 font-bold">{activity.user}</span> {activity.action}
                  </p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
                {activity.type === 'success' && (
                  <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
          {recentActivities.length === 0 && (
            <p className="text-center text-gray-500 py-4">No recent activity</p>
          )}
        </div>

        {/* Upcoming Sessions */}
        <div className="bg-white rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">Upcoming Sessions</h3>
            <button
              onClick={() => setActiveTab('sessions')}
              className="text-pink-600 hover:text-pink-700 text-sm font-medium flex items-center gap-1"
            >
              View All
              <ChevronDown className="w-4 h-4 rotate-[-90deg]" />
            </button>
          </div>
          <div className="space-y-3">
            {upcomingSessions.slice(0, 3).map((session) => (
              <div key={session.id} className="p-3 border border-gray-200 rounded-lg hover:border-pink-300 transition-colors">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-sm text-gray-800 truncate">{session.subject}</h4>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ml-2 ${
                    session.status === 'confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {session.status}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-1 truncate">
                  <span className="font-medium">{session.student}</span> with {session.tutor}
                </p>
                <p className="text-xs text-gray-500">{session.time} • {session.duration}</p>
              </div>
            ))}
          </div>
          {upcomingSessions.length === 0 && (
            <p className="text-center text-gray-500 py-4 text-sm">No upcoming sessions</p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-6">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QuickAction
            title="Add New User"
            icon={Users}
            color="bg-blue-500"
            onClick={() => setActiveTab('users')}
          />
          <QuickAction
            title="Schedule Session"
            icon={Calendar}
            color="bg-green-500"
            onClick={() => setActiveTab('sessions')}
          />
          <QuickAction
            title="View Messages"
            icon={MessageCircle}
            color="bg-purple-500"
            onClick={() => setActiveTab('messaging')}
          />
          <QuickAction
            title="View Analytics"
            icon={BarChart3}
            color="bg-pink-500"
            onClick={() => setActiveTab('analytics')}
          />
        </div>
      </div>
    </div>
  )
}
