'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { owner } from '@/lib/api'
import { createLogger } from '@/lib/logger'
import type { OwnerDashboard } from '@/types/owner'

import OwnerSidebar from '@/components/owner/OwnerSidebar'
import OwnerHeader from '@/components/owner/OwnerHeader'
import DashboardOverview from '@/components/owner/DashboardOverview'
import RevenueSection from '@/components/owner/RevenueSection'
import GrowthSection from '@/components/owner/GrowthSection'
import HealthSection from '@/components/owner/HealthSection'
import CommissionSection from '@/components/owner/CommissionSection'
import Footer from '@/components/Footer'

const logger = createLogger('OwnerDashboard')

export default function OwnerPage() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth({ requiredRole: 'owner' })
  const [loading, setLoading] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [periodDays, setPeriodDays] = useState(30)
  const [dashboardData, setDashboardData] = useState<OwnerDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)
        logger.info(`Fetching owner dashboard data for ${periodDays} days`)
        const data = await owner.getDashboard(periodDays)
        setDashboardData(data)
        logger.info('Owner dashboard data loaded successfully')
      } catch (err: any) {
        logger.error('Failed to fetch owner dashboard data:', err)
        setError(err.response?.data?.detail || 'Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    if (!authLoading && user) {
      fetchData()
    }
  }, [authLoading, user, periodDays])

  const handleLogout = () => {
    logger.info('Owner logging out')
    router.push('/login')
  }

  // Show loading state
  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading owner dashboard...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-red-600 text-xl font-semibold mb-2">Error</div>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  // Show empty state if no data
  if (!dashboardData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-600">No dashboard data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <OwnerSidebar
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <OwnerHeader
          activeTab={activeTab}
          sidebarOpen={sidebarOpen}
          setSidebarOpen={setSidebarOpen}
          isMenuOpen={isMenuOpen}
          setIsMenuOpen={setIsMenuOpen}
          onLogout={handleLogout}
          user={user}
          periodDays={periodDays}
          setPeriodDays={setPeriodDays}
        />

        <main className="flex-1 overflow-y-auto p-8">
          {activeTab === 'dashboard' && <DashboardOverview data={dashboardData} />}
          {activeTab === 'revenue' && <RevenueSection data={dashboardData.revenue} />}
          {activeTab === 'growth' && <GrowthSection data={dashboardData.growth} />}
          {activeTab === 'health' && <HealthSection data={dashboardData.health} />}
          {activeTab === 'commission' && <CommissionSection data={dashboardData.commission_tiers} />}
        </main>

        <Footer />
      </div>
    </div>
  )
}
