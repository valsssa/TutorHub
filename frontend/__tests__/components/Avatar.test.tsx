/**
 * Tests for Avatar component.
 *
 * Tests cover:
 * - Rendering with image URL
 * - Rendering with initials fallback
 * - Deterministic color generation
 * - Size variants
 * - Online indicator
 * - Legacy variant support
 * - Accessibility
 */

import { render, screen } from '@testing-library/react'
import Avatar from '@/components/Avatar'

// Mock Next.js Image component
jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt, ...props }: { src: string; alt: string; [key: string]: unknown }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} {...props} data-testid="avatar-image" />
  ),
}))

describe('Avatar Component', () => {
  describe('image rendering', () => {
    it('renders image when valid avatarUrl is provided', () => {
      render(
        <Avatar
          name="John Doe"
          avatarUrl="https://example.com/avatar.jpg"
        />
      )

      const image = screen.getByTestId('avatar-image')
      expect(image).toBeInTheDocument()
      expect(image).toHaveAttribute('src', 'https://example.com/avatar.jpg')
      expect(image).toHaveAttribute('alt', 'Avatar for John Doe')
    })

    it('renders initials when avatarUrl is null', () => {
      render(<Avatar name="John Doe" avatarUrl={null} />)

      expect(screen.queryByTestId('avatar-image')).not.toBeInTheDocument()
      expect(screen.getByText('JD')).toBeInTheDocument()
    })

    it('does not render image for ui-avatars.com URLs (placeholder)', () => {
      render(
        <Avatar
          name="John Doe"
          avatarUrl="https://ui-avatars.com/api/?name=John"
        />
      )

      expect(screen.queryByTestId('avatar-image')).not.toBeInTheDocument()
      expect(screen.getByText('JD')).toBeInTheDocument()
    })

    it('does not render image for placehold.co URLs', () => {
      render(
        <Avatar
          name="Jane Smith"
          avatarUrl="https://placehold.co/100x100"
        />
      )

      expect(screen.queryByTestId('avatar-image')).not.toBeInTheDocument()
      expect(screen.getByText('JS')).toBeInTheDocument()
    })
  })

  describe('initials generation', () => {
    it('extracts initials from first and last name', () => {
      render(<Avatar name="John Doe" />)
      expect(screen.getByText('JD')).toBeInTheDocument()
    })

    it('extracts initials from multiple names (first and last)', () => {
      render(<Avatar name="John Michael Doe" />)
      expect(screen.getByText('JD')).toBeInTheDocument()
    })

    it('uses first two letters for single name', () => {
      render(<Avatar name="Madonna" />)
      expect(screen.getByText('MA')).toBeInTheDocument()
    })

    it('handles single character name', () => {
      render(<Avatar name="X" />)
      expect(screen.getByText('X')).toBeInTheDocument()
    })

    it('handles empty name with fallback ??', () => {
      render(<Avatar name="" />)
      expect(screen.getByText('??')).toBeInTheDocument()
    })

    it('uses default name "User" -> "US" when not provided', () => {
      render(<Avatar />)
      expect(screen.getByText('US')).toBeInTheDocument()
    })

    it('capitalizes initials correctly', () => {
      render(<Avatar name="john doe" />)
      expect(screen.getByText('JD')).toBeInTheDocument()
    })
  })

  describe('size variants', () => {
    it('applies xs size classes', () => {
      const { container } = render(<Avatar name="Test" size="xs" />)
      const avatar = container.querySelector('.w-8.h-8')
      expect(avatar).toBeInTheDocument()
    })

    it('applies sm size classes', () => {
      const { container } = render(<Avatar name="Test" size="sm" />)
      const avatar = container.querySelector('.w-10.h-10')
      expect(avatar).toBeInTheDocument()
    })

    it('applies md size classes (default)', () => {
      const { container } = render(<Avatar name="Test" />)
      const avatar = container.querySelector('.w-12.h-12')
      expect(avatar).toBeInTheDocument()
    })

    it('applies lg size classes', () => {
      const { container } = render(<Avatar name="Test" size="lg" />)
      const avatar = container.querySelector('.w-16.h-16')
      expect(avatar).toBeInTheDocument()
    })

    it('applies xl size classes', () => {
      const { container } = render(<Avatar name="Test" size="xl" />)
      const avatar = container.querySelector('.w-20.h-20')
      expect(avatar).toBeInTheDocument()
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
  })

  describe('color variants', () => {
    it('uses auto variant by default (deterministic color)', () => {
      const { container } = render(<Avatar name="John Doe" />)
      // Should have a color class from the palette
      const avatar = container.querySelector('[class*="bg-"]')
      expect(avatar).toBeInTheDocument()
    })

    it('applies gradient variant', () => {
      const { container } = render(<Avatar name="Test" variant="gradient" />)
      const avatar = container.querySelector('.bg-gradient-to-br')
      expect(avatar).toBeInTheDocument()
    })

    it('applies blue variant', () => {
      const { container } = render(<Avatar name="Test" variant="blue" />)
      const avatar = container.querySelector('.bg-blue-500')
      expect(avatar).toBeInTheDocument()
    })

    it('applies emerald variant', () => {
      const { container } = render(<Avatar name="Test" variant="emerald" />)
      const avatar = container.querySelector('.bg-emerald-500')
      expect(avatar).toBeInTheDocument()
    })

    it('applies purple variant', () => {
      const { container } = render(<Avatar name="Test" variant="purple" />)
      const avatar = container.querySelector('.bg-purple-500')
      expect(avatar).toBeInTheDocument()
    })

    it('applies orange variant', () => {
      const { container } = render(<Avatar name="Test" variant="orange" />)
      const avatar = container.querySelector('.bg-orange-500')
      expect(avatar).toBeInTheDocument()
    })

    it('handles all legacy variant styles', () => {
      const variants = ['gradient', 'blue', 'emerald', 'purple', 'orange'] as const

      variants.forEach((variant) => {
        const { container } = render(<Avatar name="Test" variant={variant} />)
        const avatarDiv = container.firstChild?.firstChild
        expect(avatarDiv).toBeInTheDocument()
      })
    })

    it('generates consistent color for same userId', () => {
      const { container: container1 } = render(
        <Avatar name="John Doe" userId={42} />
      )
      const { container: container2 } = render(
        <Avatar name="Different Name" userId={42} />
      )

      const avatar1Classes = container1.querySelector('[role="img"]')?.className
      const avatar2Classes = container2.querySelector('[role="img"]')?.className

      // Same userId should produce same color classes
      expect(avatar1Classes).toBe(avatar2Classes)
    })

    it('generates consistent color for same name when no userId', () => {
      const { container: container1 } = render(<Avatar name="John Doe" />)
      const { container: container2 } = render(<Avatar name="John Doe" />)

      const avatar1Classes = container1.querySelector('[role="img"]')?.className
      const avatar2Classes = container2.querySelector('[role="img"]')?.className

      expect(avatar1Classes).toBe(avatar2Classes)
    })
  })

  describe('online indicator', () => {
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
  })

  describe('accessibility', () => {
    it('has proper alt text for image', () => {
      render(
        <Avatar
          name="John Doe"
          avatarUrl="https://example.com/avatar.jpg"
        />
      )

      const image = screen.getByTestId('avatar-image')
      expect(image).toHaveAttribute('alt', 'Avatar for John Doe')
    })

    it('has aria-label for initials avatar', () => {
      render(<Avatar name="Jane Smith" />)

      const avatar = screen.getByRole('img')
      expect(avatar).toHaveAttribute('aria-label', 'Avatar for Jane Smith')
    })

    it('has default aria-label for empty name', () => {
      render(<Avatar name="" />)

      const avatar = screen.getByRole('img')
      expect(avatar).toHaveAttribute('aria-label', 'User avatar')
    })

    it('online indicator has aria-label', () => {
      render(<Avatar name="Test" showOnline />)

      const indicator = screen.getByRole('status')
      expect(indicator).toHaveAttribute('aria-label', 'Online')
    })
  })

  describe('className prop', () => {
    it('applies custom className', () => {
      const { container } = render(
        <Avatar name="Test" className="custom-class" />
      )

      const wrapper = container.querySelector('.custom-class')
      expect(wrapper).toBeInTheDocument()
    })
  })
})
