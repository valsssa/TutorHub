import { render, screen } from '@testing-library/react'
import Loading from '@/app/loading'

describe('Loading Page Component', () => {
  it('renders loading indicator', () => {
    const { container } = render(<Loading />)
    expect(container.firstChild).toBeInTheDocument()
  })

  it('displays loading text', () => {
    render(<Loading />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays descriptive message', () => {
    render(<Loading />)
    expect(screen.getByText('Please wait while we load your content')).toBeInTheDocument()
  })

  it('has spinner animation', () => {
    const { container } = render(<Loading />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toBeInTheDocument()
  })

  it('spinner has proper styling', () => {
    const { container } = render(<Loading />)
    const spinner = container.querySelector('.animate-spin')
    expect(spinner).toHaveClass(
      'w-16',
      'h-16',
      'border-4',
      'border-blue-200',
      'border-t-blue-600',
      'rounded-full'
    )
  })

  it('is centered on screen', () => {
    const { container } = render(<Loading />)
    const wrapper = container.querySelector('.min-h-screen')
    expect(wrapper).toHaveClass('flex', 'items-center', 'justify-center')
  })

  it('has proper background color', () => {
    const { container } = render(<Loading />)
    const wrapper = container.querySelector('.min-h-screen')
    expect(wrapper).toHaveClass('bg-gray-50')
  })

  it('content is centered', () => {
    const { container } = render(<Loading />)
    const content = container.querySelector('.text-center')
    expect(content).toBeInTheDocument()
  })

  it('heading has correct styling', () => {
    render(<Loading />)
    const heading = screen.getByText('Loading...')
    expect(heading).toHaveClass('text-xl', 'font-semibold', 'text-gray-700', 'mb-2')
  })

  it('description has correct styling', () => {
    render(<Loading />)
    const description = screen.getByText('Please wait while we load your content')
    expect(description).toHaveClass('text-gray-500')
  })

  it('spinner wrapper has correct size', () => {
    const { container } = render(<Loading />)
    const spinnerWrapper = container.querySelector('.w-16.h-16')
    expect(spinnerWrapper).toBeInTheDocument()
  })
})
