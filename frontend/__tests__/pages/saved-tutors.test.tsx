import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import SavedTutorsPage from '../../app/saved-tutors/page'
import { favorites } from '@/lib/api'
import { authUtils } from '@/lib/auth'
import { useToast } from '@/components/ToastContainer'

// Mock the API
jest.mock('@/lib/api', () => ({
  favorites: {
    getFavorites: jest.fn(),
    removeFavorite: jest.fn(),
  },
  auth: {
    getCurrentUser: jest.fn(),
  },
}))

// Mock auth utils
jest.mock('@/lib/auth', () => ({
  authUtils: {
    isStudent: jest.fn(),
  },
}))

// Mock toast
jest.mock('@/components/ToastContainer', () => ({
  useToast: jest.fn(),
}))

// Mock router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock cookies
jest.mock('js-cookie', () => ({
  get: jest.fn(),
}))

// Mock components
jest.mock('@/components/LoadingSpinner', () => ({
  default: () => <div data-testid="loading-spinner">Loading...</div>,
}))

jest.mock('@/components/Navbar', () => ({
  default: ({ user }: { user: any }) => <div data-testid="navbar">Navbar for {user.email}</div>,
}))

jest.mock('@/components/Footer', () => ({
  default: () => <div data-testid="footer">Footer</div>,
}))

jest.mock('@/components/TutorCard', () => ({
  default: ({ tutor, onToggleSave, isSaved }: any) => (
    <div data-testid={`tutor-card-${tutor.id}`}>
      <h3>{tutor.title}</h3>
      <button
        data-testid={`save-btn-${tutor.id}`}
        onClick={(e) => onToggleSave(e, tutor.id)}
      >
        {isSaved ? 'Remove' : 'Save'}
      </button>
    </div>
  ),
}))

describe('SavedTutorsPage', () => {
  const mockUser = {
    id: 1,
    email: 'student@test.com',
    role: 'student',
  }

  const mockFavorites = [
    {
      id: 1,
      student_id: 1,
      tutor_profile_id: 2,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      student_id: 1,
      tutor_profile_id: 3,
      created_at: '2024-01-02T00:00:00Z',
    },
  ]

  const mockTutors = [
    {
      id: 2,
      title: 'Math Tutor',
      profile_photo_url: null,
      average_rating: 4.5,
      total_reviews: 10,
      hourly_rate: 50,
      subjects: ['Mathematics'],
      experience_years: 5,
    },
    {
      id: 3,
      title: 'English Tutor',
      profile_photo_url: null,
      average_rating: 4.8,
      total_reviews: 15,
      hourly_rate: 45,
      subjects: ['English'],
      experience_years: 3,
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()

    // Setup mocks
    ;(useToast as jest.Mock).mockReturnValue({
      showError: jest.fn(),
      showSuccess: jest.fn(),
    })

    const mockRouter = {
      push: jest.fn(),
    }
    require('next/navigation').useRouter.mockReturnValue(mockRouter)

    // Mock auth
    require('js-cookie').get.mockReturnValue('mock-token')
    require('@/lib/api').auth.getCurrentUser.mockResolvedValue(mockUser)
    ;(authUtils.isStudent as jest.Mock).mockReturnValue(true)
  })

  it('shows loading state initially', async () => {
    // Mock API calls that never resolve to keep loading state
    ;(favorites.getFavorites as jest.Mock).mockImplementation(() => new Promise(() => {}))

    render(<SavedTutorsPage />)

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
  })

  it('redirects to login if not authenticated', async () => {
    const mockRouter = require('next/navigation').useRouter()
    require('js-cookie').get.mockReturnValue(null)

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })
  })

  it('shows empty state when no favorites', async () => {
    ;(favorites.getFavorites as jest.Mock).mockResolvedValue([])

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(screen.getByText('No Saved Tutors Yet')).toBeInTheDocument()
      expect(screen.getByText('Start exploring tutors and save the ones you\'re interested in. They\'ll appear here for easy access.')).toBeInTheDocument()
    })
  })

  it('displays saved tutors when they exist', async () => {
    ;(favorites.getFavorites as jest.Mock).mockResolvedValue(mockFavorites)
    ;(require('@/lib/api').tutors.getPublic as jest.Mock).mockImplementation((id: number) =>
      Promise.resolve(mockTutors.find(t => t.id === id))
    )

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(screen.getByText('Your Saved Tutors (2)')).toBeInTheDocument()
      expect(screen.getByTestId('tutor-card-2')).toBeInTheDocument()
      expect(screen.getByTestId('tutor-card-3')).toBeInTheDocument()
    })
  })

  it('removes tutor from favorites when remove button is clicked', async () => {
    const mockShowSuccess = jest.fn()
    ;(useToast as jest.Mock).mockReturnValue({
      showError: jest.fn(),
      showSuccess: mockShowSuccess,
    })

    ;(favorites.getFavorites as jest.Mock).mockResolvedValue([mockFavorites[0]])
    ;(favorites.removeFavorite as jest.Mock).mockResolvedValue(undefined)
    ;(require('@/lib/api').tutors.getPublic as jest.Mock).mockResolvedValue(mockTutors[0])

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(screen.getByTestId('tutor-card-2')).toBeInTheDocument()
    })

    const removeButton = screen.getByTestId('save-btn-2')
    fireEvent.click(removeButton)

    await waitFor(() => {
      expect(favorites.removeFavorite).toHaveBeenCalledWith(2)
      expect(mockShowSuccess).toHaveBeenCalledWith('Tutor removed from favorites')
    })
  })

  it('handles API errors gracefully', async () => {
    const mockShowError = jest.fn()
    ;(useToast as jest.Mock).mockReturnValue({
      showError: mockShowError,
      showSuccess: jest.fn(),
    })

    ;(favorites.getFavorites as jest.Mock).mockRejectedValue(new Error('API Error'))

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith('Failed to load favorite tutors')
    })
  })

  it('handles remove favorite errors', async () => {
    const mockShowError = jest.fn()
    ;(useToast as jest.Mock).mockReturnValue({
      showError: mockShowError,
      showSuccess: jest.fn(),
    })

    ;(favorites.getFavorites as jest.Mock).mockResolvedValue([mockFavorites[0]])
    ;(favorites.removeFavorite as jest.Mock).mockRejectedValue(new Error('Remove failed'))
    ;(require('@/lib/api').tutors.getPublic as jest.Mock).mockResolvedValue(mockTutors[0])

    render(<SavedTutorsPage />)

    await waitFor(() => {
      expect(screen.getByTestId('tutor-card-2')).toBeInTheDocument()
    })

    const removeButton = screen.getByTestId('save-btn-2')
    fireEvent.click(removeButton)

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith('Failed to remove from favorites')
    })
  })
})