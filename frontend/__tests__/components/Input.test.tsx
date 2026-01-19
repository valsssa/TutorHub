import { render, screen, fireEvent } from "@testing-library/react";
import Input from "@/components/Input";

const originalCrypto = global.crypto;

beforeAll(() => {
  Object.defineProperty(global, "crypto", {
    value: {
      ...originalCrypto,
      randomUUID: jest.fn(() => "test-uuid"),
    },
    configurable: true,
  });
});

afterAll(() => {
  Object.defineProperty(global, "crypto", {
    value: originalCrypto,
  });
});

describe("Input component", () => {
  it("renders input with label", () => {
    render(<Input label="Email" name="email" />);
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
  });

  it("renders input without label", () => {
    render(<Input name="test" placeholder="Enter value" />);
    expect(screen.getByPlaceholderText("Enter value")).toBeInTheDocument();
  });

  it("handles onChange events", () => {
    const handleChange = jest.fn();
    render(<Input name="test" onChange={handleChange} />);

    fireEvent.change(screen.getByRole("textbox"), {
      target: { value: "test value" },
    });
    expect(handleChange).toHaveBeenCalled();
  });

  it("displays error message", () => {
    render(<Input label="Email" name="email" error="Invalid email" />);
    expect(screen.getByText("Invalid email")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveClass("border-red-500");
  });

  it("respects required and disabled props", () => {
    render(<Input label="Username" name="username" required disabled />);
    const input = screen.getByRole("textbox", { name: /username/i });
    expect(input).toBeRequired();
    expect(input).toBeDisabled();
  });

  it("supports different input types", () => {
    const { rerender } = render(
      <Input label="Password" name="password" type="password" />,
    );
    expect(
      (screen.getByLabelText("Password") as HTMLInputElement).type,
    ).toBe("password");

    rerender(<Input label="Email" name="email" type="email" />);
    expect(
      (screen.getByLabelText("Email") as HTMLInputElement).type,
    ).toBe("email");

    rerender(<Input label="Age" name="age" type="number" />);
    expect(
      (screen.getByLabelText("Age") as HTMLInputElement).type,
    ).toBe("number");
  });

  it("applies custom className", () => {
    render(<Input name="test" className="custom-input" />);
    expect(screen.getByRole("textbox")).toHaveClass("custom-input");
  });

  it("forwards additional props", () => {
    render(<Input name="test" placeholder="Test" maxLength={10} />);
    const input = screen.getByPlaceholderText("Test");
    expect(input).toHaveAttribute("maxLength", "10");
  });

  it("sets input value correctly", () => {
    render(<Input name="test" value="initial value" onChange={() => {}} />);
    expect(screen.getByRole("textbox")).toHaveValue("initial value");
  });
});
