import { render, screen } from '@testing-library/react'
import ProgressBar from '@/components/ProgressBar'

// Mock framer-motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, animate, initial, transition, className, ...props }: any) => (
      <div className={className} {...props}>
        {children}
      </div>
    ),
  },
}))

describe('ProgressBar Component', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  it('renders progress bar', () => {
    const { container } = render(<ProgressBar value={50} />)
    const progressBar = container.querySelector('.bg-gray-200')
    expect(progressBar).toBeInTheDocument()
  })

  it('displays percentage by default', () => {
    render(<ProgressBar value={75} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('hides percentage when showPercentage is false', () => {
    render(<ProgressBar value={50} showPercentage={false} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.queryByText('50%')).not.toBeInTheDocument()
  })

  it('displays label when provided', () => {
    render(<ProgressBar value={60} label="Loading" />)
    expect(screen.getByText('Loading')).toBeInTheDocument()
  })

  it('displays icon when provided', () => {
    render(<ProgressBar value={40} icon="📊" />)
    expect(screen.getByText('📊')).toBeInTheDocument()
  })

  it('applies blue color variant by default', () => {
    const { container } = render(<ProgressBar value={50} />)
    const progressFill = container.querySelector('.from-blue-500')
    expect(progressFill).toBeInTheDocument()
  })

  it('applies green color variant', () => {
    const { container } = render(<ProgressBar value={50} color="green" />)
    const progressFill = container.querySelector('.from-green-500')
    expect(progressFill).toBeInTheDocument()
  })

  it('applies amber color variant', () => {
    const { container } = render(<ProgressBar value={50} color="amber" />)
    const progressFill = container.querySelector('.from-amber-500')
    expect(progressFill).toBeInTheDocument()
  })

  it('applies rose color variant', () => {
    const { container } = render(<ProgressBar value={50} color="rose" />)
    const progressFill = container.querySelector('.from-rose-500')
    expect(progressFill).toBeInTheDocument()
  })

  it('applies purple color variant', () => {
    const { container } = render(<ProgressBar value={50} color="purple" />)
    const progressFill = container.querySelector('.from-purple-500')
    expect(progressFill).toBeInTheDocument()
  })

  it('applies small size', () => {
    const { container } = render(<ProgressBar value={50} size="sm" />)
    const progressBar = container.querySelector('.h-2')
    expect(progressBar).toBeInTheDocument()
  })

  it('applies medium size by default', () => {
    const { container } = render(<ProgressBar value={50} />)
    const progressBar = container.querySelector('.h-3')
    expect(progressBar).toBeInTheDocument()
  })

  it('applies large size', () => {
    const { container } = render(<ProgressBar value={50} size="lg" />)
    const progressBar = container.querySelector('.h-4')
    expect(progressBar).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(<ProgressBar value={50} className="custom-progress" />)
    const wrapper = container.querySelector('.custom-progress')
    expect(wrapper).toBeInTheDocument()
  })

  it('clamps value to 0-100 range (too low)', () => {
    render(<ProgressBar value={-10} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('clamps value to 0-100 range (too high)', () => {
    render(<ProgressBar value={150} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('rounds percentage to nearest integer', () => {
    render(<ProgressBar value={33.7} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('34%')).toBeInTheDocument()
  })

  it('handles zero value', () => {
    render(<ProgressBar value={0} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('0%')).toBeInTheDocument()
  })

  it('handles 100% value', () => {
    render(<ProgressBar value={100} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('shows label and percentage together', () => {
    render(<ProgressBar value={50} label="Progress" showPercentage={true} />)
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('Progress')).toBeInTheDocument()
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('shows label, icon, and percentage together', () => {
    render(
      <ProgressBar 
        value={75} 
        label="Loading" 
        icon="⏳" 
        showPercentage={true} 
      />
    )
    
    jest.advanceTimersByTime(200)
    
    expect(screen.getByText('Loading')).toBeInTheDocument()
    expect(screen.getByText('⏳')).toBeInTheDocument()
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('renders all color variants correctly', () => {
    const colors = ['blue', 'green', 'amber', 'rose', 'purple'] as const
    const colorClasses = [
      'from-blue-500',
      'from-green-500',
      'from-amber-500',
      'from-rose-500',
      'from-purple-500',
    ]

    colors.forEach((color, index) => {
      const { container } = render(<ProgressBar value={50} color={color} />)
      const progressFill = container.querySelector(`.${colorClasses[index]}`)
      expect(progressFill).toBeInTheDocument()
    })
  })

  it('updates value when prop changes', () => {
    const { rerender } = render(<ProgressBar value={30} />)
    
    jest.advanceTimersByTime(200)
    expect(screen.getByText('30%')).toBeInTheDocument()
    
    rerender(<ProgressBar value={70} />)
    jest.advanceTimersByTime(200)
    expect(screen.getByText('70%')).toBeInTheDocument()
  })
})
