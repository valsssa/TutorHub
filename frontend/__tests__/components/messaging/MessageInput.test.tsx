/**
 * Tests for MessageInput component
 * Tests user interaction for sending messages
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MessageInput from '@/components/messaging/MessageInput';

describe('MessageInput', () => {
  const mockOnSend = jest.fn();
  const mockOnTyping = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input field and send button', () => {
    render(<MessageInput onSend={mockOnSend} />);

    expect(screen.getByPlaceholderText(/write your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('sends message when button is clicked', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'Hello, tutor!');

    const sendButton = screen.getByRole('button');
    await user.click(sendButton);

    expect(mockOnSend).toHaveBeenCalledWith('Hello, tutor!');
  });

  it('sends message when Enter key is pressed', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'Test message{enter}');

    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('does not send message when Shift+Enter is pressed', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'Line 1{shift>}{enter}{/shift}Line 2');

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('clears input after sending', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'My message');
    await user.click(screen.getByRole('button'));

    expect(input).toHaveValue('');
  });

  it('does not send empty message', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const sendButton = screen.getByRole('button');
    await user.click(sendButton);

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('does not send whitespace-only message', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, '   ');
    await user.click(screen.getByRole('button'));

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('calls onTyping when user types', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} onTyping={mockOnTyping} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'a');

    expect(mockOnTyping).toHaveBeenCalled();
  });

  it('disables input when disabled prop is true', () => {
    render(<MessageInput onSend={mockOnSend} disabled={true} />);

    expect(screen.getByPlaceholderText(/write your message/i)).toBeDisabled();
  });

  it('disables send button when disabled', () => {
    render(<MessageInput onSend={mockOnSend} disabled={true} />);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('disables send button when input is empty', () => {
    render(<MessageInput onSend={mockOnSend} />);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('enables send button when there is content', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} />);

    const input = screen.getByPlaceholderText(/write your message/i);
    await user.type(input, 'Test');

    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('shows loading state when isLoading is true', () => {
    render(<MessageInput onSend={mockOnSend} isLoading={true} />);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('displays keyboard hint text', () => {
    render(<MessageInput onSend={mockOnSend} />);

    expect(screen.getByText(/press enter to send/i)).toBeInTheDocument();
    expect(screen.getByText(/shift\+enter/i)).toBeInTheDocument();
  });
});
