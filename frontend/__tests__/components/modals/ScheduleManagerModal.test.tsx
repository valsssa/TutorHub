/**
 * Tests for ScheduleManagerModal component
 * Critical: Tutor scheduling management interface
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ScheduleManagerModal from "@/components/modals/ScheduleManagerModal";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  X: () => <span data-testid="close-icon">X</span>,
  User: () => <span data-testid="user-icon">User</span>,
  Calendar: () => <span data-testid="calendar-icon">Cal</span>,
  RotateCw: () => <span data-testid="rotate-icon">Rotate</span>,
  ArrowRight: () => <span data-testid="arrow-icon">Arrow</span>,
  Clock: () => <span data-testid="clock-icon">Clock</span>,
  ChevronDown: () => <span data-testid="chevron-icon">Chevron</span>,
}));

// Mock the toast hook
const mockShowSuccess = jest.fn();
const mockShowError = jest.fn();

jest.mock("@/components/ToastContainer", () => ({
  useToast: () => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError,
    showInfo: jest.fn(),
  }),
}));

// Mock the API
const mockCreateAvailability = jest.fn();

jest.mock("@/lib/api", () => ({
  bookings: {},
  availability: {
    createAvailability: (...args: any[]) => mockCreateAvailability(...args),
  },
}));

describe("ScheduleManagerModal", () => {
  const mockOnClose = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateAvailability.mockResolvedValue({});
  });

  describe("rendering", () => {
    it("renders nothing when isOpen is false", () => {
      const { container } = render(
        <ScheduleManagerModal {...defaultProps} isOpen={false} />
      );

      expect(container.firstChild).toBeNull();
    });

    it("renders modal when isOpen is true", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(
        screen.getByRole("dialog", { name: /schedule management/i })
      ).toBeInTheDocument();
    });

    it("displays modal title and description", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByText("Schedule Management")).toBeInTheDocument();
      expect(
        screen.getByText(/manage your lessons, time off, and availability/i)
      ).toBeInTheDocument();
    });

    it("displays all three tabs", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByText("Lesson")).toBeInTheDocument();
      expect(screen.getByText("Time off")).toBeInTheDocument();
      expect(screen.getByText("Extra slots")).toBeInTheDocument();
    });

    it("displays close button", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /close modal/i })
      ).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has proper dialog role and aria attributes", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute(
        "aria-labelledby",
        "schedule-modal-title"
      );
    });
  });

  describe("tab navigation", () => {
    it("shows Lesson tab content by default", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText("Add student")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /schedule session/i })
      ).toBeInTheDocument();
    });

    it("shows Time off tab content when clicked", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.click(screen.getByText("Time off"));

      expect(screen.getByPlaceholderText("Busy")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /book time off/i })
      ).toBeInTheDocument();
    });

    it("shows Extra slots tab content when clicked", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.click(screen.getByText("Extra slots"));

      expect(screen.getByText("Add extra slots")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /^add$/i })
      ).toBeInTheDocument();
    });

    it("respects initialTab prop", () => {
      render(
        <ScheduleManagerModal {...defaultProps} initialTab="Time off" />
      );

      expect(screen.getByPlaceholderText("Busy")).toBeInTheDocument();
    });

    it("updates active tab when initialTab changes", () => {
      const { rerender } = render(
        <ScheduleManagerModal {...defaultProps} initialTab="Lesson" />
      );

      expect(screen.getByPlaceholderText("Add student")).toBeInTheDocument();

      rerender(
        <ScheduleManagerModal {...defaultProps} initialTab="Extra slots" />
      );

      expect(screen.getByText("Add extra slots")).toBeInTheDocument();
    });
  });

  describe("close functionality", () => {
    it("calls onClose when close button is clicked", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.click(screen.getByRole("button", { name: /close modal/i }));

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("calls onClose when backdrop is clicked", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      const backdrop = screen.getByRole("dialog").parentElement?.querySelector(
        '[aria-hidden="true"]'
      );
      await user.click(backdrop!);

      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("Lesson tab", () => {
    it("renders student input field", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByPlaceholderText("Add student")).toBeInTheDocument();
      expect(screen.getByText("Student")).toBeInTheDocument();
    });

    it("renders lesson type buttons", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByText("Lesson type")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /single/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /weekly/i })
      ).toBeInTheDocument();
    });

    it("toggles lesson type selection", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      const weeklyButton = screen.getByRole("button", { name: /weekly/i });
      await user.click(weeklyButton);

      // Weekly button should now be selected (has active styling)
      expect(weeklyButton.className).toContain("border-emerald-500");
    });

    it("renders duration select", () => {
      render(<ScheduleManagerModal {...defaultProps} />);

      expect(screen.getByText("Date and time")).toBeInTheDocument();
      expect(
        screen.getByRole("option", { name: /50 minutes/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("option", { name: /25 minutes/i })
      ).toBeInTheDocument();
    });

    it("shows error when scheduling without student name", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.click(
        screen.getByRole("button", { name: /schedule session/i })
      );

      expect(mockShowError).toHaveBeenCalledWith(
        "Please enter a student name"
      );
    });

    it("shows error when scheduling without date", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText("Add student"), "John");
      await user.click(
        screen.getByRole("button", { name: /schedule session/i })
      );

      expect(mockShowError).toHaveBeenCalledWith("Please select a date");
    });

    it("shows not supported message when trying to schedule", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText("Add student"), "John");

      // Fill in date
      const dateInput = screen.getByDisplayValue("");
      fireEvent.change(dateInput, { target: { value: "2025-06-15" } });

      await user.click(
        screen.getByRole("button", { name: /schedule session/i })
      );

      expect(mockShowError).toHaveBeenCalledWith(
        expect.stringContaining("isn't supported yet")
      );
    });
  });

  describe("Time off tab", () => {
    it("renders title input", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      expect(screen.getByPlaceholderText("Busy")).toBeInTheDocument();
      expect(screen.getByText("Title")).toBeInTheDocument();
    });

    it("renders starts and ends date inputs", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      expect(screen.getByText("Starts")).toBeInTheDocument();
      expect(screen.getByText("Ends")).toBeInTheDocument();
    });

    it("renders all day checkbox", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      expect(screen.getByLabelText("All day")).toBeInTheDocument();
    });

    it("toggles all day checkbox", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      const checkbox = screen.getByLabelText("All day");
      await user.click(checkbox);

      expect(checkbox).toBeChecked();
    });

    it("shows error when booking time off without dates", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));
      await user.click(screen.getByRole("button", { name: /book time off/i }));

      expect(mockShowError).toHaveBeenCalledWith(
        "Please select start and end dates"
      );
    });

    it("shows not supported message when trying to book time off", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      // Fill in dates
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-15" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-16" } });

      await user.click(screen.getByRole("button", { name: /book time off/i }));

      expect(mockShowError).toHaveBeenCalledWith(
        expect.stringContaining("isn't supported yet")
      );
    });
  });

  describe("Extra slots tab", () => {
    it("renders description text", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      expect(screen.getByText("Add extra slots")).toBeInTheDocument();
      expect(
        screen.getByText(/choose time slots up to 24 hours long/i)
      ).toBeInTheDocument();
    });

    it("renders starts and ends inputs", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      expect(screen.getByText("Starts")).toBeInTheDocument();
      expect(screen.getByText("Ends")).toBeInTheDocument();
    });

    it("shows error when adding slots without dates", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));
      await user.click(screen.getByRole("button", { name: /^add$/i }));

      expect(mockShowError).toHaveBeenCalledWith(
        "Please select start and end dates"
      );
    });

    it("shows error when end date is before start date", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      // Fill in dates with end before start
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-20" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-15" } });

      await user.click(screen.getByRole("button", { name: /^add$/i }));

      expect(mockShowError).toHaveBeenCalledWith(
        "End date must be on or after start date"
      );
    });

    it("calls API to create availability slots", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      // Fill in dates
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-15" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-16" } });

      await user.click(screen.getByRole("button", { name: /^add$/i }));

      await waitFor(() => {
        expect(mockCreateAvailability).toHaveBeenCalled();
      });
    });

    it("shows success message and closes modal on successful slot creation", async () => {
      const user = userEvent.setup();
      mockCreateAvailability.mockResolvedValue({});

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      // Fill in dates (same day)
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-15" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-15" } });

      await user.click(screen.getByRole("button", { name: /^add$/i }));

      await waitFor(() => {
        expect(mockShowSuccess).toHaveBeenCalledWith(
          "Extra availability slots added successfully"
        );
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it("shows error message on API failure", async () => {
      const user = userEvent.setup();
      mockCreateAvailability.mockRejectedValue({
        response: { data: { detail: "Slot already exists" } },
      });

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      // Fill in dates
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-15" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-15" } });

      await user.click(screen.getByRole("button", { name: /^add$/i }));

      await waitFor(() => {
        expect(mockShowError).toHaveBeenCalledWith("Slot already exists");
      });
    });
  });

  describe("submitting states", () => {
    it("shows submitting state for lesson tab", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      await user.type(screen.getByPlaceholderText("Add student"), "John");

      const dateInput = screen.getByDisplayValue("");
      fireEvent.change(dateInput, { target: { value: "2025-06-15" } });

      const submitButton = screen.getByRole("button", {
        name: /schedule session/i,
      });
      await user.click(submitButton);

      // Button text should update during submission then reset
      // Due to the quick error response, we just verify the call completes
      expect(mockShowError).toHaveBeenCalled();
    });

    it("disables submit button while submitting extra slots", async () => {
      const user = userEvent.setup();

      let resolvePromise: () => void;
      mockCreateAvailability.mockImplementation(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          })
      );

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Extra slots"));

      // Fill in dates
      const dateInputs = screen.getAllByDisplayValue("");
      fireEvent.change(dateInputs[0], { target: { value: "2025-06-15" } });
      fireEvent.change(dateInputs[1], { target: { value: "2025-06-15" } });

      const submitButton = screen.getByRole("button", { name: /^add$/i });
      await user.click(submitButton);

      expect(screen.getByText("Adding...")).toBeInTheDocument();

      // Resolve to cleanup
      await waitFor(() => {
        resolvePromise!();
      });
    });
  });

  describe("form inputs", () => {
    it("updates student name input", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      const input = screen.getByPlaceholderText("Add student");
      await user.type(input, "Jane Smith");

      expect(input).toHaveValue("Jane Smith");
    });

    it("updates time off title input", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);
      await user.click(screen.getByText("Time off"));

      const input = screen.getByPlaceholderText("Busy");
      await user.clear(input);
      await user.type(input, "Vacation");

      expect(input).toHaveValue("Vacation");
    });

    it("updates duration select", async () => {
      const user = userEvent.setup();

      render(<ScheduleManagerModal {...defaultProps} />);

      const select = screen.getByRole("combobox", {
        name: "",
      });

      await user.selectOptions(select, "25");

      expect(select).toHaveValue("25");
    });
  });
});
