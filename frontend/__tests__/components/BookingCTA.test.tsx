import { render, screen, fireEvent } from "@testing-library/react";
import BookingCTA from "@/components/BookingCTA";
import { useRouter } from "next/navigation";

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

describe("BookingCTA component", () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
  });

  it("does not render when message count is less than 3", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={2} />);

    expect(
      screen.queryByText(/Ready to book a lesson?/i)
    ).not.toBeInTheDocument();
  });

  it("renders when message count is 3 or more", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    expect(screen.getByText(/Ready to book a lesson?/i)).toBeInTheDocument();
  });

  it("displays tutor name in message", () => {
    render(<BookingCTA tutorId={1} tutorName="Jane Smith" messageCount={5} />);

    expect(
      screen.getByText(/You've been chatting with Jane Smith/i)
    ).toBeInTheDocument();
  });

  it("navigates to tutor profile on button click", () => {
    render(<BookingCTA tutorId={42} tutorName="John Doe" messageCount={3} />);

    const button = screen.getByRole("button", {
      name: /View Profile & Book/i,
    });
    fireEvent.click(button);

    expect(mockPush).toHaveBeenCalledWith("/tutors/42");
  });

  it("shows correct styling for CTA banner", () => {
    const { container } = render(
      <BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />
    );

    const banner = container.querySelector(".bg-gradient-to-r");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveClass("from-primary-50", "to-blue-50");
  });

  it("displays calendar icon", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    // Icon container is present
    const iconContainer = screen
      .getByText(/Ready to book a lesson?/i)
      .closest("div")
      ?.querySelector(".bg-primary-600");
    expect(iconContainer).toBeInTheDocument();
  });

  it("shows arrow icon on button", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    const button = screen.getByRole("button", {
      name: /View Profile & Book/i,
    });
    expect(button).toBeInTheDocument();
  });

  it("updates visibility when message count changes", () => {
    const { rerender } = render(
      <BookingCTA tutorId={1} tutorName="John Doe" messageCount={2} />
    );

    expect(
      screen.queryByText(/Ready to book a lesson?/i)
    ).not.toBeInTheDocument();

    rerender(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    expect(screen.getByText(/Ready to book a lesson?/i)).toBeInTheDocument();
  });

  it("handles different tutor IDs correctly", () => {
    const { rerender } = render(
      <BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />
    );

    fireEvent.click(
      screen.getByRole("button", { name: /View Profile & Book/i })
    );
    expect(mockPush).toHaveBeenCalledWith("/tutors/1");

    mockPush.mockClear();

    rerender(
      <BookingCTA tutorId={99} tutorName="Jane Smith" messageCount={3} />
    );

    fireEvent.click(
      screen.getByRole("button", { name: /View Profile & Book/i })
    );
    expect(mockPush).toHaveBeenCalledWith("/tutors/99");
  });

  it("shows encouragement message", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    expect(
      screen.getByText(/Book your first lesson to get started!/i)
    ).toBeInTheDocument();
  });

  it("is accessible with proper heading structure", () => {
    render(<BookingCTA tutorId={1} tutorName="John Doe" messageCount={3} />);

    const heading = screen.getByText(/Ready to book a lesson?/i);
    expect(heading.tagName).toBe("H4");
  });
});
