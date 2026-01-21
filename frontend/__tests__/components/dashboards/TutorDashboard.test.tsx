import { render, screen, waitFor } from '@testing-library/react'
import { TutorDashboard } from '@/components/dashboards/TutorDashboard'
import { mockUser, mockBookings } from '@/test-utils/mocks'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() })
}))

jest.mock('@/lib/api', () => ({
  bookings: {
    list: jest.fn(),
    listTutorBookings: jest.fn()
  }
}))

describe('TutorDashboard', () => {
  const mockTutor = mockUser({ role: 'tutor', first_name: 'Alice' })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders welcome message with tutor name', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: [],
      meta: { total_earnings: 0, sessions_completed: 0 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    expect(screen.getByText(/Welcome back, Alice/i)).toBeInTheDocument()
  })

  it('displays earnings summary', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: [],
      meta: { total_earnings: 1250.50, sessions_completed: 25 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('$1,250.50')).toBeInTheDocument()
      expect(screen.getByText('25 sessions')).toBeInTheDocument()
    })
  })

  it('displays pending booking requests count', async () => {
    // Given
    const pendingBookings = [
      mockBookings({ status: 'pending', id: 1 }),
      mockBookings({ status: 'pending', id: 2 }),
      mockBookings({ status: 'confirmed', id: 3 })
    ]
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: pendingBookings,
      meta: { total_earnings: 0, sessions_completed: 0 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('2 Pending Requests')).toBeInTheDocument()
    })
  })

  it('shows approve/decline buttons for pending bookings', async () => {
    // Given
    const pendingBookings = [mockBookings({ status: 'pending' })]
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: pendingBookings,
      meta: { total_earnings: 0, sessions_completed: 0 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getAllByText('Approve').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Decline').length).toBeGreaterThan(0)
    })
  })

  it('displays upcoming confirmed sessions', async () => {
    // Given
    const upcomingBookings = [
      mockBookings({ status: 'confirmed', start_time: '2025-01-25T10:00:00Z' })
    ]
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: upcomingBookings,
      meta: { total_earnings: 0, sessions_completed: 0 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Upcoming Sessions')).toBeInTheDocument()
      expect(screen.getByText('Jan 25, 2025')).toBeInTheDocument()
    })
  })

  it('shows availability calendar link', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: [],
      meta: { total_earnings: 0, sessions_completed: 0 }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Manage Availability')).toBeInTheDocument()
    })
  })

  it('displays recent reviews section', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockResolvedValue({
      data: [],
      meta: {
        total_earnings: 0,
        sessions_completed: 0,
        recent_reviews: [
          { rating: 5, comment: 'Great tutor!', student_name: 'John' }
        ]
      }
    })

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Recent Reviews')).toBeInTheDocument()
      expect(screen.getByText('Great tutor!')).toBeInTheDocument()
    })
  })

  it('handles loading state', () => {
    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('handles error state', async () => {
    // Given
    const { bookings } = await import('@/lib/api')
    ;(bookings.listTutorBookings as jest.Mock).mockRejectedValue(
      new Error('Failed to load dashboard')
    )

    // When
    render(<TutorDashboard user={mockTutor} />)

    // Then
    await waitFor(() => {
      expect(screen.getByText('Failed to load dashboard')).toBeInTheDocument()
    })
  })
})