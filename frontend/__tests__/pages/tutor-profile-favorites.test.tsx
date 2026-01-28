import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { jest } from '@jest/globals'
import TutorDetailPage from '../../app/tutors/[id]/page'
import { tutors, favorites, auth } from '@/lib/api'
import { authUtils } from '@/lib/auth'
import { useToast } from '@/components/ToastContainer'

// Create mock functions
const mockShowError = jest.fn()
const mockShowSuccess = jest.fn()

// Mock the API
jest.mock('@/lib/api', () => ({
  tutors: {
    get: jest.fn(),
    getReviews: jest.fn(),
    getPublic: jest.fn(),
  },
  subjects: {
    list: jest.fn(),
  },
  favorites: {
    checkFavorite: jest.fn(),
    addFavorite: jest.fn(),
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
    isTutor: jest.fn(),
  },
}))

// Mock toast - return the mock functions directly
jest.mock('@/components/ToastContainer', () => ({
  useToast: () => ({
    showError: mockShowError,
    showSuccess: mockShowSuccess,
  }),
}))

// Mock router and params (extend global mock)
const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  pathname: '/',
  query: {},
  asPath: '/',
}
const mockParams = { id: '1' }

jest.mock('next/navigation', () => ({
  ...jest.requireActual('next/navigation'),
  useRouter: jest.fn(() => mockRouter),
  useParams: jest.fn(() => mockParams),
}))

// Mock cookies
jest.mock('js-cookie', () => ({
  get: jest.fn(),
}))

// Mock components
jest.mock('@/components/TutorProfileView', () => ({
  default: ({ onToggleSave, isSaved }: any) => (
    <div data-testid="tutor-profile-view">
      <button
        data-testid="toggle-save-btn"
        onClick={(e) => onToggleSave && onToggleSave(e, 1)}
      >
        {isSaved ? 'Remove from favorites' : 'Save to favorites'}
      </button>
    </div>
  ),
}))

jest.mock('@/components/PublicHeader', () => ({
  default: () => <div data-testid="public-header">Public Header</div>,
}))

jest.mock('@/components/Navbar', () => ({
  default: ({ user }: { user: any }) => <div data-testid="navbar">Navbar</div>,
}))

jest.mock('@/components/Footer', () => ({
  default: () => <div data-testid="footer">Footer</div>,
}))

describe('TutorDetailPage - Favorites', () => {
  const mockUser = {
    id: 2,
    email: 'student@test.com',
    role: 'student',
  }

  const mockTutor = {
    id: 1,
    user_id: 3,
    title: 'Math Tutor',
    first_name: 'John',
    last_name: 'Doe',
    profile_photo_url: null,
    average_rating: 4.5,
    total_reviews: 10,
    hourly_rate: 50,
    subjects: ['Mathematics'],
    experience_years: 5,
  }

  const mockSubjects = [
    { id: 1, name: 'Mathematics', category: 'STEM' },
  ]

  const mockReviews = []

  beforeEach(() => {
    jest.clearAllMocks()

    // Mock API responses
    ;(tutors.get as jest.Mock).mockResolvedValue(mockTutor)
    ;(tutors.getReviews as jest.Mock).mockResolvedValue(mockReviews)
    ;(require('@/lib/api').subjects.list as jest.Mock).mockResolvedValue(mockSubjects)

    // Mock auth
    require('js-cookie').get.mockReturnValue('mock-token')
    ;(auth.getCurrentUser as jest.Mock).mockResolvedValue(mockUser)
    ;(authUtils.isStudent as jest.Mock).mockReturnValue(true)
    ;(authUtils.isTutor as jest.Mock).mockReturnValue(false)
  })

  it('checks favorite status on load', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockResolvedValue({ id: 1, tutor_profile_id: 1 })

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(favorites.checkFavorite).toHaveBeenCalledWith(1)
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Remove from favorites')
    })
  })

  it('shows save button when tutor is not favorited', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockRejectedValue(new Error('Not found'))

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(favorites.checkFavorite).toHaveBeenCalledWith(1)
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Save to favorites')
    })
  })

  it('adds tutor to favorites when save button is clicked', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockRejectedValue(new Error('Not found'))
    ;(favorites.addFavorite as jest.Mock).mockResolvedValue({ id: 1, tutor_profile_id: 1 })

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Save to favorites')
    })

    const saveButton = screen.getByTestId('toggle-save-btn')
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(favorites.addFavorite).toHaveBeenCalledWith(1)
      expect(mockShowSuccess).toHaveBeenCalledWith('Tutor saved to favorites')
      expect(saveButton).toHaveTextContent('Remove from favorites')
    })
  })

  it('removes tutor from favorites when remove button is clicked', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockResolvedValue({ id: 1, tutor_profile_id: 1 })
    ;(favorites.removeFavorite as jest.Mock).mockResolvedValue(undefined)

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Remove from favorites')
    })

    const removeButton = screen.getByTestId('toggle-save-btn')
    fireEvent.click(removeButton)

    await waitFor(() => {
      expect(favorites.removeFavorite).toHaveBeenCalledWith(1)
      expect(mockShowSuccess).toHaveBeenCalledWith('Tutor removed from favorites')
      expect(removeButton).toHaveTextContent('Save to favorites')
    })
  })

  it('handles favorite API errors gracefully', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockRejectedValue(new Error('Not found'))
    ;(favorites.addFavorite as jest.Mock).mockRejectedValue({
      response: { data: { detail: 'API Error' } }
    })

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Save to favorites')
    })

    const saveButton = screen.getByTestId('toggle-save-btn')
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith('API Error')
    })
  })

  it('does not show save button for non-students', async () => {
    ;(authUtils.isStudent as jest.Mock).mockReturnValue(false)

    render(<TutorDetailPage />)

    await waitFor(() => {
      // The button should not be rendered since onToggleSave is undefined for non-students
      expect(screen.queryByTestId('toggle-save-btn')).not.toBeInTheDocument()
    })
  })

  it('handles authentication errors gracefully', async () => {
    const mockRouter = require('next/navigation').useRouter()
    ;(auth.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Auth failed'))

    render(<TutorDetailPage />)

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/login')
    })
  })

  it('handles favorite check errors gracefully', async () => {
    ;(favorites.checkFavorite as jest.Mock).mockRejectedValue(new Error('Check failed'))

    render(<TutorDetailPage />)

    await waitFor(() => {
      // Should still render the profile and show save button
      expect(screen.getByTestId('toggle-save-btn')).toHaveTextContent('Save to favorites')
    })
  })
})