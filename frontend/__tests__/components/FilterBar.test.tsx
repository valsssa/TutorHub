import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FilterBar from '@/components/FilterBar'

describe('FilterBar', () => {
  const mockOnFilterChange = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders filter controls', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    // Then
    expect(screen.getByLabelText('Subject')).toBeInTheDocument()
    expect(screen.getByLabelText('Max Price')).toBeInTheDocument()
    expect(screen.getByLabelText('Min Rating')).toBeInTheDocument()
    expect(screen.getByText('Clear Filters')).toBeInTheDocument()
  })

  it('applies subject filter', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    const subjectSelect = screen.getByLabelText('Subject')
    fireEvent.change(subjectSelect, { target: { value: '1' } })

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({ subject_id: 1 })
  })

  it('applies price filter', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    const priceInput = screen.getByLabelText('Max Price')
    fireEvent.change(priceInput, { target: { value: '75' } })

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({ max_price: 75 })
  })

  it('applies rating filter', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    const ratingSelect = screen.getByLabelText('Min Rating')
    fireEvent.change(ratingSelect, { target: { value: '4' } })

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({ min_rating: 4 })
  })

  it('combines multiple filters', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    // Apply multiple filters
    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Max Price'), { target: { value: '60' } })
    fireEvent.change(screen.getByLabelText('Min Rating'), { target: { value: '4' } })

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      subject_id: 1,
      max_price: 60,
      min_rating: 4
    })
  })

  it('shows active filter count badge', () => {
    // When
    render(<FilterBar activeFilters={{ subject_id: 1, min_rating: 4 }} onFilterChange={mockOnFilterChange} />)

    // Then
    expect(screen.getByText('2 active')).toBeInTheDocument()
  })

  it('clears all filters when reset clicked', () => {
    // When
    render(<FilterBar activeFilters={{ subject_id: 1 }} onFilterChange={mockOnFilterChange} />)

    const clearButton = screen.getByText('Clear Filters')
    fireEvent.click(clearButton)

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({})
  })

  it('displays current active filters', () => {
    // When
    render(<FilterBar activeFilters={{ subject_id: 1, max_price: 50 }} onFilterChange={mockOnFilterChange} />)

    // Then
    expect(screen.getByText('Subject: Mathematics')).toBeInTheDocument()
    expect(screen.getByText('Max Price: $50')).toBeInTheDocument()
  })

  it('removes individual filter when close button clicked', () => {
    // When
    render(<FilterBar activeFilters={{ subject_id: 1, max_price: 50 }} onFilterChange={mockOnFilterChange} />)

    const removeSubjectFilter = screen.getByLabelText('Remove subject filter')
    fireEvent.click(removeSubjectFilter)

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({ max_price: 50 })
  })

  it('shows filter options for subjects', async () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} subjects={[
      { id: 1, name: 'Mathematics' },
      { id: 2, name: 'English' }
    ]} />)

    const subjectSelect = screen.getByLabelText('Subject')

    // Then
    expect(subjectSelect).toContainElement(screen.getByText('Mathematics'))
    expect(subjectSelect).toContainElement(screen.getByText('English'))
  })

  it('shows rating options', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    const ratingSelect = screen.getByLabelText('Min Rating')

    // Then
    expect(ratingSelect).toContainElement(screen.getByText('4+ stars'))
    expect(ratingSelect).toContainElement(screen.getByText('3+ stars'))
  })

  it('handles empty filters gracefully', () => {
    // When
    render(<FilterBar activeFilters={{}} onFilterChange={mockOnFilterChange} />)

    // Then
    expect(screen.queryByText(/\d+ active/)).not.toBeInTheDocument()
    expect(screen.queryByText('Subject:')).not.toBeInTheDocument()
  })

  it('shows loading state when applying filters', () => {
    // Given
    mockOnFilterChange.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))

    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} />)

    fireEvent.change(screen.getByLabelText('Subject'), { target: { value: '1' } })

    // Then
    expect(screen.getByText('Applying filters...')).toBeInTheDocument()
  })

  it('displays filter summary', () => {
    // When
    render(<FilterBar activeFilters={{ subject_id: 1, max_price: 75, min_rating: 4 }} onFilterChange={mockOnFilterChange} />)

    // Then
    expect(screen.getByText('3 filters applied')).toBeInTheDocument()
  })

  it('preserves other filters when one is removed', () => {
    // When
    render(<FilterBar activeFilters={{
      subject_id: 1,
      max_price: 75,
      min_rating: 4,
      available_today: true
    }} onFilterChange={mockOnFilterChange} />)

    // Remove price filter
    const removePriceFilter = screen.getByLabelText('Remove price filter')
    fireEvent.click(removePriceFilter)

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      subject_id: 1,
      min_rating: 4,
      available_today: true
    })
  })

  it('shows advanced filters section', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} showAdvanced={true} />)

    // Then
    expect(screen.getByText('Advanced Filters')).toBeInTheDocument()
    expect(screen.getByLabelText('Sort by')).toBeInTheDocument()
    expect(screen.getByLabelText('Experience Level')).toBeInTheDocument()
  })

  it('applies advanced filters', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} showAdvanced={true} />)

    // Apply advanced filters
    fireEvent.change(screen.getByLabelText('Sort by'), { target: { value: 'experience' } })
    fireEvent.change(screen.getByLabelText('Experience Level'), { target: { value: 'expert' } })

    // Then
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      sort_by: 'experience',
      experience_level: 'expert'
    })
  })

  it('toggles advanced filters visibility', () => {
    // When
    render(<FilterBar onFilterChange={mockOnFilterChange} showAdvanced={true} />)

    const toggleButton = screen.getByText('Show Advanced')
    fireEvent.click(toggleButton)

    // Then - Advanced filters should be hidden
    expect(screen.queryByLabelText('Sort by')).not.toBeInTheDocument()

    // Click again to show
    fireEvent.click(screen.getByText('Hide Advanced'))
    expect(screen.getByLabelText('Sort by')).toBeInTheDocument()
  })
})