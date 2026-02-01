import { render, screen } from '@testing-library/react'
import Badge from '@/components/Badge'

describe('Badge Component', () => {
  it('renders children content', () => {
    render(<Badge>Test Badge</Badge>)
    expect(screen.getByText('Test Badge')).toBeInTheDocument()
  })

  it('applies default variant styles', () => {
    const { container } = render(<Badge>Default</Badge>)
    const badge = screen.getByText('Default')
    expect(badge).toHaveClass('bg-slate-100', 'text-slate-600')
  })

  it('applies verified variant with shield icon', () => {
    const { container } = render(<Badge variant="verified">Verified</Badge>)
    const badge = screen.getByText('Verified')
    expect(badge).toHaveClass('bg-emerald-100', 'text-emerald-700')
    
    // Check for shield icon
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies approved variant with shield icon', () => {
    const { container } = render(<Badge variant="approved">Approved</Badge>)
    const badge = screen.getByText('Approved')
    expect(badge).toHaveClass('bg-emerald-100', 'text-emerald-700')
    
    // Check for shield icon
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('applies pending variant styles', () => {
    render(<Badge variant="pending">Pending</Badge>)
    const badge = screen.getByText('Pending')
    expect(badge).toHaveClass('bg-amber-100', 'text-amber-700')
  })

  it('applies rejected variant styles', () => {
    render(<Badge variant="rejected">Rejected</Badge>)
    const badge = screen.getByText('Rejected')
    expect(badge).toHaveClass('bg-red-100', 'text-red-700')
  })

  it('applies admin role variant', () => {
    render(<Badge variant="admin">Admin</Badge>)
    const badge = screen.getByText('Admin')
    expect(badge).toHaveClass('bg-red-100', 'text-red-800')
  })

  it('applies tutor role variant', () => {
    render(<Badge variant="tutor">Tutor</Badge>)
    const badge = screen.getByText('Tutor')
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800')
  })

  it('applies student role variant', () => {
    render(<Badge variant="student">Student</Badge>)
    const badge = screen.getByText('Student')
    expect(badge).toHaveClass('bg-emerald-100', 'text-emerald-800')
  })

  it('applies custom className', () => {
    render(<Badge className="custom-badge">Test</Badge>)
    const badge = screen.getByText('Test')
    expect(badge).toHaveClass('custom-badge')
  })

  it('does not show shield icon for non-verified variants', () => {
    const { container } = render(<Badge variant="pending">Pending</Badge>)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeInTheDocument()
  })

  it('renders with multiple children elements', () => {
    render(
      <Badge>
        <span>Multiple</span>
        <span>Elements</span>
      </Badge>
    )
    expect(screen.getByText('Multiple')).toBeInTheDocument()
    expect(screen.getByText('Elements')).toBeInTheDocument()
  })

  it('has correct base classes', () => {
    render(<Badge>Test</Badge>)
    const badge = screen.getByText('Test')
    expect(badge).toHaveClass(
      'inline-flex',
      'items-center',
      'px-2',
      'py-0.5',
      'rounded',
      'text-xs',
      'font-medium',
      'border'
    )
  })
})
