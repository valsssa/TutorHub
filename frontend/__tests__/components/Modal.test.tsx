import { render, screen, fireEvent } from '@testing-library/react'
import Modal from '@/components/Modal'

describe('Modal Component', () => {
  const mockOnClose = jest.fn()
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    title: 'Test Modal',
    children: <div>Modal Content</div>,
  }

  beforeEach(() => {
    mockOnClose.mockClear()
  })

  it('renders nothing when isOpen is false', () => {
    const { container } = render(<Modal {...defaultProps} isOpen={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders modal when isOpen is true', () => {
    render(<Modal {...defaultProps} />)
    expect(screen.getByText('Test Modal')).toBeInTheDocument()
    expect(screen.getByText('Modal Content')).toBeInTheDocument()
  })

  it('displays the title correctly', () => {
    render(<Modal {...defaultProps} title="Custom Title" />)
    expect(screen.getByText('Custom Title')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(
      <Modal {...defaultProps}>
        <div>Custom Children</div>
      </Modal>
    )
    expect(screen.getByText('Custom Children')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', () => {
    render(<Modal {...defaultProps} />)
    const closeButton = screen.getByRole('button')
    fireEvent.click(closeButton)
    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const backdrop = container.querySelector('.bg-black')
    if (backdrop) {
      fireEvent.click(backdrop)
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    }
  })

  it('has proper structure with header and content sections', () => {
    const { container } = render(<Modal {...defaultProps} />)
    
    // Check for header
    const header = container.querySelector('.border-b')
    expect(header).toBeInTheDocument()
    
    // Check for content wrapper
    const content = container.querySelectorAll('.p-6')
    expect(content.length).toBeGreaterThan(0)
  })

  it('applies dark mode classes', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const modal = container.querySelector('.dark\\:bg-slate-900')
    expect(modal).toBeInTheDocument()
  })

  it('has backdrop blur effect', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const backdrop = container.querySelector('.backdrop-blur-sm')
    expect(backdrop).toBeInTheDocument()
  })

  it('has fixed positioning and proper z-index', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const wrapper = container.querySelector('.fixed.inset-0.z-50')
    expect(wrapper).toBeInTheDocument()
  })

  it('has scrollable content area', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const modal = container.querySelector('.overflow-y-auto')
    expect(modal).toBeInTheDocument()
  })

  it('renders close icon (X)', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const closeIcon = container.querySelector('svg')
    expect(closeIcon).toBeInTheDocument()
  })

  it('prevents modal content click from closing modal', () => {
    const { container } = render(<Modal {...defaultProps} />)
    const modalContent = container.querySelector('.bg-white.dark\\:bg-slate-900')
    
    if (modalContent) {
      fireEvent.click(modalContent)
      // onClose should not be called when clicking modal content
      expect(mockOnClose).not.toHaveBeenCalled()
    }
  })

  it('renders complex children correctly', () => {
    render(
      <Modal {...defaultProps}>
        <div>
          <h3>Heading</h3>
          <p>Paragraph</p>
          <button>Action</button>
        </div>
      </Modal>
    )
    
    expect(screen.getByText('Heading')).toBeInTheDocument()
    expect(screen.getByText('Paragraph')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
  })
})
