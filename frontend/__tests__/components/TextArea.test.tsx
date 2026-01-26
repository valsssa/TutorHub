import { render, screen, fireEvent } from '@testing-library/react'
import TextArea from '@/components/TextArea'

describe('TextArea Component', () => {
  it('renders textarea element', () => {
    render(<TextArea />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('renders with label', () => {
    render(<TextArea label="Description" />)
    expect(screen.getByText('Description')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
  })

  it('displays error message when error prop is provided', () => {
    render(<TextArea error="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
  })

  it('applies error styling when error is present', () => {
    render(<TextArea error="Error message" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('border-red-500')
  })

  it('displays helper text when provided and no error', () => {
    render(<TextArea helperText="Enter your message here" />)
    expect(screen.getByText('Enter your message here')).toBeInTheDocument()
  })

  it('does not display helper text when error is present', () => {
    render(
      <TextArea 
        helperText="Helper text" 
        error="Error message" 
      />
    )
    expect(screen.queryByText('Helper text')).not.toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
  })

  it('handles onChange event', () => {
    const mockOnChange = jest.fn()
    render(<TextArea onChange={mockOnChange} />)
    
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'New text' } })
    
    expect(mockOnChange).toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<TextArea className="custom-textarea" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('custom-textarea')
  })

  it('generates unique id from label', () => {
    render(<TextArea label="My Label" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveAttribute('id', 'textarea-my-label')
  })

  it('uses provided id over generated one', () => {
    render(<TextArea label="My Label" id="custom-id" />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveAttribute('id', 'custom-id')
  })

  it('passes through native textarea attributes', () => {
    render(
      <TextArea 
        disabled 
        required 
        name="test-textarea"
        placeholder="Enter text"
        rows={5}
        maxLength={200}
      />
    )
    const textarea = screen.getByRole('textbox')
    expect(textarea).toBeDisabled()
    expect(textarea).toBeRequired()
    expect(textarea).toHaveAttribute('name', 'test-textarea')
    expect(textarea).toHaveAttribute('placeholder', 'Enter text')
    expect(textarea).toHaveAttribute('rows', '5')
    expect(textarea).toHaveAttribute('maxlength', '200')
  })

  it('has correct base styling classes', () => {
    render(<TextArea />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass(
      'w-full',
      'px-3',
      'py-2',
      'border',
      'rounded-lg',
      'shadow-sm',
      'resize-none'
    )
  })

  it('handles error as string', () => {
    render(<TextArea error="String error" />)
    expect(screen.getByText('String error')).toBeInTheDocument()
  })

  it('converts non-string error to string', () => {
    const errorObject = { message: 'Object error' }
    render(<TextArea error={errorObject as any} />)
    expect(screen.getByText('[object Object]')).toBeInTheDocument()
  })

  it('label associates correctly with textarea element', () => {
    render(<TextArea label="Test Label" />)
    const label = screen.getByText('Test Label')
    const textarea = screen.getByRole('textbox')
    
    expect(label).toHaveAttribute('for', textarea.id)
  })

  it('handles focus and blur events', () => {
    const mockOnFocus = jest.fn()
    const mockOnBlur = jest.fn()
    render(<TextArea onFocus={mockOnFocus} onBlur={mockOnBlur} />)
    
    const textarea = screen.getByRole('textbox')
    
    fireEvent.focus(textarea)
    expect(mockOnFocus).toHaveBeenCalledTimes(1)
    
    fireEvent.blur(textarea)
    expect(mockOnBlur).toHaveBeenCalledTimes(1)
  })

  it('displays default value', () => {
    render(<TextArea defaultValue="Default text" />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    expect(textarea.value).toBe('Default text')
  })

  it('displays controlled value', () => {
    const { rerender } = render(<TextArea value="Controlled text" onChange={() => {}} />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    expect(textarea.value).toBe('Controlled text')
    
    rerender(<TextArea value="Updated text" onChange={() => {}} />)
    expect(textarea.value).toBe('Updated text')
  })

  it('applies normal border color when no error', () => {
    render(<TextArea />)
    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveClass('border-gray-300')
  })
})
