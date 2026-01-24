import { render, screen } from '@testing-library/react'
import Avatar from '@/components/Avatar'

describe('Avatar Component', () => {
  it('renders with initial when no avatar URL provided', () => {
    render(<Avatar name="John Doe" />)
    expect(screen.getByText('J')).toBeInTheDocument()
  })

  it('renders with correct initial for single character name', () => {
    render(<Avatar name="X" />)
    expect(screen.getByText('X')).toBeInTheDocument()
  })

  it('renders default initial "U" when no name provided', () => {
    render(<Avatar />)
    expect(screen.getByText('U')).toBeInTheDocument()
  })

  it('renders image when avatarUrl is provided', () => {
    render(<Avatar name="Jane Smith" avatarUrl="https://example.com/avatar.jpg" />)
    const img = screen.getByRole('img', { name: 'Jane Smith' })
    expect(img).toBeInTheDocument()
    expect(img).toHaveAttribute('src')
  })

  it('does not render image for ui-avatars.com URLs', () => {
    render(<Avatar name="Test User" avatarUrl="https://ui-avatars.com/api/?name=Test" />)
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    expect(screen.getByText('T')).toBeInTheDocument()
  })

  it('applies correct size classes', () => {
    const { container, rerender } = render(<Avatar name="Test" size="xs" />)
    let avatarDiv = container.querySelector('.w-8')
    expect(avatarDiv).toBeInTheDocument()

    rerender(<Avatar name="Test" size="xl" />)
    avatarDiv = container.querySelector('.w-20')
    expect(avatarDiv).toBeInTheDocument()
  })

  it('applies correct variant classes', () => {
    const { container, rerender } = render(<Avatar name="Test" variant="blue" />)
    let avatarDiv = container.querySelector('.bg-blue-100')
    expect(avatarDiv).toBeInTheDocument()

    rerender(<Avatar name="Test" variant="gradient" />)
    avatarDiv = container.querySelector('.bg-gradient-to-br')
    expect(avatarDiv).toBeInTheDocument()
  })

  it('shows online indicator when showOnline is true', () => {
    const { container } = render(<Avatar name="Test" showOnline={true} />)
    const onlineIndicator = container.querySelector('[title="Online"]')
    expect(onlineIndicator).toBeInTheDocument()
  })

  it('does not show online indicator by default', () => {
    const { container } = render(<Avatar name="Test" />)
    const onlineIndicator = container.querySelector('[title="Online"]')
    expect(onlineIndicator).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<Avatar name="Test" className="custom-class" />)
    const wrapper = container.querySelector('.custom-class')
    expect(wrapper).toBeInTheDocument()
  })

  it('shows online indicator with image avatar', () => {
    const { container } = render(
      <Avatar 
        name="Test User" 
        avatarUrl="https://example.com/avatar.jpg" 
        showOnline={true} 
      />
    )
    const onlineIndicator = container.querySelector('[title="Online"]')
    expect(onlineIndicator).toBeInTheDocument()
  })

  it('capitalizes initial correctly', () => {
    render(<Avatar name="john" />)
    expect(screen.getByText('J')).toBeInTheDocument()
  })

  it('handles empty string name gracefully', () => {
    render(<Avatar name="" />)
    expect(screen.getByText('U')).toBeInTheDocument()
  })

  it('handles all size variants', () => {
    const sizes = ['xs', 'sm', 'md', 'lg', 'xl'] as const
    const sizeClasses = ['w-8', 'w-10', 'w-12', 'w-16', 'w-20']
    
    sizes.forEach((size, index) => {
      const { container } = render(<Avatar name="Test" size={size} />)
      const avatarDiv = container.querySelector(`.${sizeClasses[index]}`)
      expect(avatarDiv).toBeInTheDocument()
    })
  })

  it('handles all variant styles', () => {
    const variants = ['gradient', 'blue', 'emerald', 'purple', 'orange'] as const
    
    variants.forEach((variant) => {
      const { container } = render(<Avatar name="Test" variant={variant} />)
      const avatarDiv = container.firstChild?.firstChild
      expect(avatarDiv).toBeInTheDocument()
    })
  })
})
