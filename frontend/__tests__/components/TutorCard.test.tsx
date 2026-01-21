import { render, screen, fireEvent } from '@testing-library/react'
import { TutorCard } from '@/components/TutorCard'

describe('TutorCard', () => {
  const mockTutor = {
    id: 1,
    name: 'Alice Johnson',
    title: 'Math Expert',
    bio: 'Experienced math tutor with 10+ years teaching',
    hourly_rate: 50,
    rating: 4.9,
    review_count: 25,
    subjects: [
      { name: 'Mathematics' },
      { name: 'Calculus' }
    ],
    languages: ['English', 'Spanish'],
    avatar_url: 'https://example.com/avatar.jpg',
    is_available_today: true
  }

  const mockOnBook = jest.fn()
  const mockOnViewProfile = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders tutor information', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Alice Johnson')).toBeInTheDocument()
    expect(screen.getByText('Math Expert')).toBeInTheDocument()
    expect(screen.getByText('$50/hour')).toBeInTheDocument()
    expect(screen.getByText('4.9')).toBeInTheDocument()
    expect(screen.getByText('(25 reviews)')).toBeInTheDocument()
  })

  it('displays subjects list', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
    expect(screen.getByText('Calculus')).toBeInTheDocument()
  })

  it('shows availability status', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Available today')).toBeInTheDocument()
  })

  it('shows unavailable status when not available', () => {
    // Given
    const unavailableTutor = { ...mockTutor, is_available_today: false }

    // When
    render(
      <TutorCard
        tutor={unavailableTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Unavailable today')).toBeInTheDocument()
  })

  it('displays languages spoken', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('English, Spanish')).toBeInTheDocument()
  })

  it('shows truncated bio when too long', () => {
    // Given
    const longBioTutor = {
      ...mockTutor,
      bio: 'This is a very long bio that should be truncated because it exceeds the maximum length allowed for display in the tutor card component. It contains way too much text to fit comfortably.'
    }

    // When
    render(
      <TutorCard
        tutor={longBioTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText(/truncated because it exceeds/)).toBeInTheDocument()
    expect(screen.getByText('...')).toBeInTheDocument()
  })

  it('calls onBook when book button clicked', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    const bookButton = screen.getByText('Book Session')
    fireEvent.click(bookButton)

    // Then
    expect(mockOnBook).toHaveBeenCalledWith(mockTutor)
  })

  it('calls onViewProfile when view profile button clicked', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    const viewProfileButton = screen.getByText('View Profile')
    fireEvent.click(viewProfileButton)

    // Then
    expect(mockOnViewProfile).toHaveBeenCalledWith(mockTutor.id)
  })

  it('displays star rating visually', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    const stars = screen.getAllByLabelText('star')
    expect(stars).toHaveLength(5) // Assuming 5-star rating system

    // Check that first 4 stars are filled (4.9 rating rounds to 5)
    expect(stars[0]).toHaveClass('filled')
    expect(stars[1]).toHaveClass('filled')
    expect(stars[2]).toHaveClass('filled')
    expect(stars[3]).toHaveClass('filled')
    expect(stars[4]).toHaveClass('filled')
  })

  it('shows avatar image when provided', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    const avatar = screen.getByAltText('Alice Johnson')
    expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg')
  })

  it('shows default avatar when no image provided', () => {
    // Given
    const noAvatarTutor = { ...mockTutor, avatar_url: null }

    // When
    render(
      <TutorCard
        tutor={noAvatarTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    const avatar = screen.getByAltText('Alice Johnson')
    expect(avatar).toHaveAttribute('src', '/default-avatar.png')
  })

  it('displays price with currency formatting', () => {
    // Given
    const highPriceTutor = { ...mockTutor, hourly_rate: 125 }

    // When
    render(
      <TutorCard
        tutor={highPriceTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('$125/hour')).toBeInTheDocument()
  })

  it('shows featured badge when tutor is featured', () => {
    // Given
    const featuredTutor = { ...mockTutor, is_featured: true }

    // When
    render(
      <TutorCard
        tutor={featuredTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Featured')).toBeInTheDocument()
  })

  it('disables book button when tutor unavailable', () => {
    // Given
    const unavailableTutor = { ...mockTutor, is_available_today: false }

    // When
    render(
      <TutorCard
        tutor={unavailableTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    const bookButton = screen.getByText('Book Session')
    expect(bookButton).toBeDisabled()
  })

  it('shows next available time when not available today', () => {
    // Given
    const unavailableTutor = {
      ...mockTutor,
      is_available_today: false,
      next_available: 'Tomorrow at 2:00 PM'
    }

    // When
    render(
      <TutorCard
        tutor={unavailableTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Tomorrow at 2:00 PM')).toBeInTheDocument()
  })

  it('handles tutors with no reviews', () => {
    // Given
    const noReviewsTutor = { ...mockTutor, rating: null, review_count: 0 }

    // When
    render(
      <TutorCard
        tutor={noReviewsTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('No reviews yet')).toBeInTheDocument()
  })

  it('displays response time when provided', () => {
    // Given
    const responsiveTutor = { ...mockTutor, average_response_time: '2 hours' }

    // When
    render(
      <TutorCard
        tutor={responsiveTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('Responds in 2 hours')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    // When
    render(
      <TutorCard
        tutor={mockTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
        loading={true}
      />
    )

    // Then
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('handles empty subjects list', () => {
    // Given
    const noSubjectsTutor = { ...mockTutor, subjects: [] }

    // When
    render(
      <TutorCard
        tutor={noSubjectsTutor}
        onBook={mockOnBook}
        onViewProfile={mockOnViewProfile}
      />
    )

    // Then
    expect(screen.getByText('No subjects listed')).toBeInTheDocument()
  })
})