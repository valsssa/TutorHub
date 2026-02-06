import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Input } from '@/components/ui/input';

describe('Input', () => {
  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('renders without label', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText(/enter text/i)).toBeInTheDocument();
  });

  it('shows error message', () => {
    render(<Input label="Email" error="Invalid email address" />);
    expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
  });

  it('applies error styling when error is present', () => {
    render(<Input label="Email" error="Invalid email" />);
    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveClass('border-red-500');
  });

  it('shows hint text when no error', () => {
    render(<Input label="Password" hint="Minimum 8 characters" />);
    expect(screen.getByText(/minimum 8 characters/i)).toBeInTheDocument();
  });

  it('hides hint text when error is present', () => {
    render(
      <Input
        label="Password"
        hint="Minimum 8 characters"
        error="Password is required"
      />
    );
    expect(screen.queryByText(/minimum 8 characters/i)).not.toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<Input label="Disabled" disabled />);
    const input = screen.getByLabelText(/disabled/i);
    expect(input).toBeDisabled();
  });

  it('applies disabled styling', () => {
    render(<Input label="Disabled" disabled />);
    const input = screen.getByLabelText(/disabled/i);
    expect(input).toHaveClass('disabled:opacity-50');
  });

  it('accepts user input', async () => {
    const user = userEvent.setup();
    render(<Input label="Name" />);

    const input = screen.getByLabelText(/name/i);
    await user.type(input, 'John Doe');
    expect(input).toHaveValue('John Doe');
  });

  it('calls onChange handler', async () => {
    const user = userEvent.setup();
    const handleChange = vi.fn();
    render(<Input label="Name" onChange={handleChange} />);

    await user.type(screen.getByLabelText(/name/i), 'a');
    expect(handleChange).toHaveBeenCalled();
  });

  it('renders with different input types', () => {
    const { rerender } = render(<Input label="Email" type="email" />);
    expect(screen.getByLabelText(/email/i)).toHaveAttribute('type', 'email');

    rerender(<Input label="Password" type="password" />);
    expect(screen.getByLabelText(/password/i)).toHaveAttribute('type', 'password');

    rerender(<Input label="Number" type="number" />);
    expect(screen.getByLabelText(/number/i)).toHaveAttribute('type', 'number');
  });

  it('merges custom className', () => {
    render(<Input label="Custom" className="custom-class" />);
    const input = screen.getByLabelText(/custom/i);
    expect(input).toHaveClass('custom-class');
  });

  it('generates unique id when not provided', () => {
    render(
      <>
        <Input label="First" />
        <Input label="Second" />
      </>
    );
    const firstInput = screen.getByLabelText(/first/i);
    const secondInput = screen.getByLabelText(/second/i);
    expect(firstInput.id).not.toBe(secondInput.id);
  });

  it('uses provided id', () => {
    render(<Input label="Custom ID" id="my-custom-id" />);
    const input = screen.getByLabelText(/custom id/i);
    expect(input).toHaveAttribute('id', 'my-custom-id');
  });
});
