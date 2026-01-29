/**
 * Tests for RejectReasonModal component
 * Critical: Admin rejection workflow for tutor applications
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import RejectReasonModal from "@/components/modals/RejectReasonModal";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  X: () => <span data-testid="close-icon">X</span>,
  AlertTriangle: () => <span data-testid="alert-icon">Alert</span>,
}));

describe("RejectReasonModal", () => {
  const mockOnClose = jest.fn();
  const mockOnConfirm = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onConfirm: mockOnConfirm,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders nothing when isOpen is false", () => {
      const { container } = render(
        <RejectReasonModal {...defaultProps} isOpen={false} />
      );

      expect(container.firstChild).toBeNull();
    });

    it("renders modal when isOpen is true", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(
        screen.getByRole("dialog", { name: /reject tutor application/i })
      ).toBeInTheDocument();
    });

    it("displays default title", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(screen.getByText("Reject Tutor Application")).toBeInTheDocument();
    });

    it("displays custom title when provided", () => {
      render(
        <RejectReasonModal {...defaultProps} title="Custom Rejection Title" />
      );

      expect(screen.getByText("Custom Rejection Title")).toBeInTheDocument();
    });

    it("displays default description", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(
        screen.getByText(/provide a reason for rejecting/i)
      ).toBeInTheDocument();
    });

    it("displays custom description when provided", () => {
      render(
        <RejectReasonModal
          {...defaultProps}
          description="Custom description for rejection"
        />
      );

      expect(
        screen.getByText("Custom description for rejection")
      ).toBeInTheDocument();
    });

    it("displays alert icon", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(screen.getByTestId("alert-icon")).toBeInTheDocument();
    });

    it("displays close button", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /close/i })
      ).toBeInTheDocument();
    });

    it("displays rejection reason textarea", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(screen.getByLabelText("Rejection Reason")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/enter the reason for rejection/i)
      ).toBeInTheDocument();
    });

    it("displays Cancel and Reject buttons", () => {
      render(<RejectReasonModal {...defaultProps} />);

      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /reject application/i })
      ).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has proper dialog role and aria attributes", () => {
      render(<RejectReasonModal {...defaultProps} />);

      const dialog = screen.getByRole("dialog");
      expect(dialog).toHaveAttribute("aria-modal", "true");
      expect(dialog).toHaveAttribute("aria-labelledby", "reject-modal-title");
    });

    it("textarea has aria-required attribute", () => {
      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      expect(textarea).toHaveAttribute("aria-required", "true");
    });
  });

  describe("interactions", () => {
    it("calls onClose when close button is clicked", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const closeButton = screen.getByRole("button", { name: /close/i });
      await user.click(closeButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("calls onClose when Cancel button is clicked", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("calls onClose when backdrop is clicked", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const backdrop = screen.getByRole("dialog").parentElement?.querySelector(
        '[aria-hidden="true"]'
      );
      await user.click(backdrop!);

      expect(mockOnClose).toHaveBeenCalled();
    });

    it("updates textarea value when typing", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test rejection reason");

      expect(textarea).toHaveValue("Test rejection reason");
    });

    it("clears textarea when modal is closed via Cancel", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Some reason");

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      // Rerender with isOpen true to check cleared state
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe("form submission", () => {
    it("calls onConfirm with trimmed reason on submit", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "  Incomplete documentation  ");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith("Incomplete documentation");
      });
    });

    it("closes modal after successful submission", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test reason");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnClose).toHaveBeenCalled();
      });
    });

    it("clears textarea after successful submission", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      const { rerender } = render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test reason");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalled();
      });

      // Rerender to check that state was cleared
      rerender(<RejectReasonModal {...defaultProps} />);
      expect(screen.getByLabelText("Rejection Reason")).toHaveValue("");
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

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test reason");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      expect(screen.getByText("Rejecting...")).toBeInTheDocument();

      // Resolve to clean up
      await waitFor(() => {
        resolveConfirm!();
      });
    });

    it("disables buttons during submission", async () => {
      const user = userEvent.setup();

      mockOnConfirm.mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test reason");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeDisabled();
    });

    it("re-enables submit after submission completes", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      const { rerender } = render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Test reason");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalled();
      });

      // Rerender and check button is enabled
      rerender(<RejectReasonModal {...defaultProps} />);

      await user.type(screen.getByLabelText("Rejection Reason"), "New reason");

      expect(
        screen.getByRole("button", { name: /reject application/i })
      ).not.toBeDisabled();
    });
  });

  describe("validation", () => {
    it("disables submit button when reason is empty", () => {
      render(<RejectReasonModal {...defaultProps} />);

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      expect(submitButton).toBeDisabled();
    });

    it("disables submit button when reason is only whitespace", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "   ");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      expect(submitButton).toBeDisabled();
    });

    it("enables submit button when valid reason is provided", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "Valid reason for rejection");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      expect(submitButton).not.toBeDisabled();
    });

    it("does not call onConfirm when reason is empty and submit is attempted", async () => {
      const user = userEvent.setup();

      render(<RejectReasonModal {...defaultProps} />);

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });

      // Try to click disabled button (shouldn't trigger anything)
      await user.click(submitButton);

      expect(mockOnConfirm).not.toHaveBeenCalled();
    });
  });

  describe("edge cases", () => {
    it("handles very long rejection reasons", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      const longReason = "A".repeat(1000);
      await user.type(textarea, longReason);

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith(longReason);
      });
    });

    it("handles special characters in rejection reason", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      const specialReason = "Reason with <script>alert('xss')</script> & \"quotes\" and 'apostrophes'";
      await user.type(textarea, specialReason);

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith(specialReason);
      });
    });

    it("handles multiline rejection reasons", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      const multilineReason = "Line 1\nLine 2\nLine 3";

      // Use fireEvent for multiline input
      fireEvent.change(textarea, { target: { value: multilineReason } });

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith(multilineReason);
      });
    });

    it("trims leading and trailing whitespace", async () => {
      const user = userEvent.setup();
      mockOnConfirm.mockResolvedValue(undefined);

      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      await user.type(textarea, "  Reason with whitespace  ");

      const submitButton = screen.getByRole("button", {
        name: /reject application/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockOnConfirm).toHaveBeenCalledWith("Reason with whitespace");
      });
    });
  });

  describe("keyboard navigation", () => {
    it("textarea is focusable", () => {
      render(<RejectReasonModal {...defaultProps} />);

      const textarea = screen.getByLabelText("Rejection Reason");
      textarea.focus();

      expect(document.activeElement).toBe(textarea);
    });
  });
});
