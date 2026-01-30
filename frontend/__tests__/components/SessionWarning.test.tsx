/**
 * Tests for SessionWarning component
 * Tests session expiration warning modal and countdown functionality
 */

import { render, screen, fireEvent, act, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SessionWarning, { useSessionTimeout } from '@/components/SessionWarning';
import { renderHook } from '@testing-library/react';

// Mock timers for countdown tests
jest.useFakeTimers();

describe('SessionWarning', () => {
  const mockOnExtend = jest.fn();
  const mockOnExpire = jest.fn();
  const mockOnLogout = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnExtend.mockResolvedValue(undefined);
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.useFakeTimers();
  });

  describe('visibility', () => {
    it('does not render when session has time remaining', () => {
      const { container } = render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
        />
      );

      // Advance a bit but not enough to trigger warning
      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(container.firstChild).toBeNull();
    });

    it('shows warning modal when approaching session expiration', () => {
      const now = Date.now();
      // Set last activity to 26 minutes ago (4 minutes remaining, less than 5 min warning threshold)
      const lastActivity = now - 26 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('Session Expiring')).toBeInTheDocument();
    });
  });

  describe('countdown timer', () => {
    it('displays countdown timer correctly', () => {
      const now = Date.now();
      // 3 minutes remaining (180 seconds)
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Should show time remaining (around 3:00)
      expect(screen.getByText(/\d+:\d{2}/)).toBeInTheDocument();
    });

    it('formats time with leading zeros for seconds', () => {
      const now = Date.now();
      // Set to 1 minute 5 seconds remaining
      const lastActivity = now - (30 - 65 / 60) * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Timer should be in format M:SS
      const timer = screen.getByText(/\d+:\d{2}/);
      expect(timer).toBeInTheDocument();
    });

    it('decrements countdown every second', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      const initialTimeText = screen.getByText(/\d+:\d{2}/).textContent;

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      const updatedTimeText = screen.getByText(/\d+:\d{2}/).textContent;

      // Time should have decreased
      expect(updatedTimeText).not.toBe(initialTimeText);
    });

    it('shows "until automatic logout" text', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText(/until automatic logout/i)).toBeInTheDocument();
    });
  });

  describe('Extend Session button', () => {
    it('renders "Stay Logged In" button', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByRole('button', { name: /stay logged in/i })).toBeInTheDocument();
    });

    it('calls onExtend when clicked', async () => {
      jest.useRealTimers();
      const user = userEvent.setup();

      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      // Wait for component to show
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stay logged in/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /stay logged in/i }));

      await waitFor(() => {
        expect(mockOnExtend).toHaveBeenCalled();
      });

      jest.useFakeTimers();
    });

    it('shows loading state while extending', async () => {
      jest.useRealTimers();
      const user = userEvent.setup();

      mockOnExtend.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)));

      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /stay logged in/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /stay logged in/i }));

      // Button should show loading state
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /loading/i })).toBeInTheDocument();
      });

      jest.useFakeTimers();
    });
  });

  describe('Logout button', () => {
    it('renders "Log Out" button', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
    });

    it('calls onLogout when clicked', async () => {
      jest.useRealTimers();
      const user = userEvent.setup();

      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /log out/i }));

      expect(mockOnLogout).toHaveBeenCalled();

      jest.useFakeTimers();
    });
  });

  describe('auto-logout', () => {
    it('calls onExpire when countdown reaches zero', () => {
      const now = Date.now();
      // Set to just 5 seconds remaining
      const lastActivity = now - (30 * 60 - 5) * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Advance past the remaining time
      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(mockOnExpire).toHaveBeenCalled();
    });

    it('calls onExpire when session has already expired', () => {
      const now = Date.now();
      // Session already expired (31 minutes ago)
      const lastActivity = now - 31 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(mockOnExpire).toHaveBeenCalled();
    });
  });

  describe('modal behavior', () => {
    it('displays warning icon', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      const { container } = render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Check for warning icon container
      const iconContainer = container.querySelector('.bg-amber-100');
      expect(iconContainer).toBeInTheDocument();
    });

    it('displays informative message about session expiration', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText(/session is about to expire/i)).toBeInTheDocument();
    });

    it('displays progress indicator', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      const { container } = render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Check for progress bar
      const progressBar = container.querySelector('.bg-amber-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('cannot be closed by clicking backdrop', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      const { container } = render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Try clicking backdrop
      const backdrop = container.querySelector('.bg-black\\/50');
      if (backdrop) {
        fireEvent.click(backdrop);
      }

      // Modal should still be visible
      expect(screen.getByText('Session Expiring')).toBeInTheDocument();
    });

    it('does not show close button', () => {
      const now = Date.now();
      const lastActivity = now - 27 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          onLogout={mockOnLogout}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      // Should not have close button
      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument();
    });
  });

  describe('default props', () => {
    it('uses default warning minutes of 5', () => {
      const now = Date.now();
      // 4 minutes remaining (within default 5 min warning)
      const lastActivity = now - 26 * 60 * 1000;

      render(
        <SessionWarning
          sessionDuration={30}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('Session Expiring')).toBeInTheDocument();
    });

    it('uses default session duration of 30 minutes', () => {
      const now = Date.now();
      // 4 minutes remaining with 30 min session
      const lastActivity = now - 26 * 60 * 1000;

      render(
        <SessionWarning
          warningMinutes={5}
          onExtend={mockOnExtend}
          onExpire={mockOnExpire}
          lastActivity={lastActivity}
        />
      );

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(screen.getByText('Session Expiring')).toBeInTheDocument();
    });
  });
});

describe('useSessionTimeout hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  it('returns lastActivity timestamp', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    expect(result.current.lastActivity).toBeDefined();
    expect(typeof result.current.lastActivity).toBe('number');
  });

  it('returns showWarning state', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    expect(result.current.showWarning).toBeDefined();
    expect(typeof result.current.showWarning).toBe('boolean');
  });

  it('returns updateActivity function', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    expect(result.current.updateActivity).toBeDefined();
    expect(typeof result.current.updateActivity).toBe('function');
  });

  it('returns extendSession function', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    expect(result.current.extendSession).toBeDefined();
    expect(typeof result.current.extendSession).toBe('function');
  });

  it('returns setShowWarning function', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    expect(result.current.setShowWarning).toBeDefined();
    expect(typeof result.current.setShowWarning).toBe('function');
  });

  it('updateActivity updates lastActivity timestamp', () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    const initialActivity = result.current.lastActivity;

    // Advance time
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    act(() => {
      result.current.updateActivity();
    });

    expect(result.current.lastActivity).toBeGreaterThanOrEqual(initialActivity);
  });

  it('extendSession resets lastActivity and hides warning', async () => {
    const { result } = renderHook(() => useSessionTimeout({}));

    // Manually set showWarning to true
    act(() => {
      result.current.setShowWarning(true);
    });

    expect(result.current.showWarning).toBe(true);

    await act(async () => {
      await result.current.extendSession();
    });

    expect(result.current.showWarning).toBe(false);
  });

  it('calls onExpire when session expires', () => {
    const mockOnExpire = jest.fn();

    renderHook(() => useSessionTimeout({
      sessionDuration: 1, // 1 minute
      warningMinutes: 0.5,
      onExpire: mockOnExpire,
    }));

    // Advance past session duration
    act(() => {
      jest.advanceTimersByTime(2 * 60 * 1000);
    });

    expect(mockOnExpire).toHaveBeenCalled();
  });
});
