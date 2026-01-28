import { render, screen, fireEvent } from '@testing-library/react'
import Pagination from '@/components/Pagination'

describe('Pagination Component', () => {
  const mockOnPageChange = jest.fn()
  
  const defaultProps = {
    currentPage: 1,
    totalPages: 10,
    onPageChange: mockOnPageChange,
    hasNext: true,
    hasPrev: false,
  }

  beforeEach(() => {
    mockOnPageChange.mockClear()
  })

  it('renders pagination controls', () => {
    render(<Pagination {...defaultProps} />)
    expect(screen.getByText('← Previous')).toBeInTheDocument()
    expect(screen.getByText('Next →')).toBeInTheDocument()
  })

  it('displays current page and total pages', () => {
    render(<Pagination {...defaultProps} totalItems={100} />)
    expect(screen.getByText(/Showing page/)).toBeInTheDocument()
    expect(screen.getByText('1', { selector: 'span' })).toBeInTheDocument()
    expect(screen.getByText('10', { selector: 'span' })).toBeInTheDocument()
  })

  it('displays total items when provided', () => {
    render(<Pagination {...defaultProps} totalItems={95} />)
    expect(screen.getByText(/95 total/)).toBeInTheDocument()
  })

  it('disables Previous button when hasPrev is false', () => {
    render(<Pagination {...defaultProps} hasPrev={false} />)
    const prevButton = screen.getByLabelText('Previous page')
    expect(prevButton).toBeDisabled()
    expect(prevButton).toHaveClass('cursor-not-allowed')
  })

  it('enables Previous button when hasPrev is true', () => {
    render(<Pagination {...defaultProps} currentPage={5} hasPrev={true} />)
    const prevButton = screen.getByLabelText('Previous page')
    expect(prevButton).not.toBeDisabled()
  })

  it('disables Next button when hasNext is false', () => {
    render(<Pagination {...defaultProps} hasNext={false} />)
    const nextButton = screen.getByLabelText('Next page')
    expect(nextButton).toBeDisabled()
    expect(nextButton).toHaveClass('cursor-not-allowed')
  })

  it('enables Next button when hasNext is true', () => {
    render(<Pagination {...defaultProps} hasNext={true} />)
    const nextButton = screen.getByLabelText('Next page')
    expect(nextButton).not.toBeDisabled()
  })

  it('calls onPageChange with correct page when Previous is clicked', () => {
    render(<Pagination {...defaultProps} currentPage={5} hasPrev={true} />)
    const prevButton = screen.getByLabelText('Previous page')
    fireEvent.click(prevButton)
    expect(mockOnPageChange).toHaveBeenCalledWith(4)
  })

  it('calls onPageChange with correct page when Next is clicked', () => {
    render(<Pagination {...defaultProps} />)
    const nextButton = screen.getByLabelText('Next page')
    fireEvent.click(nextButton)
    expect(mockOnPageChange).toHaveBeenCalledWith(2)
  })

  it('renders all page numbers when total pages is small', () => {
    render(<Pagination {...defaultProps} totalPages={5} currentPage={1} />)
    // Should show pages 1-5
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByLabelText(`Page ${i}`)).toBeInTheDocument()
    }
  })

  it('shows ellipsis when there are many pages', () => {
    render(<Pagination {...defaultProps} currentPage={5} totalPages={20} />)
    expect(screen.getByText('...')).toBeInTheDocument()
  })

  it('highlights current page', () => {
    render(<Pagination {...defaultProps} currentPage={3} />)
    const currentPageButton = screen.getByLabelText('Page 3')
    expect(currentPageButton).toHaveClass('from-sky-500')
    expect(currentPageButton).toHaveAttribute('aria-current', 'page')
  })

  it('calls onPageChange when page number is clicked', () => {
    render(<Pagination {...defaultProps} totalPages={5} />)
    const page3Button = screen.getByLabelText('Page 3')
    fireEvent.click(page3Button)
    expect(mockOnPageChange).toHaveBeenCalledWith(3)
  })

  it('always shows first and last page', () => {
    render(<Pagination {...defaultProps} currentPage={10} totalPages={20} />)
    expect(screen.getByLabelText('Page 1')).toBeInTheDocument()
    expect(screen.getByLabelText('Page 20')).toBeInTheDocument()
  })

  it('does not call onPageChange when disabled Previous is clicked', () => {
    render(<Pagination {...defaultProps} hasPrev={false} />)
    const prevButton = screen.getByLabelText('Previous page')
    fireEvent.click(prevButton)
    expect(mockOnPageChange).not.toHaveBeenCalled()
  })

  it('does not call onPageChange when disabled Next is clicked', () => {
    render(<Pagination {...defaultProps} hasNext={false} />)
    const nextButton = screen.getByLabelText('Next page')
    fireEvent.click(nextButton)
    expect(mockOnPageChange).not.toHaveBeenCalled()
  })

  it('shows mobile page indicator', () => {
    const { container } = render(<Pagination {...defaultProps} currentPage={3} />)
    const mobileIndicator = container.querySelector('.sm\\:hidden')
    expect(mobileIndicator).toHaveTextContent('3 / 10')
  })

  it('renders correct page range around current page', () => {
    render(<Pagination {...defaultProps} currentPage={10} totalPages={20} />)
    
    // Should show pages around current page (9, 10, 11)
    expect(screen.getByLabelText('Page 9')).toBeInTheDocument()
    expect(screen.getByLabelText('Page 10')).toBeInTheDocument()
    expect(screen.getByLabelText('Page 11')).toBeInTheDocument()
  })

  it('handles edge case of single page', () => {
    render(<Pagination {...defaultProps} totalPages={1} hasNext={false} />)
    expect(screen.getByLabelText('Page 1')).toBeInTheDocument()
    expect(screen.getByLabelText('Previous page')).toBeDisabled()
    expect(screen.getByLabelText('Next page')).toBeDisabled()
  })
})
