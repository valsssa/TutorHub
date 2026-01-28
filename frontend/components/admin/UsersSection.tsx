'use client'

import { useState } from 'react'
import { Users, Bell, CheckCircle, Search, Award, Star } from 'lucide-react'
import RejectReasonModal from '@/components/modals/RejectReasonModal'

interface UserData {
  id: number
  email: string
  role: string
  is_active: boolean
  created_at: string
  user?: {
    email: string
    role: string
  }
  title?: string
  hourly_rate?: number
  bio?: string
  profile_status?: string
  average_rating?: number
  total_reviews?: number
  total_sessions?: number
}

interface UsersSectionProps {
  allUsers: UserData[]
  pendingTutors: UserData[]
  searchTerm: string
  setSearchTerm: (term: string) => void
  selectedUser: UserData | null
  setSelectedUser: (user: UserData | null) => void
  approveTutor: (tutorId: number) => Promise<void>
  rejectTutor: (tutorId: number, reason: string) => Promise<void>
}

export default function UsersSection({
  allUsers,
  pendingTutors,
  searchTerm,
  setSearchTerm,
  selectedUser,
  setSelectedUser,
  approveTutor,
  rejectTutor
}: UsersSectionProps) {
  const [rejectModalOpen, setRejectModalOpen] = useState(false)
  const [tutorToReject, setTutorToReject] = useState<number | null>(null)

  const handleOpenRejectModal = (tutorId: number) => {
    setTutorToReject(tutorId)
    setRejectModalOpen(true)
  }

  const handleRejectConfirm = async (reason: string) => {
    if (tutorToReject !== null) {
      await rejectTutor(tutorToReject, reason)
      setTutorToReject(null)
    }
  }

  return (
    <div className="space-y-6">
      {/* Pending Tutor Approvals */}
      {pendingTutors.length > 0 && (
        <div className="bg-gradient-to-r from-orange-50 to-yellow-50 border border-orange-200 rounded-2xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-orange-800 flex items-center gap-2">
              <Bell className="w-6 h-6" />
              Pending Tutor Approvals ({pendingTutors.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pendingTutors.map((tutor) => (
              <div key={tutor.id} className="bg-white border border-orange-200 rounded-xl p-4 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                      <span className="text-lg font-bold text-orange-800">
                        {tutor.user?.email?.charAt(0).toUpperCase() || 'T'}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-800">{tutor.user?.email || 'Unknown'}</p>
                      <span className="text-xs px-2 py-1 bg-orange-100 text-orange-800 rounded-full">
                        {tutor.profile_status || 'pending'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="space-y-2 mb-4 text-sm">
                  <p><span className="font-medium">Title:</span> {tutor.title || 'N/A'}</p>
                  <p><span className="font-medium">Rate:</span> ${tutor.hourly_rate || 0}/hr</p>
                  <p className="text-xs text-gray-600 line-clamp-2">{tutor.bio || 'No bio provided'}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => approveTutor(tutor.id)}
                    className="flex-1 bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-1"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve
                  </button>
                  <button
                    onClick={() => handleOpenRejectModal(tutor.id)}
                    className="flex-1 bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => setSelectedUser(tutor)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Users */}
      <div className="bg-white rounded-2xl shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4 md:mb-0">All Users ({allUsers.length})</h3>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-3 text-left text-sm font-semibold text-gray-600">User</th>
                <th className="py-3 text-left text-sm font-semibold text-gray-600">Email</th>
                <th className="py-3 text-left text-sm font-semibold text-gray-600">Role</th>
                <th className="py-3 text-left text-sm font-semibold text-gray-600">Status</th>
                <th className="py-3 text-left text-sm font-semibold text-gray-600">Joined</th>
                <th className="py-3 text-left text-sm font-semibold text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {allUsers
                .filter((u) =>
                  u.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                  u.role?.toLowerCase().includes(searchTerm.toLowerCase())
                )
                .map((user) => (
                <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-4">
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        user.role === 'admin' ? 'bg-red-100' :
                        user.role === 'tutor' ? 'bg-purple-100' : 'bg-blue-100'
                      }`}>
                        <span className={`text-sm font-bold ${
                          user.role === 'admin' ? 'text-red-800' :
                          user.role === 'tutor' ? 'text-purple-800' : 'text-blue-800'
                        }`}>
                          {user.email?.charAt(0).toUpperCase() || 'U'}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">User #{user.id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 text-gray-600">{user.email}</td>
                  <td className="py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      user.role === 'admin' ? 'bg-red-100 text-red-800' :
                      user.role === 'tutor' ? 'bg-purple-100 text-purple-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="py-4 text-sm text-gray-600">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-4">
                    <button
                      onClick={() => setSelectedUser(user)}
                      className="text-pink-600 hover:text-pink-700 font-medium text-sm"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {allUsers.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No users found</p>
          </div>
        )}
      </div>

      {/* Reject Reason Modal */}
      <RejectReasonModal
        isOpen={rejectModalOpen}
        onClose={() => {
          setRejectModalOpen(false)
          setTutorToReject(null)
        }}
        onConfirm={handleRejectConfirm}
      />

      {/* User Details Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b sticky top-0 bg-white">
              <h3 className="text-2xl font-bold text-gray-800">User Details</h3>
            </div>
            <div className="p-6 space-y-6">
              {/* Basic Info */}
              <div>
                <h4 className="font-semibold text-gray-800 mb-3">Basic Information</h4>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">User ID:</span>
                    <span className="font-medium">#{selectedUser.id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Email:</span>
                    <span className="font-medium">{selectedUser.email || selectedUser.user?.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Role:</span>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      (selectedUser.role || selectedUser.user?.role) === 'admin' ? 'bg-red-100 text-red-800' :
                      (selectedUser.role || selectedUser.user?.role) === 'tutor' ? 'bg-purple-100 text-purple-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {selectedUser.role || selectedUser.user?.role}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      selectedUser.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {selectedUser.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Joined:</span>
                    <span className="font-medium">{new Date(selectedUser.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Tutor Profile Info (if tutor) */}
              {(selectedUser.user?.role === 'tutor' || selectedUser.role === 'tutor' || selectedUser.title) && (
                <div>
                  <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Tutor Profile
                  </h4>
                  <div className="space-y-3 text-sm bg-purple-50 p-4 rounded-lg">
                    {selectedUser.title && (
                      <div>
                        <p className="text-gray-600">Title</p>
                        <p className="font-medium">{selectedUser.title}</p>
                      </div>
                    )}
                    {selectedUser.hourly_rate && (
                      <div>
                        <p className="text-gray-600">Hourly Rate</p>
                        <p className="font-medium text-green-600">${selectedUser.hourly_rate}/hour</p>
                      </div>
                    )}
                    {selectedUser.bio && (
                      <div>
                        <p className="text-gray-600">Bio</p>
                        <p className="font-medium">{selectedUser.bio}</p>
                      </div>
                    )}
                    {selectedUser.profile_status && (
                      <div>
                        <p className="text-gray-600">Profile Status</p>
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                          selectedUser.profile_status === 'approved' ? 'bg-green-100 text-green-800' :
                          selectedUser.profile_status === 'rejected' ? 'bg-red-100 text-red-800' :
                          'bg-orange-100 text-orange-800'
                        }`}>
                          {selectedUser.profile_status}
                        </span>
                      </div>
                    )}
                    {selectedUser.average_rating && (
                      <div>
                        <p className="text-gray-600">Average Rating</p>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-current" />
                          <span className="font-medium">{Number(selectedUser.average_rating).toFixed(1)}</span>
                          <span className="text-gray-500">({selectedUser.total_reviews || 0} reviews)</span>
                        </div>
                      </div>
                    )}
                    {selectedUser.total_sessions !== undefined && (
                      <div>
                        <p className="text-gray-600">Total Sessions</p>
                        <p className="font-medium">{selectedUser.total_sessions}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Admin Actions */}
              <div className="pt-4 border-t flex gap-3">
                <button
                  onClick={() => setSelectedUser(null)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    // Navigate to messages page with user parameter
                    window.location.href = `/messages?user=${selectedUser.id}`
                  }}
                  className="flex-1 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  Send Message
                </button>
                {selectedUser.profile_status === 'pending_approval' && (
                  <>
                    <button
                      onClick={() => {
                        approveTutor(selectedUser.id)
                        setSelectedUser(null)
                      }}
                      className="flex-1 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        handleOpenRejectModal(selectedUser.id)
                        setSelectedUser(null)
                      }}
                      className="flex-1 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
