import { screen } from '@testing-library/react'
import { render } from '../../test-utils'
import TutorDashboard from '@/components/dashboards/TutorDashboard'

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() })
}))

describe('TutorDashboard', () => {
  const mockUser = {
    id: 1,
    email: 'alice@example.com',
    role: 'tutor' as const,
    is_active: true,
    is_verified: true,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
    avatar_url: null,
    avatarUrl: null,
    currency: 'USD',
    timezone: 'UTC',
    first_name: 'Alice',
    last_name: 'Smith',
    country: null,
    bio: null,
    learning_goal: null,
  }

  const mockBookingsList = []

  const mockProfile = {
    id: 1,
    user_id: 1,
    name: 'Alice Smith',
    title: 'Math Tutor',
    headline: 'Expert Math Tutor',
    bio: 'I love teaching math',
    description: 'Experienced math tutor',
    hourly_rate: 50,
    experience_years: 5,
    education: 'Masters in Mathematics',
    languages: ['English'],
    video_url: null,
    profile_photo_url: null,
    average_rating: 4.8,
    total_reviews: 25,
    total_sessions: 100,
    is_approved: true,
    profile_status: 'approved' as const,
    rejection_reason: null,
    subjects: [],
    certifications: [],
    educations: [],
    pricing_options: [],
    availabilities: [],
    timezone: 'UTC',
    version: 1,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders welcome message with tutor name', () => {
    render(<TutorDashboard user={mockUser} bookings={mockBookingsList} profile={mockProfile} />)

    expect(screen.getByText(/Welcome, Alice Smith/i)).toBeInTheDocument()
  })

  it('shows verified tutor badge', () => {
    render(<TutorDashboard user={mockUser} bookings={mockBookingsList} profile={mockProfile} />)

    expect(screen.getByText('Verified Tutor')).toBeInTheDocument()
  })

  it('shows quick schedule buttons', () => {
    render(<TutorDashboard user={mockUser} bookings={mockBookingsList} profile={mockProfile} />)

    expect(screen.getByText('Schedule session')).toBeInTheDocument()
    expect(screen.getByText('Add time off')).toBeInTheDocument()
    expect(screen.getByText('Add extra slots')).toBeInTheDocument()
    expect(screen.getByText('Set up availability')).toBeInTheDocument()
  })

  it('shows Tutor Command Center title', () => {
    render(<TutorDashboard user={mockUser} bookings={mockBookingsList} profile={mockProfile} />)

    expect(screen.getByText('Tutor Command Center')).toBeInTheDocument()
  })
})