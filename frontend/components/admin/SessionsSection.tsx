'use client'

import { Plus } from 'lucide-react'
import { Session } from '@/types/admin'

interface SessionsSectionProps {
  upcomingSessions: Session[]
  searchTerm: string
  setSearchTerm: (term: string) => void
}

export default function SessionsSection({
  upcomingSessions,
  searchTerm,
  setSearchTerm
}: SessionsSectionProps) {
  return (
    <div className="bg-white rounded-2xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">Session Management</h3>
        <button className="bg-gradient-to-r from-pink-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-pink-600 hover:to-purple-700 transition-all flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Schedule Session
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Session</th>
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Student</th>
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Tutor</th>
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Date & Time</th>
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Duration</th>
              <th className="py-3 text-left text-sm font-semibold text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {upcomingSessions.map((session) => (
              <tr key={session.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-xs font-bold text-purple-800">{session.subject.charAt(0)}</span>
                    </div>
                    <span className="font-medium">{session.subject}</span>
                  </div>
                </td>
                <td className="py-4 font-medium">{session.student}</td>
                <td className="py-4">{session.tutor}</td>
                <td className="py-4 text-gray-600">{session.time}</td>
                <td className="py-4 text-gray-600">{session.duration}</td>
                <td className="py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    (session.status === 'SCHEDULED' || session.status === 'confirmed') ? 'bg-green-100 text-green-800' :
                    (session.status === 'ACTIVE') ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {session.status === 'REQUESTED' ? 'Pending' :
                     session.status === 'SCHEDULED' ? 'Confirmed' :
                     session.status === 'ACTIVE' ? 'In Progress' :
                     session.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
