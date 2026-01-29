'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import {
  Shield, Calendar, MessageCircle, Settings,
  Bell, Coins,
  Users, TrendingDown as ChartLine,
  CreditCard, Lock, Palette, Zap
} from 'lucide-react'
import { useLocale } from '@/contexts/LocaleContext'
import { admin } from '@/lib/api'
import { useAuth } from '@/hooks/useAuth'
import { createLogger } from '@/lib/logger'

import type { UserData, Stats, Activity, Session, Conversation, Message, SidebarItem, SettingsTab } from '@/types/admin'

const logger = createLogger('AdminDashboard')
import AdminSidebar from '@/components/admin/AdminSidebar'
import AdminHeader from '@/components/admin/AdminHeader'
import DashboardSection from '@/components/admin/DashboardSection'
import Footer from '@/components/Footer'
import UsersSection from '@/components/admin/UsersSection'
import SessionsSection from '@/components/admin/SessionsSection'
import ActivitiesSection from '@/components/admin/ActivitiesSection'
import MessagingSection from '@/components/admin/MessagingSection'
import AnalyticsSection from '@/components/admin/AnalyticsSection'
import SettingsSection from '@/components/admin/SettingsSection'

export default function AdminDashboard() {
  const router = useRouter()
  const { setCurrency } = useLocale()
  const { user, loading: authLoading } = useAuth({ requiredRole: 'admin' })
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeSettingsTab, setActiveSettingsTab] = useState('general')
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null)
  const [newMessage, setNewMessage] = useState('')
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  // Real data from backend
  const [stats, setStats] = useState<Stats>({
    totalUsers: 0,
    activeTutors: 0,
    totalSessions: 0,
    revenue: 0,
    satisfaction: 0,
    completionRate: 0
  })
  const [recentActivities, setRecentActivities] = useState<Activity[]>([])
  const [upcomingSessions, setUpcomingSessions] = useState<Session[]>([])
  const [monthlyRevenueData, setMonthlyRevenueData] = useState<any[]>([])
  const [subjectDistribution, setSubjectDistribution] = useState<any[]>([])
  const [userGrowthData, setUserGrowthData] = useState<any[]>([])
  const [sessionMetrics, setSessionMetrics] = useState<any[]>([])
  const [allUsers, setAllUsers] = useState<any[]>([])
  const [pendingTutors, setPendingTutors] = useState<any[]>([])
  const [selectedUser, setSelectedUser] = useState<any>(null)
  const [showUserModal, setShowUserModal] = useState(false)

  // Mock data for messaging (can be implemented later)
  const conversations: Conversation[] = [
    {
      id: 1,
      participant: 'Dr. Maria Garcia',
      role: 'Tutor',
      avatar: 'MG',
      lastMessage: "Hi there! I'm available for our session tomorrow.",
      time: '2 hours ago',
      unread: 2,
      status: 'online'
    },
    {
      id: 2,
      participant: 'Alex Thompson',
      role: 'Student',
      avatar: 'AT',
      lastMessage: 'Thanks for the great session today!',
      time: '5 hours ago',
      unread: 0,
      status: 'offline'
    }
  ]

  const messages: Message[] = [
    { id: 1, sender: 'Dr. Maria Garcia', message: "Hi there! I'm available for our session tomorrow.", time: '2 hours ago', type: 'received' },
    { id: 2, sender: 'Admin', message: 'Great! Looking forward to it.', time: '1 hour ago', type: 'sent' },
    { id: 3, sender: 'Dr. Maria Garcia', message: "Perfect! I'll send you the session link 10 minutes before.", time: '1 hour ago', type: 'received' },
    { id: 4, sender: 'Admin', message: 'Sounds good, thank you!', time: '45 minutes ago', type: 'sent' }
  ]

  const sidebarItems: SidebarItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: Shield },
    { id: 'users', label: 'User Management', icon: Users },
    { id: 'sessions', label: 'Sessions', icon: Calendar },
    { id: 'messaging', label: 'Messaging', icon: MessageCircle },
    { id: 'analytics', label: 'Analytics', icon: ChartLine },
    { id: 'settings', label: 'Settings', icon: Settings }
  ]

  const settingsTabs: SettingsTab[] = [
    { id: 'general', label: 'General', icon: Coins },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'integrations', label: 'Integrations', icon: Zap }
  ]

  // Fetch dashboard data - optimized with caching via API client
  const fetchDashboardData = useCallback(async () => {
    try {
      // Fetch all data in parallel using cached API methods
      const [
        statsData,
        activitiesData,
        sessionsData,
        metricsData,
        revenueData,
        subjectsData,
        growthData
      ] = await Promise.all([
        admin.getDashboardStats(),
        admin.getRecentActivities(50),
        admin.getUpcomingSessions(50),
        admin.getSessionMetrics(),
        admin.getMonthlyRevenue(6),
        admin.getSubjectDistribution(),
        admin.getUserGrowth(6)
      ])

      // Map API response to local Stats type
      setStats({
        totalUsers: statsData.total_users,
        activeTutors: statsData.total_tutors,
        totalSessions: statsData.active_sessions,
        revenue: statsData.total_revenue,
        satisfaction: statsData.conversion_rate * 100, // Convert to percentage
        completionRate: statsData.conversion_rate * 100
      })
      setRecentActivities(activitiesData as Activity[])

      // Transform sessions data
      const transformedSessions = (sessionsData as any[]).map((s: any) => ({
        id: s.id,
        student: s.student_name || 'Unknown',
        tutor: s.tutor_name || 'Unknown',
        subject: s.subject_name || 'Unknown',
        time: new Date(s.start_time).toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: 'numeric',
          minute: 'numeric'
        }),
        duration: `${Math.round((new Date(s.end_time).getTime() - new Date(s.start_time).getTime()) / 60000)} min`,
        status: s.status
      }))
      setUpcomingSessions(transformedSessions)

      setSessionMetrics(metricsData)
      setMonthlyRevenueData(revenueData)
      setSubjectDistribution(subjectsData)
      setUserGrowthData(growthData)
    } catch (error) {
      logger.error('Error fetching dashboard data', error)
    }
  }, [])

  // Fetch all users - optimized with API client
  const fetchUsers = useCallback(async () => {
    try {
      const users = await admin.listUsers()
      setAllUsers(users)
    } catch (error) {
      logger.error('Error fetching users', error)
    }
  }, [])

  // Fetch pending tutors - optimized with API client
  const fetchPendingTutors = useCallback(async () => {
    try {
      const response = await admin.listPendingTutors(1, 50)
      setPendingTutors(response.items || [])
    } catch (error) {
      logger.error('Error fetching pending tutors', error)
    }
  }, [])

  // Approve tutor
  const approveTutor = async (tutorId: number) => {
    try {
      await admin.approveTutor(tutorId)
      await fetchPendingTutors()
      await fetchUsers()
      alert('Tutor approved successfully!')
    } catch (error) {
      logger.error('Error approving tutor', error)
      alert('Failed to approve tutor')
    }
  }

  // Reject tutor
  const rejectTutor = async (tutorId: number, reason: string) => {
    try {
      await admin.rejectTutor(tutorId, reason)
      await fetchPendingTutors()
      await fetchUsers()
      alert('Tutor rejected successfully!')
    } catch (error) {
      logger.error('Error rejecting tutor', error)
      alert('Failed to reject tutor')
    }
  }

  useEffect(() => {
    const loadData = async () => {
      if (!user) return

      try {
        // Sync currency with LocaleContext
        if (user.currency) {
          setCurrency(user.currency)
        }

        // Fetch all dashboard data in parallel
        await Promise.all([
          fetchDashboardData(),
          fetchUsers(),
          fetchPendingTutors()
        ])
      } catch (error) {
        logger.error('Error loading dashboard data', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      loadData()
    }
  }, [user, fetchDashboardData, fetchUsers, fetchPendingTutors, setCurrency])

  // Fetch users when activeTab changes to 'users'
  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers()
      fetchPendingTutors()
    }
  }, [activeTab, fetchUsers, fetchPendingTutors])

  const handleLogout = useCallback(() => {
    Cookies.remove('token')
    router.push('/login')
  }, [router])

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault()
    if (newMessage.trim()) {
      logger.debug('Sending message', { message: newMessage })
      setNewMessage('')
    }
  }

  const handleUserPreferencesUpdated = (updatedUser: UserData) => {
    logger.debug('handleUserPreferencesUpdated called', updatedUser)
    // Currency is already updated in GeneralSettings before this is called
    // This ensures the user state is synced with the backend response
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <AdminSidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sidebarItems={sidebarItems}
        user={user}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <AdminHeader
          activeTab={activeTab}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          isMenuOpen={isMenuOpen}
          setIsMenuOpen={setIsMenuOpen}
          onLogout={handleLogout}
          user={user}
        />

        {/* Dashboard Content */}
        <main className="flex-1 p-6 overflow-auto">
          {activeTab === 'dashboard' && (
            <DashboardSection
              stats={stats}
              recentActivities={recentActivities}
              upcomingSessions={upcomingSessions}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'users' && (
            <UsersSection
              allUsers={allUsers}
              pendingTutors={pendingTutors}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              selectedUser={selectedUser}
              setSelectedUser={setSelectedUser}
              approveTutor={approveTutor}
              rejectTutor={rejectTutor}
            />
          )}

          {activeTab === 'sessions' && (
            <SessionsSection
              upcomingSessions={upcomingSessions}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
            />
          )}

          {activeTab === 'activities' && (
            <ActivitiesSection
              recentActivities={recentActivities}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'messaging' && (
            <MessagingSection
              conversations={conversations}
              messages={messages}
              selectedConversation={selectedConversation}
              setSelectedConversation={setSelectedConversation}
              newMessage={newMessage}
              setNewMessage={setNewMessage}
              handleSendMessage={handleSendMessage}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsSection
              monthlyRevenueData={monthlyRevenueData}
              subjectDistribution={subjectDistribution}
              userGrowthData={userGrowthData}
              sessionMetrics={sessionMetrics}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsSection
              activeSettingsTab={activeSettingsTab}
              setActiveSettingsTab={setActiveSettingsTab}
              settingsTabs={settingsTabs}
              user={user}
              onUserUpdated={handleUserPreferencesUpdated}
            />
          )}
        </main>
      </div>
      <Footer />
    </div>
  )
}
