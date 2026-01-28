import { render, screen } from './test-utils'
import NotFound from '../app/not-found'
import Error from '../app/error'
import Loading from '../app/loading'
import '@testing-library/jest-dom'

// Mock Next.js Link component
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return <a href={href}>{children}</a>
  }
})

describe('Error Pages', () => {
  describe('404 Not Found Page', () => {
    it('renders 404 page with correct heading', () => {
      render(<NotFound />)
      expect(screen.getByText('404')).toBeInTheDocument()
      expect(screen.getByText('Page Not Found')).toBeInTheDocument()
    })

    it('displays error message', () => {
      render(<NotFound />)
      expect(
        screen.getByText(/Sorry, we couldn't find the page you're looking for/i)
      ).toBeInTheDocument()
    })

    it('renders action buttons', () => {
      render(<NotFound />)
      expect(screen.getByText('Go to Homepage')).toBeInTheDocument()
      expect(screen.getByText('Go Back')).toBeInTheDocument()
    })

    it('renders helpful links', () => {
      render(<NotFound />)
      expect(screen.getByText('Browse Tutors')).toBeInTheDocument()
      expect(screen.getByText('My Bookings')).toBeInTheDocument()
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Help Center')).toBeInTheDocument()
    })

    it('contains correct link hrefs', () => {
      render(<NotFound />)
      const homepageLink = screen.getByRole('link', { name: /Go to Homepage/i })
      expect(homepageLink).toHaveAttribute('href', '/')
    })
  })

  describe('Generic Error Page', () => {
    const mockError = new Error('Test error message')
    const mockReset = jest.fn()

    beforeEach(() => {
      // Mock console.error to avoid cluttering test output
      jest.spyOn(console, 'error').mockImplementation(() => {})
    })

    afterEach(() => {
      jest.restoreAllMocks()
    })

    it('renders error page with correct heading', () => {
      render(<Error error={mockError} reset={mockReset} />)
      expect(screen.getByText('Oops!')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('displays error description', () => {
      render(<Error error={mockError} reset={mockReset} />)
      expect(
        screen.getByText(/We encountered an unexpected error/i)
      ).toBeInTheDocument()
    })

    it('renders Try Again button', () => {
      render(<Error error={mockError} reset={mockReset} />)
      expect(screen.getByText('Try Again')).toBeInTheDocument()
    })

    it('renders Go to Homepage button', () => {
      render(<Error error={mockError} reset={mockReset} />)
      expect(screen.getByText('Go to Homepage')).toBeInTheDocument()
    })

    it('calls reset function when Try Again is clicked', () => {
      render(<Error error={mockError} reset={mockReset} />)
      const tryAgainButton = screen.getByText('Try Again')
      tryAgainButton.click()
      expect(mockReset).toHaveBeenCalledTimes(1)
    })

    it('displays error message in development mode', () => {
      const originalEnv = process.env.NODE_ENV
      process.env.NODE_ENV = 'development'

      render(<Error error={mockError} reset={mockReset} />)
      expect(screen.getByText(/Test error message/i)).toBeInTheDocument()

      process.env.NODE_ENV = originalEnv
    })

    it('logs error to console on mount', () => {
      const consoleErrorSpy = jest.spyOn(console, 'error')
      render(<Error error={mockError} reset={mockReset} />)
      expect(consoleErrorSpy).toHaveBeenCalledWith('Application error:', mockError)
    })

    it('renders support links', () => {
      render(<Error error={mockError} reset={mockReset} />)
      expect(screen.getByText('Contact Support')).toBeInTheDocument()
      expect(screen.getByText('Email Us')).toBeInTheDocument()
    })
  })

  describe('Loading Page', () => {
    it('renders loading spinner', () => {
      render(<Loading />)
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('displays loading message', () => {
      render(<Loading />)
      expect(
        screen.getByText('Please wait while we load your content')
      ).toBeInTheDocument()
    })

    it('contains spinner animation element', () => {
      const { container } = render(<Loading />)
      const spinner = container.querySelector('.animate-spin')
      expect(spinner).toBeInTheDocument()
    })
  })
})
