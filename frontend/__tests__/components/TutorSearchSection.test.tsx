import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import TutorSearchSection from '@/components/TutorSearchSection'
import { Subject } from '@/types'

describe('TutorSearchSection', () => {
  const mockProps = {
    subjects: [] as Subject[],
    selectedSubject: undefined,
    priceRange: [5, 200] as [number, number],
    minRating: undefined,
    minExperience: undefined,
    sortBy: 'top_picks',
    searchTerm: '',
    resultsCount: 0,
    onSubjectChange: jest.fn(),
    onPriceChange: jest.fn(),
    onMinRatingChange: jest.fn(),
    onMinExperienceChange: jest.fn(),
    onSortChange: jest.fn(),
    onSearchChange: jest.fn(),
    onUpdate: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders search input and basic filter buttons', () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    // Then
    expect(screen.getByPlaceholderText(/Search tutors/i)).toBeInTheDocument()
    expect(screen.getByText('All Subjects')).toBeInTheDocument()
    expect(screen.getByText('Any price')).toBeInTheDocument()
    expect(screen.getByText('Any Rating')).toBeInTheDocument()
    expect(screen.getByText('Any Experience')).toBeInTheDocument()
    expect(screen.getByText('Our top picks')).toBeInTheDocument()
  })

  it('displays subject dropdown options when clicked', () => {
    // Given
    const subjects = [
      { id: 1, name: 'Mathematics' },
      { id: 2, name: 'English' }
    ]

    // When
    render(<TutorSearchSection {...mockProps} subjects={subjects} />)

    const subjectButton = screen.getByText('All Subjects')
    fireEvent.click(subjectButton)

    // Then
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
    expect(screen.getByText('English')).toBeInTheDocument()
  })

  it('calls onSubjectChange when subject is selected', () => {
    // Given
    const subjects = [{ id: 1, name: 'Mathematics' }]

    // When
    render(<TutorSearchSection {...mockProps} subjects={subjects} />)

    const subjectButton = screen.getByText('All Subjects')
    fireEvent.click(subjectButton)

    const mathOption = screen.getByText('Mathematics')
    fireEvent.click(mathOption)

    // Then
    expect(mockProps.onSubjectChange).toHaveBeenCalledWith(1)
  })

  it('displays selected subject name', () => {
    // Given
    const subjects = [{ id: 1, name: 'Mathematics' }]

    // When
    render(<TutorSearchSection {...mockProps} subjects={subjects} selectedSubject={1} />)

    // Then
    expect(screen.getByText('Mathematics')).toBeInTheDocument()
  })

  it('calls onSearchChange when search input changes', async () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    const searchInput = screen.getByPlaceholderText(/Search tutors/i)
    fireEvent.change(searchInput, { target: { value: 'John Doe' } })

    // Wait for debounce
    await waitFor(() => {
      expect(mockProps.onSearchChange).toHaveBeenCalledWith('John Doe')
    }, { timeout: 600 })
  })

  it('displays price range label correctly', () => {
    // When
    render(<TutorSearchSection {...mockProps} priceRange={[10, 50]} />)

    // Then
    expect(screen.getByText('$10 - $50')).toBeInTheDocument()
  })

  it('shows rating filter options when clicked', () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    const ratingButton = screen.getByText('Any Rating')
    fireEvent.click(ratingButton)

    // Then
    expect(screen.getByText('4+ Stars')).toBeInTheDocument()
    expect(screen.getByText('4.5+ Stars')).toBeInTheDocument()
    expect(screen.getByText('5 Stars')).toBeInTheDocument()
  })

  it('calls onMinRatingChange when rating option is selected', () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    const ratingButton = screen.getByText('Any Rating')
    fireEvent.click(ratingButton)

    const fourStarsOption = screen.getByText('4+ Stars')
    fireEvent.click(fourStarsOption)

    // Then
    expect(mockProps.onMinRatingChange).toHaveBeenCalledWith(4)
  })


  it('shows experience filter options when clicked', () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    const experienceButton = screen.getByText('Any Experience')
    fireEvent.click(experienceButton)

    // Then
    expect(screen.getByText('1+ Years')).toBeInTheDocument()
    expect(screen.getByText('3+ Years')).toBeInTheDocument()
    expect(screen.getByText('5+ Years')).toBeInTheDocument()
    expect(screen.getByText('10+ Years')).toBeInTheDocument()
  })

  it('calls onMinExperienceChange when experience option is selected', () => {
    // When
    render(<TutorSearchSection {...mockProps} />)

    const experienceButton = screen.getByText('Any Experience')
    fireEvent.click(experienceButton)

    const fiveYearsOption = screen.getByText('5+ Years')
    fireEvent.click(fiveYearsOption)

    // Then
    expect(mockProps.onMinExperienceChange).toHaveBeenCalledWith(5)
  })







})