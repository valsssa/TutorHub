import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TutorSearchSection } from '@/components/TutorSearchSection'

jest.mock('@/lib/api', () => ({
  tutors: {
    search: jest.fn()
  },
  subjects: {
    list: jest.fn()
  }
}))

describe('TutorSearchSection', () => {
  const mockOnSearch = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders search input and filters', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [
        { id: 1, name: 'Mathematics' },
        { id: 2, name: 'English' }
      ]
    })

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Then
    expect(screen.getByPlaceholderText(/Search by name or subject/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Subject')).toBeInTheDocument()
    expect(screen.getByLabelText(/Price Range/i)).toBeInTheDocument()
    expect(screen.getByLabelText('Minimum Rating')).toBeInTheDocument()
  })

  it('debounces search input', async () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const input = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(input, { target: { value: 'Math' } })

    // Then - should not call immediately
    expect(mockOnSearch).not.toHaveBeenCalled()

    // After debounce delay (500ms)
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('Math')
    }, { timeout: 600 })
  })

  it('applies subject filter', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [{ id: 1, name: 'Mathematics' }]
    })

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    await waitFor(() => {
      const subjectSelect = screen.getByLabelText('Subject')
      fireEvent.change(subjectSelect, { target: { value: '1' } })
    })

    // Then
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('', { subject_id: 1 })
    })
  })

  it('applies price range filter', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const maxPriceInput = screen.getByLabelText('Max Price')
    fireEvent.change(maxPriceInput, { target: { value: '75' } })

    // Then
    expect(mockOnSearch).toHaveBeenCalledWith('', { max_price: 75 })
  })

  it('applies rating filter', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const ratingSelect = screen.getByLabelText('Minimum Rating')
    fireEvent.change(ratingSelect, { target: { value: '4' } })

    // Then
    expect(mockOnSearch).toHaveBeenCalledWith('', { min_rating: 4 })
  })

  it('combines multiple filters', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [{ id: 1, name: 'Mathematics' }]
    })

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Apply multiple filters
    const searchInput = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(searchInput, { target: { value: 'John' } })

    await waitFor(() => {
      const subjectSelect = screen.getByLabelText('Subject')
      fireEvent.change(subjectSelect, { target: { value: '1' } })
    })

    const maxPriceInput = screen.getByLabelText('Max Price')
    fireEvent.change(maxPriceInput, { target: { value: '60' } })

    // Then
    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('John', {
        subject_id: 1,
        max_price: 60
      })
    })
  })

  it('shows loading state during search', async () => {
    // Given
    mockOnSearch.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const input = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(input, { target: { value: 'test' } })

    // Then
    expect(screen.getByText('Searching...')).toBeInTheDocument()
  })

  it('displays search results count', async () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} totalResults={25} />)

    // Then
    expect(screen.getByText('25 tutors found')).toBeInTheDocument()
  })

  it('shows no results message', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} totalResults={0} />)

    // Then
    expect(screen.getByText('No tutors found')).toBeInTheDocument()
  })

  it('clears search when clear button clicked', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Fill search
    const input = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(input, { target: { value: 'test search' } })

    // Clear search
    const clearButton = screen.getByLabelText('Clear search')
    fireEvent.click(clearButton)

    // Then
    expect(input).toHaveValue('')
    expect(mockOnSearch).toHaveBeenCalledWith('')
  })

  it('handles search error', async () => {
    // Given
    mockOnSearch.mockRejectedValue(new Error('Search failed'))

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const input = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(input, { target: { value: 'test' } })

    // Then
    await waitFor(() => {
      expect(screen.getByText('Search failed')).toBeInTheDocument()
    })
  })

  it('shows advanced filters toggle', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Then
    expect(screen.getByText('Advanced Filters')).toBeInTheDocument()
  })

  it('toggles advanced filters visibility', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    const toggleButton = screen.getByText('Advanced Filters')
    fireEvent.click(toggleButton)

    // Then - Advanced filters should be visible
    expect(screen.getByText('Sort by')).toBeInTheDocument()
    expect(screen.getByText('Availability')).toBeInTheDocument()
  })

  it('applies sorting options', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Show advanced filters
    const toggleButton = screen.getByText('Advanced Filters')
    fireEvent.click(toggleButton)

    // Select sorting
    const sortSelect = screen.getByLabelText('Sort by')
    fireEvent.change(sortSelect, { target: { value: 'rating' } })

    // Then
    expect(mockOnSearch).toHaveBeenCalledWith('', { sort_by: 'rating' })
  })

  it('filters by availability', () => {
    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Show advanced filters
    const toggleButton = screen.getByText('Advanced Filters')
    fireEvent.click(toggleButton)

    // Select availability
    const availabilitySelect = screen.getByLabelText('Availability')
    fireEvent.change(availabilitySelect, { target: { value: 'today' } })

    // Then
    expect(mockOnSearch).toHaveBeenCalledWith('', { available_today: true })
  })

  it('resets all filters', async () => {
    // Given
    const { subjects } = await import('@/lib/api')
    ;(subjects.list as jest.Mock).mockResolvedValue({
      data: [{ id: 1, name: 'Mathematics' }]
    })

    // When
    render(<TutorSearchSection onSearch={mockOnSearch} />)

    // Apply filters
    const searchInput = screen.getByPlaceholderText(/Search/i)
    fireEvent.change(searchInput, { target: { value: 'test' } })

    await waitFor(() => {
      const subjectSelect = screen.getByLabelText('Subject')
      fireEvent.change(subjectSelect, { target: { value: '1' } })
    })

    // Reset filters
    const resetButton = screen.getByText('Reset Filters')
    fireEvent.click(resetButton)

    // Then
    await waitFor(() => {
      expect(searchInput).toHaveValue('')
      expect(mockOnSearch).toHaveBeenCalledWith('', {})
    })
  })
})