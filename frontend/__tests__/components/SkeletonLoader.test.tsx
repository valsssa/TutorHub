import { render, screen } from '@testing-library/react'
import SkeletonLoader, { TutorCardSkeleton, TutorProfileSkeleton } from '@/components/SkeletonLoader'

describe('SkeletonLoader Component', () => {
  describe('Basic SkeletonLoader', () => {
    it('renders with default props', () => {
      const { container } = render(<SkeletonLoader />)
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('applies rectangular variant by default', () => {
      const { container } = render(<SkeletonLoader />)
      const skeleton = container.querySelector('.rounded-lg')
      expect(skeleton).toBeInTheDocument()
    })

    it('applies text variant', () => {
      const { container } = render(<SkeletonLoader variant="text" />)
      const skeleton = container.querySelector('.rounded')
      expect(skeleton).toBeInTheDocument()
    })

    it('applies circle variant', () => {
      const { container } = render(<SkeletonLoader variant="circle" />)
      const skeleton = container.querySelector('.rounded-full')
      expect(skeleton).toBeInTheDocument()
    })

    it('applies custom width and height', () => {
      const { container } = render(<SkeletonLoader width="200px" height="50px" />)
      const skeleton = container.firstChild as HTMLElement
      expect(skeleton.style.width).toBe('200px')
      expect(skeleton.style.height).toBe('50px')
    })

    it('applies custom className', () => {
      const { container } = render(<SkeletonLoader className="custom-class" />)
      const skeleton = container.querySelector('.custom-class')
      expect(skeleton).toBeInTheDocument()
    })

    it('renders multiple lines when lines prop is provided', () => {
      const { container } = render(<SkeletonLoader lines={3} />)
      const skeletons = container.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBe(3)
    })

    it('renders single line when lines is 1', () => {
      const { container } = render(<SkeletonLoader lines={1} />)
      const skeletons = container.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBe(1)
    })

    it('makes last line 80% width when multiple lines', () => {
      const { container } = render(<SkeletonLoader lines={3} width="100%" />)
      const skeletons = container.querySelectorAll('.animate-pulse')
      const lastSkeleton = skeletons[skeletons.length - 1] as HTMLElement
      expect(lastSkeleton.style.width).toBe('80%')
    })

    it('has proper animation classes', () => {
      const { container } = render(<SkeletonLoader />)
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toHaveClass('bg-gradient-to-r')
      expect(skeleton).toHaveClass('from-gray-200')
      expect(skeleton).toHaveClass('via-gray-300')
      expect(skeleton).toHaveClass('to-gray-200')
    })
  })

  describe('TutorCardSkeleton', () => {
    it('renders tutor card skeleton structure', () => {
      const { container } = render(<TutorCardSkeleton />)
      const card = container.querySelector('.bg-white.rounded-2xl')
      expect(card).toBeInTheDocument()
    })

    it('contains multiple skeleton elements', () => {
      const { container } = render(<TutorCardSkeleton />)
      const skeletons = container.querySelectorAll('.animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('has grid layout for stats', () => {
      const { container } = render(<TutorCardSkeleton />)
      const grid = container.querySelector('.grid-cols-2')
      expect(grid).toBeInTheDocument()
    })

    it('renders circular skeleton for avatar', () => {
      const { container } = render(<TutorCardSkeleton />)
      const circle = container.querySelector('.rounded-full')
      expect(circle).toBeInTheDocument()
    })

    it('has animate-pulse class on container', () => {
      const { container } = render(<TutorCardSkeleton />)
      const card = container.querySelector('.animate-pulse')
      expect(card).toBeInTheDocument()
    })
  })

  describe('TutorProfileSkeleton', () => {
    it('renders tutor profile skeleton structure', () => {
      const { container } = render(<TutorProfileSkeleton />)
      expect(container.firstChild).toBeInTheDocument()
    })

    it('has proper layout grid', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const grid = container.querySelector('.lg\\:grid-cols-12')
      expect(grid).toBeInTheDocument()
    })

    it('renders breadcrumb skeleton', () => {
      const { container } = render(<TutorProfileSkeleton />)
      // Check for container structure
      expect(container.querySelector('.container')).toBeInTheDocument()
    })

    it('renders hero header section', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const rounded = container.querySelectorAll('.rounded-3xl')
      expect(rounded.length).toBeGreaterThan(0)
    })

    it('renders video placeholder with aspect ratio', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const video = container.querySelector('.aspect-video')
      expect(video).toBeInTheDocument()
    })

    it('renders sidebar with sticky positioning', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const sticky = container.querySelector('.sticky')
      expect(sticky).toBeInTheDocument()
    })

    it('renders stats grid with 3 columns', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const statsGrid = container.querySelector('.grid-cols-3')
      expect(statsGrid).toBeInTheDocument()
    })

    it('has proper background styling', () => {
      const { container } = render(<TutorProfileSkeleton />)
      const bg = container.querySelector('.bg-slate-50')
      expect(bg).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('skeleton elements have no interactive content', () => {
      const { container } = render(<SkeletonLoader />)
      const buttons = container.querySelectorAll('button')
      const links = container.querySelectorAll('a')
      expect(buttons.length).toBe(0)
      expect(links.length).toBe(0)
    })

    it('tutor card skeleton has no interactive elements', () => {
      const { container } = render(<TutorCardSkeleton />)
      const buttons = container.querySelectorAll('button')
      const links = container.querySelectorAll('a')
      expect(buttons.length).toBe(0)
      expect(links.length).toBe(0)
    })
  })
})
