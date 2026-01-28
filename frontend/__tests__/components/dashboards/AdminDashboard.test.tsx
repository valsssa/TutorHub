import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { AdminDashboard } from '@/components/dashboards/AdminDashboard'
import { mockUser } from '@/test-utils/mocks'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() })
}))

jest.mock('@/lib/api', () => ({
  admin: {
    getDashboardStats: jest.fn(),
    getRecentActivities: jest.fn()
  }
}))

describe('AdminDashboard', () => {
  const mockAdmin = mockUser({ role: 'admin', first_name: 'Admin' })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders admin dashboard with metrics', async () => {
    // Given
    const mockStats = {
      total_users: 1250,
      active_tutors: 45,
      sessions_today: 23,
      revenue_today: 1150.50,
      pending_tutors: 8,
      total_sessions: 15420
    }
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue(mockStats)
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
      expect(screen.getByText('1,250')).toBeInTheDocument() // Total users
      expect(screen.getByText('45')).toBeInTheDocument() // Active tutors
      expect(screen.getByText('23')).toBeInTheDocument() // Sessions today
      expect(screen.getByText('$1,150.50')).toBeInTheDocument() // Revenue
    })
  })

  it('displays navigation tabs', async () => {
    // Given
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue({})
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('User Management')).toBeInTheDocument()
      expect(screen.getByText('Tutor Approvals')).toBeInTheDocument()
      expect(screen.getByText('Sessions')).toBeInTheDocument()
      expect(screen.getByText('Analytics')).toBeInTheDocument()
      expect(screen.getByText('Audit Log')).toBeInTheDocument()
      expect(screen.getByText('Settings')).toBeInTheDocument()
    })
  })

  it('shows pending tutors count', async () => {
    // Given
    const mockStats = { pending_tutors: 5 }
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue(mockStats)
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument() // Pending tutors badge
      expect(screen.getByText('pending')).toBeInTheDocument()
    })
  })

  it('displays recent activities', async () => {
    // Given
    const mockActivities = [
      {
        id: 1,
        action: 'user_registered',
        description: 'New student registered',
        timestamp: '2025-01-20T10:30:00Z',
        user_email: 'student@test.com'
      },
      {
        id: 2,
        action: 'tutor_approved',
        description: 'Tutor profile approved',
        timestamp: '2025-01-20T09:15:00Z',
        user_email: 'tutor@test.com'
      }
    ]
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue({})
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue(mockActivities)

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Recent Activities')).toBeInTheDocument()
      expect(screen.getByText('New student registered')).toBeInTheDocument()
      expect(screen.getByText('Tutor profile approved')).toBeInTheDocument()
      expect(screen.getByText('student@test.com')).toBeInTheDocument()
    })
  })

  it('navigates to user management tab', async () => {
    // Given
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue({})
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      const userManagementTab = screen.getByText('User Management')
      fireEvent.click(userManagementTab)
      // Verify tab becomes active (implementation would show different content)
    })
  })

  it('shows quick action buttons', async () => {
    // Given
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue({})
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Approve Tutors')).toBeInTheDocument()
      expect(screen.getByText('View All Users')).toBeInTheDocument()
      expect(screen.getByText('Monitor Sessions')).toBeInTheDocument()
    })
  })

  it('displays system health indicators', async () => {
    // Given
    const mockStats = {
      system_health: 'good',
      database_connections: 12,
      active_websockets: 45
    }
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue(mockStats)
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('System Status: Good')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument() // DB connections
      expect(screen.getByText('45')).toBeInTheDocument() // Active WebSockets
    })
  })

  it('handles loading state', () => {
    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    expect(screen.getByText('Loading admin dashboard...')).toBeInTheDocument()
  })

  it('handles error state', async () => {
    // Given
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockRejectedValue(
      new Error('Failed to load admin dashboard')
    )

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Failed to load admin dashboard')).toBeInTheDocument()
    })
  })

  it('shows admin-specific navigation', async () => {
    // Given
    const { admin } = await import('@/lib/api')
    ;(admin.getDashboardStats as jest.Mock).mockResolvedValue({})
    ;(admin.getRecentActivities as jest.Mock).mockResolvedValue([])

    // When
    render(<AdminDashboard user={mockAdmin} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Admin Panel')).toBeInTheDocument()
      expect(screen.getByText('System Settings')).toBeInTheDocument()
    })
  })
})