/**
 * Tests for ConnectionStatus component
 * Tests WebSocket connection status display and accessibility
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConnectionStatus, { ConnectionStatusDot, ConnectionStatusBanner } from '@/components/messaging/ConnectionStatus';

describe('ConnectionStatus', () => {
  describe('main component', () => {
    it('shows "Live" when connected', () => {
      render(<ConnectionStatus isConnected={true} connectionState="connected" />);

      expect(screen.getByText('Live')).toBeInTheDocument();
    });

    it('shows "Connecting" when connecting', () => {
      render(<ConnectionStatus isConnected={false} connectionState="connecting" />);

      expect(screen.getByText('Connecting')).toBeInTheDocument();
    });

    it('shows reconnection attempt count when reconnecting', () => {
      render(
        <ConnectionStatus
          isConnected={false}
          connectionState="reconnecting"
          reconnectAttempts={3}
          maxReconnectAttempts={10}
        />
      );

      expect(screen.getByText(/reconnecting \(3\/10\)/i)).toBeInTheDocument();
    });

    it('shows "Connection Failed" when failed', () => {
      render(<ConnectionStatus isConnected={false} connectionState="failed" />);

      expect(screen.getByText('Connection Failed')).toBeInTheDocument();
    });

    it('shows "Disconnected" when disconnected', () => {
      render(<ConnectionStatus isConnected={false} connectionState="disconnected" />);

      expect(screen.getByText('Disconnected')).toBeInTheDocument();
    });

    it('shows "Offline" when not online', () => {
      render(<ConnectionStatus isConnected={false} isOnline={false} />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('shows reconnect button when failed', () => {
      const mockReconnect = jest.fn();
      render(
        <ConnectionStatus
          isConnected={false}
          connectionState="failed"
          onReconnect={mockReconnect}
        />
      );

      expect(screen.getByRole('button', { name: /reconnect/i })).toBeInTheDocument();
    });

    it('calls onReconnect when button clicked', () => {
      const mockReconnect = jest.fn();
      render(
        <ConnectionStatus
          isConnected={false}
          connectionState="failed"
          onReconnect={mockReconnect}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: /reconnect/i }));
      expect(mockReconnect).toHaveBeenCalled();
    });

    it('shows queued messages count', () => {
      render(
        <ConnectionStatus
          isConnected={false}
          connectionState="reconnecting"
          queuedMessages={3}
        />
      );

      expect(screen.getByText('3 queued')).toBeInTheDocument();
    });

    it('has proper accessibility role', () => {
      render(<ConnectionStatus isConnected={true} />);

      expect(screen.getByRole('status')).toBeInTheDocument();
    });

    it('has aria-live for screen readers', () => {
      render(<ConnectionStatus isConnected={true} />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
    });
  });

  describe('compact mode', () => {
    it('renders in compact mode', () => {
      render(<ConnectionStatus isConnected={true} connectionState="connected" compact />);

      expect(screen.getByText('Live')).toBeInTheDocument();
    });

    it('shows shorter text in compact mode when reconnecting', () => {
      render(
        <ConnectionStatus
          isConnected={false}
          connectionState="reconnecting"
          reconnectAttempts={3}
          compact
        />
      );

      expect(screen.getByText('Reconnecting')).toBeInTheDocument();
    });
  });

  describe('ConnectionStatusDot', () => {
    it('shows green when connected', () => {
      render(<ConnectionStatusDot isConnected={true} connectionState="connected" />);

      const dot = screen.getByRole('status');
      expect(dot).toHaveClass('bg-green-500');
    });

    it('shows yellow when connecting', () => {
      render(<ConnectionStatusDot isConnected={false} connectionState="connecting" />);

      const dot = screen.getByRole('status');
      expect(dot).toHaveClass('bg-yellow-500');
    });

    it('shows red when failed', () => {
      render(<ConnectionStatusDot isConnected={false} connectionState="failed" />);

      const dot = screen.getByRole('status');
      expect(dot).toHaveClass('bg-red-500');
    });

    it('shows gray when offline', () => {
      render(<ConnectionStatusDot isConnected={false} isOnline={false} />);

      const dot = screen.getByRole('status');
      expect(dot).toHaveClass('bg-gray-400');
    });

    it('has accessible label', () => {
      render(<ConnectionStatusDot isConnected={true} connectionState="connected" />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Connected');
    });

    it('animates when connecting', () => {
      render(<ConnectionStatusDot isConnected={false} connectionState="connecting" />);

      expect(screen.getByRole('status')).toHaveClass('animate-pulse');
    });
  });

  describe('ConnectionStatusBanner', () => {
    it('returns null when connected', () => {
      const { container } = render(
        <ConnectionStatusBanner connectionState="connected" />
      );

      expect(container.firstChild).toBeNull();
    });

    it('returns null when connecting', () => {
      const { container } = render(
        <ConnectionStatusBanner connectionState="connecting" />
      );

      expect(container.firstChild).toBeNull();
    });

    it('shows banner when reconnecting', () => {
      render(
        <ConnectionStatusBanner
          connectionState="reconnecting"
          reconnectAttempts={2}
          maxReconnectAttempts={10}
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/reconnecting.*attempt 2\/10/i)).toBeInTheDocument();
    });

    it('shows banner when failed', () => {
      render(<ConnectionStatusBanner connectionState="failed" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/connection failed/i)).toBeInTheDocument();
    });

    it('shows banner when offline', () => {
      render(<ConnectionStatusBanner connectionState="disconnected" isOnline={false} />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/you are offline/i)).toBeInTheDocument();
    });

    it('shows reconnect button when failed and online', () => {
      const mockReconnect = jest.fn();
      render(
        <ConnectionStatusBanner
          connectionState="failed"
          isOnline={true}
          onReconnect={mockReconnect}
        />
      );

      expect(screen.getByRole('button', { name: /reconnect/i })).toBeInTheDocument();
    });

    it('does not show reconnect button when offline', () => {
      const mockReconnect = jest.fn();
      render(
        <ConnectionStatusBanner
          connectionState="failed"
          isOnline={false}
          onReconnect={mockReconnect}
        />
      );

      expect(screen.queryByRole('button', { name: /reconnect/i })).not.toBeInTheDocument();
    });
  });
});
