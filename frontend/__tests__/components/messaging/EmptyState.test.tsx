/**
 * Tests for EmptyState component
 * Tests empty state display for messaging
 */

import { render, screen } from '@testing-library/react';
import EmptyState from '@/components/messaging/EmptyState';

describe('EmptyState', () => {
  it('renders with default title and message', () => {
    render(<EmptyState />);

    expect(screen.getByRole('heading', { name: /select a conversation/i })).toBeInTheDocument();
    expect(screen.getByText(/choose a thread from the left/i)).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(<EmptyState title="No messages yet" />);

    expect(screen.getByRole('heading', { name: /no messages yet/i })).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<EmptyState message="Start a new conversation to get started" />);

    expect(screen.getByText(/start a new conversation/i)).toBeInTheDocument();
  });

  it('renders message icon', () => {
    render(<EmptyState />);

    // Icon should be in the document with aria-hidden
    const icon = document.querySelector('svg[aria-hidden="true"]');
    expect(icon).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<EmptyState />);

    const container = screen.getByRole('status');
    expect(container).toHaveAttribute('aria-label', 'No conversation selected');
  });

  it('displays hint text about message appearance', () => {
    render(<EmptyState />);

    expect(screen.getByText(/your messages will appear here/i)).toBeInTheDocument();
  });
});
