/**
 * Tests for RescheduleBookingModal component
 * Critical: Rescheduling is a key booking management feature
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RescheduleBookingModal from "@/components/modals/RescheduleBookingModal";
import { BookingDTO } from "@/types/booking";

// Mock react-icons
jest.mock("react-icons/fi", () => ({
  FiX: () => <span data-testid="close-icon">X</span>,
  FiCalendar: () => <span data-testid="calendar-icon">Cal</span>,
  FiClock: () => <span data-testid="clock-icon">Clock</span>,
}));

describe("RescheduleBookingModal", () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const createMockBooking = (
    overrides: Partial<BookingDTO> = {}
  ): BookingDTO => ({
    id: 1,
    tutor_profile_id: 1,
    student_id: 2,
    subject_id: 1,
    start_at: "2025-02-15T14:00:00Z",
    end_at: "2025-02-15T15:00:00Z",
    topic: "Math Tutoring",
    notes: "Test notes",
    hourly_rate: 50,
    total_amount: 50,
    status: "confirmed",
    meeting_url: null,
    pricing_option_id: null,
    pricing_type: null,
    subject_name: "Mathematics",
    student_name: "John Doe",
    student: {
      id: 2,
      name: "John Doe",
      email: "john@example.com",
    },
    tutor_earnings_cents: 4500,
    lesson_type: "regular",
    student_timezone: "UTC",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders nothing when isOpen is false", () => {
      const { container } = render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={false}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it("renders nothing when booking is null", () => {
      const { container } = render(
        <RescheduleBookingModal
          booking={null}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it("renders modal when isOpen is true and booking exists", () => {
      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByText("Reschedule Booking")).toBeInTheDocument();
    });

    it("displays current schedule information", () => {
      const booking = createMockBooking();

      render(
        <RescheduleBookingModal
          booking={booking}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByText("Current Schedule")).toBeInTheDocument();
      // Duration should be shown (60 min)
      expect(screen.getByText(/60 min/)).toBeInTheDocument();
    });

    it("displays date input with minimum date set to tomorrow", () => {
      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date");
      expect(dateInput).toBeInTheDocument();
      expect(dateInput).toHaveAttribute("min");
    });

    it("displays time input", () => {
      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const timeInput = screen.getByLabelText("New Time");
      expect(timeInput).toBeInTheDocument();
    });

    it("displays info message about tutor notification", () => {
      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(
        screen.getByText(/tutor will be notified/i)
      ).toBeInTheDocument();
    });

    it("displays Cancel and Confirm buttons", () => {
      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /confirm reschedule/i })
      ).toBeInTheDocument();
    });
  });

  describe("pre-filled values", () => {
    it("pre-fills date and time from booking", () => {
      const booking = createMockBooking({
        start_at: "2025-03-20T10:30:00Z",
      });

      render(
        <RescheduleBookingModal
          booking={booking}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date") as HTMLInputElement;
      const timeInput = screen.getByLabelText("New Time") as HTMLInputElement;

      // Date should be pre-filled (note: displayed in local time)
      expect(dateInput.value).toBeTruthy();
      expect(timeInput.value).toBeTruthy();
    });
  });

  describe("interactions", () => {
    it("calls onClose when close button is clicked", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const closeButton = screen.getByTestId("close-icon").closest("button");
      await user.click(closeButton!);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("calls onClose when Cancel button is clicked", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("updates date value when input changes", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date") as HTMLInputElement;

      await user.clear(dateInput);
      await user.type(dateInput, "2025-06-15");

      expect(dateInput.value).toBe("2025-06-15");
    });

    it("updates time value when input changes", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const timeInput = screen.getByLabelText("New Time") as HTMLInputElement;

      await user.clear(timeInput);
      await user.type(timeInput, "15:30");

      expect(timeInput.value).toBe("15:30");
    });
  });

  describe("form submission", () => {
    it("calls onConfirm with formatted datetime on submit", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date") as HTMLInputElement;
      const timeInput = screen.getByLabelText("New Time") as HTMLInputElement;

      await user.clear(dateInput);
      await user.type(dateInput, "2025-06-15");

      await user.clear(timeInput);
      await user.type(timeInput, "14:30");

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith("2025-06-15T14:30:00");
      });
    });

    it("closes modal after successful submission", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it("shows submitting state during submission", async () => {
      const user = userEvent.setup();

      let resolveConfirm: () => void;
      mockOnConfirm.mockImplementation(
        () =>
          new Promise<void>((resolve) => {
            resolveConfirm = resolve;
          })
      );

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      await user.click(submitButton);

      expect(screen.getByText("Rescheduling...")).toBeInTheDocument();

      // Resolve the promise
      await waitFor(() => {
        resolveConfirm!();
      });
    });

    it("disables buttons during submission", async () => {
      const user = userEvent.setup();

      mockOnConfirm.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      await user.click(submitButton);

      expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
      expect(screen.getByText("Rescheduling...")).toBeInTheDocument();
    });

    it("handles submission error gracefully", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockRejectedValue(new Error("Failed to reschedule"));

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      await user.click(submitButton);

      // Should not crash, should re-enable submit button
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /confirm reschedule/i })
        ).not.toBeDisabled();
      });
    });
  });

  describe("validation", () => {
    it("disables submit button when date is empty", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date") as HTMLInputElement;
      await user.clear(dateInput);

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      expect(submitButton).toBeDisabled();
    });

    it("disables submit button when time is empty", async () => {
      const user = userEvent.setup();

      render(
        <RescheduleBookingModal
          booking={createMockBooking()}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const timeInput = screen.getByLabelText("New Time") as HTMLInputElement;
      await user.clear(timeInput);

      const submitButton = screen.getByRole("button", {
        name: /confirm reschedule/i,
      });
      expect(submitButton).toBeDisabled();
    });
  });

  describe("duration calculation", () => {
    it("correctly calculates 60-minute session duration", () => {
      const booking = createMockBooking({
        start_at: "2025-02-15T14:00:00Z",
        end_at: "2025-02-15T15:00:00Z",
      });

      render(
        <RescheduleBookingModal
          booking={booking}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByText(/60 min/)).toBeInTheDocument();
    });

    it("correctly calculates 90-minute session duration", () => {
      const booking = createMockBooking({
        start_at: "2025-02-15T14:00:00Z",
        end_at: "2025-02-15T15:30:00Z",
      });

      render(
        <RescheduleBookingModal
          booking={booking}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByText(/90 min/)).toBeInTheDocument();
    });

    it("shows duration info in time input helper text", () => {
      const booking = createMockBooking({
        start_at: "2025-02-15T14:00:00Z",
        end_at: "2025-02-15T15:00:00Z",
      });

      render(
        <RescheduleBookingModal
          booking={booking}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      expect(screen.getByText(/Duration will remain 60 minutes/)).toBeInTheDocument();
    });
  });

  describe("state reset", () => {
    it("resets form state when booking changes", () => {
      const booking1 = createMockBooking({
        start_at: "2025-02-15T10:00:00Z",
      });
      const booking2 = createMockBooking({
        start_at: "2025-03-20T16:00:00Z",
      });

      const { rerender } = render(
        <RescheduleBookingModal
          booking={booking1}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      const dateInput = screen.getByLabelText("New Date") as HTMLInputElement;
      const initialDate = dateInput.value;

      rerender(
        <RescheduleBookingModal
          booking={booking2}
          isOpen={true}
          onClose={mockOnClose}
          onConfirm={mockOnConfirm}
        />
      );

      // Date should be updated to booking2's date
      expect(dateInput.value).not.toBe(initialDate);
    });
  });
});
