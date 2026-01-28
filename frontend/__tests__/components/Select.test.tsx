import { render, screen, fireEvent } from '@testing-library/react'
import Select from '@/components/Select'

describe('Select Component', () => {
  const mockOptions = [
    { value: '1', label: 'Option 1' },
    { value: '2', label: 'Option 2' },
    { value: '3', label: 'Option 3' },
  ]

  it('renders select with options', () => {
    render(<Select options={mockOptions} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('Option 1')).toBeInTheDocument()
    expect(screen.getByText('Option 2')).toBeInTheDocument()
    expect(screen.getByText('Option 3')).toBeInTheDocument()
  })

  it('renders with label', () => {
    render(<Select label="Choose Option" options={mockOptions} />)
    expect(screen.getByText('Choose Option')).toBeInTheDocument()
    expect(screen.getByLabelText('Choose Option')).toBeInTheDocument()
  })

  it('renders placeholder option when provided', () => {
    render(<Select options={mockOptions} placeholder="Select an option" />)
    expect(screen.getByText('Select an option')).toBeInTheDocument()
    
    const placeholderOption = screen.getByRole('option', { name: 'Select an option' })
    expect(placeholderOption).toHaveAttribute('value', '')
    expect(placeholderOption).toHaveAttribute('disabled')
  })

  it('displays error message when error prop is provided', () => {
    render(<Select options={mockOptions} error="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('applies error styling when error is present', () => {
    render(<Select options={mockOptions} error="Error message" />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveClass('border-red-500')
  })

  it('displays helper text when provided and no error', () => {
    render(<Select options={mockOptions} helperText="Please select an option" />)
    expect(screen.getByText('Please select an option')).toBeInTheDocument()
  })

  it('does not display helper text when error is present', () => {
    render(
      <Select 
        options={mockOptions} 
        helperText="Helper text" 
        error="Error message" 
      />
    )
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('handles onChange event', () => {
    const mockOnChange = jest.fn()
    render(<Select options={mockOptions} onChange={mockOnChange} />)
    
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: '2' } })
    
    expect(mockOnChange).toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<Select options={mockOptions} className="custom-select" />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveClass('custom-select')
  })

  it('generates unique id from label', () => {
    render(<Select label="My Label" options={mockOptions} />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveAttribute('id', 'select-my-label')
  })

  it('uses provided id over generated one', () => {
    render(<Select label="My Label" options={mockOptions} id="custom-id" />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveAttribute('id', 'custom-id')
  })

  it('passes through native select attributes', () => {
    render(
      <Select 
        options={mockOptions} 
        disabled 
        required 
        name="test-select"
      />
    )
    const select = screen.getByRole('combobox')
    expect(select).toBeDisabled()
    expect(select).toBeRequired()
    expect(select).toHaveAttribute('name', 'test-select')
  })

  it('renders with numeric option values', () => {
    const numericOptions = [
      { value: 1, label: 'One' },
      { value: 2, label: 'Two' },
      { value: 3, label: 'Three' },
    ]
    render(<Select options={numericOptions} />)
    expect(screen.getByText('One')).toBeInTheDocument()
    expect(screen.getByText('Two')).toBeInTheDocument()
    expect(screen.getByText('Three')).toBeInTheDocument()
  })

  it('has correct base styling classes', () => {
    render(<Select options={mockOptions} />)
    const select = screen.getByRole('combobox')
    expect(select).toHaveClass(
      'w-full',
      'px-3',
      'py-2',
      'border',
      'rounded-lg',
      'shadow-sm',
      'bg-white'
    )
  })

  it('handles error as string', () => {
    render(<Select options={mockOptions} error="String error" />)
    expect(screen.getByText('String error')).toBeInTheDocument()
  })

  it('converts non-string error to string', () => {
    const errorObject = { message: 'Object error' }
    render(<Select options={mockOptions} error={errorObject as any} />)
    expect(screen.getByText('[object Object]')).toBeInTheDocument()
  })

  it('renders empty options array', () => {
    render(<Select options={[]} />)
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
    expect(select.children.length).toBe(0)
  })

  it('label associates correctly with select element', () => {
    render(<Select label="Test Label" options={mockOptions} />)
    const label = screen.getByText('Test Label')
    const select = screen.getByRole('combobox')
    
    expect(label).toHaveAttribute('for', select.id)
  })
})
