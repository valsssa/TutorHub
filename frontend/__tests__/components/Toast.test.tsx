import { render, screen, fireEvent, act } from "@testing-library/react";
import Toast from "@/components/Toast";

describe("Toast", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders provided message", () => {
    render(
      <Toast message="Test message" type="info" onClose={jest.fn()} />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Test message");
  });

  it("invokes onClose when close button is clicked", () => {
    const handleClose = jest.fn();
    render(
      <Toast message="Dismiss me" type="info" onClose={handleClose} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("applies style variants", () => {
    const { rerender, container } = render(
      <Toast message="Success" type="success" onClose={jest.fn()} />,
    );

    expect(container.firstChild).toHaveClass(
      "bg-green-50",
      "border-green-500",
      "text-green-800",
    );

    rerender(<Toast message="Error" type="error" onClose={jest.fn()} />);
    expect(container.firstChild).toHaveClass(
      "bg-red-50",
      "border-red-500",
      "text-red-800",
    );

    rerender(<Toast message="Info" type="info" onClose={jest.fn()} />);
    expect(container.firstChild).toHaveClass(
      "bg-blue-50",
      "border-blue-500",
      "text-blue-800",
    );
  });

  it("auto-dismisses after duration", () => {
    const handleClose = jest.fn();
    render(
      <Toast
        message="Auto close"
        type="info"
        onClose={handleClose}
        duration={2000}
      />,
    );

    act(() => {
      jest.advanceTimersByTime(2000);
    });

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
