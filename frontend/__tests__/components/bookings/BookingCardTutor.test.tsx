/**
 * Tests for BookingCardTutor component
 * Critical: Tutor booking management is a core feature
 */

import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import BookingCardTutor from "@/components/bookings/BookingCardTutor";
import { BookingDTO } from "@/types/booking";

// Mock react-icons
jest.mock("react-icons/fi", () => ({
  FiCalendar: () => <span data-testid="calendar-icon">Cal</span>,
  FiClock: () => <span data-testid="clock-icon">Clock</span>,
  FiDollarSign: () => <span data-testid="dollar-icon">$</span>,
  FiCheck: () => <span data-testid="check-icon">Check</span>,
  FiX: () => <span data-testid="x-icon">X</span>,
  FiAlertCircle: () => <span data-testid="alert-icon">Alert</span>,
  FiUser: () => <span data-testid="user-icon">User</span>,
}));

// Mock the timezone context
jest.mock("@/contexts/TimezoneContext", () => ({
  useTimezone: () => ({
    userTimezone: "America/New_York",
    setUserTimezone: jest.fn(),
  }),
}));

// Mock TimeDisplay component
jest.mock("@/components/TimeDisplay", () => ({
  __esModule: true,
  default: ({ date }: { date: string }) => (
    <span data-testid="time-display">{date}</span>
  ),
}));

// Mock booking utils
jest.mock("@/lib/bookingUtils", () => ({
  BOOKING_STATUS_COLORS: {
    pending: "bg-yellow-100 text-yellow-800",
    confirmed: "bg-green-100 text-green-800",
    completed: "bg-blue-100 text-blue-800",
    cancelled: "bg-red-100 text-red-800",
  },
  LESSON_TYPE_BADGES: {
    regular: "bg-blue-100 text-blue-800",
    trial: "bg-purple-100 text-purple-800",
    package: "bg-emerald-100 text-emerald-800",
  },
  SESSION_STATE_COLORS: {
    REQUESTED: "bg-yellow-100 text-yellow-800",
    SCHEDULED: "bg-green-100 text-green-800",
    ACTIVE: "bg-blue-100 text-blue-800",
    ENDED: "bg-gray-100 text-gray-800",
    CANCELLED: "bg-red-100 text-red-800",
  },
  DISPUTE_STATE_COLORS: {
    NONE: "",
    FILED: "bg-orange-100 text-orange-800",
    RESOLVED_STUDENT_FAVOR: "bg-red-100 text-red-800",
    RESOLVED_TUTOR_FAVOR: "bg-green-100 text-green-800",
  },
  calculateBookingTiming: (booking: any) => ({
    startDate: new Date(booking.start_at),
    endDate: new Date(booking.end_at),
    duration: 60,
    hoursUntil: 24,
  }),
  formatBookingPrice: (cents: number) => `$${(cents / 100).toFixed(2)}`,
  getDisplayTimezone: () => "America/New_York",
  getSessionStateLabel: (state: string) => state,
  getSessionOutcomeLabel: (outcome: string) => outcome,
  getDisputeStateLabel: (state: string) => state,
  isUpcomingBooking: (state: string) => ["REQUESTED", "SCHEDULED"].includes(state),
  isCancellableBooking: (state: string) => state === "SCHEDULED",
  hasOpenDispute: (state: string) => state === "FILED",
}));

describe("BookingCardTutor", () => {
  const mockOnConfirm = jest.fn();
  const mockOnDecline = jest.fn();
  const mockOnCancel = jest.fn();
  const mockOnMarkNoShow = jest.fn();
  const mockOnAddNotes = jest.fn();

  const createMockBooking = (
    overrides: Partial<BookingDTO> = {}
  ): BookingDTO => ({
    id: 1,
    tutor_profile_id: 1,
    student_id: 2,
    subject_id: 1,
    start_at: "2025-02-15T14:00:00Z",
    end_at: "2025-02-15T15:00:00Z",
    topic: "Calculus tutoring",
    notes: "",
    hourly_rate: 50,
    total_amount: 50,
    rate_cents: 5000,
    status: "pending",
    session_state: "REQUESTED",
    session_outcome: null,
    dispute_state: "NONE",
    meeting_url: null,
    pricing_option_id: null,
    pricing_type: null,
    subject_name: "Mathematics",
    student_name: "John Doe",
    student: {
      id: 2,
      name: "John Doe",
      email: "john@example.com",
      avatar_url: null,
      level: "Intermediate",
    },
    tutor_earnings_cents: 4500,
    lesson_type: "regular",
    student_timezone: "America/Los_Angeles",
    student_tz: "America/Los_Angeles",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders student name", () => {
      render(<BookingCardTutor booking={createMockBooking()} />);

      expect(screen.getByText("John Doe")).toBeInTheDocument();
    });

    it("renders student level when available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            student: {
              id: 2,
              name: "John Doe",
              email: "john@example.com",
              level: "Advanced",
            },
          })}
        />
      );

      expect(screen.getByText(/Level: Advanced/)).toBeInTheDocument();
    });

    it("renders student avatar when available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            student: {
              id: 2,
              name: "John Doe",
              email: "john@example.com",
              avatar_url: "https://example.com/avatar.jpg",
            },
          })}
        />
      );

      const avatar = screen.getByAltText("John Doe");
      expect(avatar).toHaveAttribute(
        "src",
        "https://example.com/avatar.jpg"
      );
    });

    it("renders placeholder icon when no avatar", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            student: {
              id: 2,
              name: "John Doe",
              email: "john@example.com",
              avatar_url: null,
            },
          })}
        />
      );

      expect(screen.getByTestId("user-icon")).toBeInTheDocument();
    });

    it("renders session state badge", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ session_state: "SCHEDULED" })}
        />
      );

      expect(screen.getByText("SCHEDULED")).toBeInTheDocument();
    });

    it("renders session outcome badge when available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            session_state: "ENDED",
            session_outcome: "COMPLETED",
          })}
        />
      );

      expect(screen.getByText("COMPLETED")).toBeInTheDocument();
    });

    it("renders dispute badge when has dispute", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ dispute_state: "FILED" })}
        />
      );

      expect(screen.getByText("FILED")).toBeInTheDocument();
    });

    it("renders lesson type badge", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ lesson_type: "trial" })}
        />
      );

      expect(screen.getByText("trial")).toBeInTheDocument();
    });

    it("renders calendar and clock icons", () => {
      render(<BookingCardTutor booking={createMockBooking()} />);

      expect(screen.getByTestId("calendar-icon")).toBeInTheDocument();
      expect(screen.getByTestId("clock-icon")).toBeInTheDocument();
    });

    it("displays duration in minutes", () => {
      render(<BookingCardTutor booking={createMockBooking()} />);

      expect(screen.getByText(/60 min/)).toBeInTheDocument();
    });

    it("displays tutor earnings", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ tutor_earnings_cents: 4500 })}
        />
      );

      expect(screen.getByText("$45.00")).toBeInTheDocument();
    });

    it("displays total amount", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ rate_cents: 5000 })}
        />
      );

      expect(screen.getByText(/from \$50.00 total/)).toBeInTheDocument();
    });

    it("displays subject name", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ subject_name: "Physics" })}
        />
      );

      expect(screen.getByText(/Subject:/)).toBeInTheDocument();
      expect(screen.getByText(/Physics/)).toBeInTheDocument();
    });

    it("displays student notes when available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            notes_student: "Please focus on derivatives",
          })}
        />
      );

      expect(screen.getByText("Student notes:")).toBeInTheDocument();
      expect(
        screen.getByText("Please focus on derivatives")
      ).toBeInTheDocument();
    });

    it("displays tutor notes when available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            notes_tutor: "Review chain rule",
          })}
        />
      );

      expect(screen.getByText("Your notes:")).toBeInTheDocument();
      expect(screen.getByText("Review chain rule")).toBeInTheDocument();
    });
  });

  describe("pending booking state", () => {
    it("shows pending alert for REQUESTED bookings", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ session_state: "REQUESTED" })}
        />
      );

      expect(
        screen.getByText("Awaiting your confirmation")
      ).toBeInTheDocument();
      expect(screen.getByTestId("alert-icon")).toBeInTheDocument();
    });

    it("applies left border styling for pending bookings", () => {
      const { container } = render(
        <BookingCardTutor
          booking={createMockBooking({ session_state: "REQUESTED" })}
        />
      );

      const card = container.firstChild;
      expect(card).toHaveClass("border-l-4", "border-yellow-500");
    });
  });

  describe("action buttons", () => {
    describe("confirm button", () => {
      it("renders Confirm button for REQUESTED bookings", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "REQUESTED" })}
            onConfirm={mockOnConfirm}
          />
        );

        expect(
          screen.getByRole("button", { name: /confirm/i })
        ).toBeInTheDocument();
      });

      it("calls onConfirm with booking ID when clicked", async () => {
        const user = userEvent.setup();

        render(
          <BookingCardTutor
            booking={createMockBooking({ id: 123, session_state: "REQUESTED" })}
            onConfirm={mockOnConfirm}
          />
        );

        const confirmButton = screen.getByRole("button", { name: /confirm/i });
        await user.click(confirmButton);

        expect(mockOnConfirm).toHaveBeenCalledWith(123);
      });

      it("does not render Confirm button when onConfirm not provided", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "REQUESTED" })}
          />
        );

        expect(
          screen.queryByRole("button", { name: /confirm/i })
        ).not.toBeInTheDocument();
      });
    });

    describe("decline button", () => {
      it("renders Decline button for REQUESTED bookings", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "REQUESTED" })}
            onDecline={mockOnDecline}
          />
        );

        expect(
          screen.getByRole("button", { name: /decline/i })
        ).toBeInTheDocument();
      });

      it("calls onDecline with booking ID when clicked", async () => {
        const user = userEvent.setup();

        render(
          <BookingCardTutor
            booking={createMockBooking({ id: 456, session_state: "REQUESTED" })}
            onDecline={mockOnDecline}
          />
        );

        const declineButton = screen.getByRole("button", { name: /decline/i });
        await user.click(declineButton);

        expect(mockOnDecline).toHaveBeenCalledWith(456);
      });
    });

    describe("cancel button", () => {
      it("renders Cancel button for SCHEDULED bookings", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "SCHEDULED" })}
            onCancel={mockOnCancel}
          />
        );

        expect(
          screen.getByRole("button", { name: /cancel/i })
        ).toBeInTheDocument();
      });

      it("calls onCancel with booking ID when clicked", async () => {
        const user = userEvent.setup();

        render(
          <BookingCardTutor
            booking={createMockBooking({ id: 789, session_state: "SCHEDULED" })}
            onCancel={mockOnCancel}
          />
        );

        const cancelButton = screen.getByRole("button", { name: /cancel/i });
        await user.click(cancelButton);

        expect(mockOnCancel).toHaveBeenCalledWith(789);
      });

      it("does not render Cancel button for REQUESTED bookings", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "REQUESTED" })}
            onCancel={mockOnCancel}
          />
        );

        expect(
          screen.queryByRole("button", { name: /^cancel$/i })
        ).not.toBeInTheDocument();
      });
    });

    describe("add notes button", () => {
      it("renders Add Notes button for upcoming bookings", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({ session_state: "SCHEDULED" })}
            onAddNotes={mockOnAddNotes}
          />
        );

        expect(
          screen.getByRole("button", { name: /add notes/i })
        ).toBeInTheDocument();
      });

      it("shows Edit Notes when notes already exist", () => {
        render(
          <BookingCardTutor
            booking={createMockBooking({
              session_state: "SCHEDULED",
              notes_tutor: "Existing notes",
            })}
            onAddNotes={mockOnAddNotes}
          />
        );

        expect(
          screen.getByRole("button", { name: /edit notes/i })
        ).toBeInTheDocument();
      });

      it("calls onAddNotes with booking ID when clicked", async () => {
        const user = userEvent.setup();

        render(
          <BookingCardTutor
            booking={createMockBooking({ id: 111, session_state: "SCHEDULED" })}
            onAddNotes={mockOnAddNotes}
          />
        );

        const addNotesButton = screen.getByRole("button", {
          name: /add notes/i,
        });
        await user.click(addNotesButton);

        expect(mockOnAddNotes).toHaveBeenCalledWith(111);
      });
    });
  });

  describe("fallback to legacy status", () => {
    it("uses legacy status when session_state is not available", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            session_state: undefined,
            status: "confirmed",
          })}
        />
      );

      // Should render with some status display
      expect(screen.getByText("confirmed")).toBeInTheDocument();
    });
  });

  describe("different booking states", () => {
    it("renders correctly for ACTIVE session", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ session_state: "ACTIVE" })}
        />
      );

      expect(screen.getByText("ACTIVE")).toBeInTheDocument();
      // Should not show confirm/decline buttons
      expect(
        screen.queryByRole("button", { name: /confirm/i })
      ).not.toBeInTheDocument();
    });

    it("renders correctly for ENDED session", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            session_state: "ENDED",
            session_outcome: "COMPLETED",
          })}
        />
      );

      expect(screen.getByText("ENDED")).toBeInTheDocument();
      expect(screen.getByText("COMPLETED")).toBeInTheDocument();
    });

    it("renders correctly for CANCELLED session", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ session_state: "CANCELLED" })}
        />
      );

      expect(screen.getByText("CANCELLED")).toBeInTheDocument();
    });
  });

  describe("dispute states", () => {
    it("does not show dispute badge when NONE", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ dispute_state: "NONE" })}
        />
      );

      const card = screen.getByText("John Doe").closest("div")?.parentElement;
      expect(card?.textContent).not.toContain("NONE");
    });

    it("shows FILED dispute badge", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ dispute_state: "FILED" })}
        />
      );

      expect(screen.getByText("FILED")).toBeInTheDocument();
    });

    it("shows resolved dispute badge", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({
            dispute_state: "RESOLVED_TUTOR_FAVOR",
          })}
        />
      );

      expect(screen.getByText("RESOLVED_TUTOR_FAVOR")).toBeInTheDocument();
    });
  });

  describe("lesson types", () => {
    it("renders regular lesson type", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ lesson_type: "regular" })}
        />
      );

      expect(screen.getByText("regular")).toBeInTheDocument();
    });

    it("renders trial lesson type", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ lesson_type: "trial" })}
        />
      );

      expect(screen.getByText("trial")).toBeInTheDocument();
    });

    it("renders package lesson type", () => {
      render(
        <BookingCardTutor
          booking={createMockBooking({ lesson_type: "package" })}
        />
      );

      expect(screen.getByText("package")).toBeInTheDocument();
    });
  });
});
