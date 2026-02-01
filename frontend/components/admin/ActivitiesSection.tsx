'use client'

import { ChevronDown, CheckCircle, Clock } from 'lucide-react'
import { Activity } from '@/types/admin'

interface ActivitiesSectionProps {
  recentActivities: Activity[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  setActiveTab: (tab: string) => void
}

export default function ActivitiesSection({
  recentActivities,
  searchTerm,
  setSearchTerm,
  setActiveTab
}: ActivitiesSectionProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">All Recent Activities</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium flex items-center gap-1"
          >
            <ChevronDown className="w-4 h-4 rotate-90" />
            Back to Dashboard
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {recentActivities.map((activity) => (
          <div key={activity.id} className="flex items-start space-x-3 p-4 rounded-lg border border-gray-200 hover:border-pink-300 hover:bg-gray-50 transition-all">
            <div className={`w-3 h-3 rounded-full mt-1.5 flex-shrink-0 ${
              activity.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
            }`}></div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-gray-800">
                <span className="text-pink-600 font-bold">{activity.user}</span> {activity.action}
              </p>
              <p className="text-sm text-gray-500 mt-1">{activity.time}</p>
            </div>
            {activity.type === 'success' && (
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
            )}
          </div>
        ))}
      </div>

      {recentActivities.length === 0 && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
            <Clock className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500">No recent activity to display</p>
        </div>
      )}
    </div>
  )
}
