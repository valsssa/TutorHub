import { render } from "@testing-library/react";
import LoadingSpinner from "@/components/LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders spinner element with animation", () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("applies size variants", () => {
    const { rerender, container } = render(<LoadingSpinner size="sm" />);
    let spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("h-4", "w-4");

    rerender(<LoadingSpinner size="md" />);
    spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("h-8", "w-8");

    rerender(<LoadingSpinner size="lg" />);
    spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("h-12", "w-12");
  });

  it("supports color variants", () => {
    const { rerender, container } = render(
      <LoadingSpinner color="primary" />,
    );
    let spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("border-primary-600");

    rerender(<LoadingSpinner color="white" />);
    spinner = container.querySelector(".animate-spin");
    expect(spinner).toHaveClass("border-white");
  });
});
