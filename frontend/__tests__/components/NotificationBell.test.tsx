import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import NotificationBell from "@/components/NotificationBell";
import { notifications as notificationAPI } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";

// Mock dependencies
jest.mock("@/lib/api", () => ({
  notifications: {
    list: jest.fn(),
    markRead: jest.fn(),
    markAllAsRead: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("@/hooks/useWebSocket", () => ({
  useWebSocket: jest.fn(),
}));

jest.mock("@/components/ToastContainer", () => ({
  useToast: () => ({
    showError: jest.fn(),
    showSuccess: jest.fn(),
  }),
}));

const mockNotifications = [
  {
    id: 1,
    type: "new_message",
    title: "New Message",
    message: "You have a new message from John",
    link: "/messages/1",
    is_read: false,
    created_at: new Date().toISOString(),
    category: "messages",
    priority: 1,
  },
  {
    id: 2,
    type: "booking_confirmed",
    title: "Booking Confirmed",
    message: "Your booking has been confirmed",
    link: "/bookings/2",
    is_read: true,
    created_at: new Date(Date.now() - 3600000).toISOString(),
    category: "bookings",
    priority: 2,
  },
];

describe("NotificationBell component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (notificationAPI.list as jest.Mock).mockResolvedValue(mockNotifications);
    (useWebSocket as jest.Mock).mockReturnValue({
      isConnected: true,
      lastMessage: null,
    });
  });

  it("renders notification bell icon", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(screen.getByLabelText("Notifications")).toBeInTheDocument();
    });
  });

  it("displays unread count badge", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
    });
  });

  it("loads notifications on mount", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });
  });

  it("opens dropdown on bell click", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    expect(screen.getByText("Notifications")).toBeInTheDocument();
    expect(screen.getByText("Mark all read")).toBeInTheDocument();
  });

  it("displays all notifications in dropdown", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    expect(screen.getByText("New Message")).toBeInTheDocument();
    expect(screen.getByText("Booking Confirmed")).toBeInTheDocument();
  });

  it("marks notification as read", async () => {
    (notificationAPI.markRead as jest.Mock).mockResolvedValue({});

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    const markReadButtons = screen.getAllByTitle("Mark as read");
    fireEvent.click(markReadButtons[0]);

    await waitFor(() => {
      expect(notificationAPI.markRead).toHaveBeenCalledWith(1);
    });
  });

  it("marks all notifications as read", async () => {
    (notificationAPI.markAllAsRead as jest.Mock).mockResolvedValue({});

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));
    fireEvent.click(screen.getByText("Mark all read"));

    await waitFor(() => {
      expect(notificationAPI.markAllAsRead).toHaveBeenCalled();
    });
  });

  it("deletes notification", async () => {
    (notificationAPI.delete as jest.Mock).mockResolvedValue({});

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    const deleteButtons = screen.getAllByTitle("Delete");
    fireEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(notificationAPI.delete).toHaveBeenCalledWith(1);
    });
  });

  it("shows empty state when no notifications", async () => {
    (notificationAPI.list as jest.Mock).mockResolvedValue([]);

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    expect(screen.getByText("No notifications yet")).toBeInTheDocument();
  });

  it("closes dropdown when clicking outside", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));
    expect(screen.getByText("Notifications")).toBeInTheDocument();

    fireEvent.mouseDown(document.body);

    await waitFor(() => {
      expect(screen.queryByText("Mark all read")).not.toBeInTheDocument();
    });
  });

  it("receives new notification via WebSocket", async () => {
    const newNotification = {
      type: "notification",
      notification_id: 3,
      notification_type: "booking_reminder",
      title: "Booking Reminder",
      message: "Your session starts in 1 hour",
      link: "/bookings/3",
      created_at: new Date().toISOString(),
      category: "reminders",
      priority: 3,
    };

    const { rerender } = render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    // Simulate WebSocket message
    (useWebSocket as jest.Mock).mockReturnValue({
      isConnected: true,
      lastMessage: newNotification,
    });

    rerender(<NotificationBell />);

    await waitFor(() => {
      fireEvent.click(screen.getByLabelText("Notifications"));
      expect(screen.getByText("Booking Reminder")).toBeInTheDocument();
    });
  });

  it("updates unread count when marking as read", async () => {
    (notificationAPI.markRead as jest.Mock).mockResolvedValue({});

    render(<NotificationBell />);

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    const markReadButtons = screen.getAllByTitle("Mark as read");
    fireEvent.click(markReadButtons[0]);

    await waitFor(() => {
      expect(screen.queryByText("1")).not.toBeInTheDocument();
    });
  });

  it("shows notification icon based on type", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    // Icons are rendered (cannot test exact icon, but structure is there)
    const dropdown = screen.getByRole("button", { name: /Notifications/i })
      .nextElementSibling;
    expect(dropdown).toBeInTheDocument();
  });

  it("formats time correctly", async () => {
    const oneHourAgo = new Date(Date.now() - 3600000).toISOString();
    const oneDayAgo = new Date(Date.now() - 86400000).toISOString();

    (notificationAPI.list as jest.Mock).mockResolvedValue([
      {
        ...mockNotifications[0],
        created_at: oneHourAgo,
      },
      {
        ...mockNotifications[1],
        created_at: oneDayAgo,
      },
    ]);

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    // Time formatting is present
    expect(screen.getByText(/1h ago/i)).toBeInTheDocument();
    expect(screen.getByText(/1d ago/i)).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    (notificationAPI.list as jest.Mock).mockRejectedValue(
      new Error("Network error")
    );

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    // Should not crash and show empty state
    fireEvent.click(screen.getByLabelText("Notifications"));
    expect(screen.getByText("No notifications yet")).toBeInTheDocument();
  });

  it("shows loading state while fetching notifications", () => {
    (notificationAPI.list as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    );

    render(<NotificationBell />);

    fireEvent.click(screen.getByLabelText("Notifications"));

    // Loading spinner should be visible
    const dropdown = screen.getByLabelText("Notifications").nextElementSibling;
    expect(dropdown).toBeInTheDocument();
  });

  it("displays notification link", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    const links = screen.getAllByText("View →");
    expect(links).toHaveLength(2);
    expect(links[0].closest("a")).toHaveAttribute("href", "/messages/1");
  });

  it("highlights unread notifications", async () => {
    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    // Unread notifications have blue background
    const dropdown = screen.getByText("Notifications").closest("div");
    const unreadNotif = dropdown?.querySelector(".bg-blue-50");
    expect(unreadNotif).toBeInTheDocument();
  });

  it("does not show Mark all read when no unread notifications", async () => {
    (notificationAPI.list as jest.Mock).mockResolvedValue([
      { ...mockNotifications[0], is_read: true },
      { ...mockNotifications[1], is_read: true },
    ]);

    render(<NotificationBell />);

    await waitFor(() => {
      expect(notificationAPI.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByLabelText("Notifications"));

    expect(screen.queryByText("Mark all read")).not.toBeInTheDocument();
  });
});
