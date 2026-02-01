import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "@/app/login/page";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
};

jest.mock("@/components/ToastContainer", () => ({
  useToast: () => toastMocks,
}));

jest.mock("@/lib/api", () => ({
  auth: {
    login: jest.fn(),
  },
}));

describe("LoginPage", () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
    });
  });

  it("renders login form", () => {
    render(<LoginPage />);

    expect(
      screen.getByRole("heading", { name: /welcome back/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /sign in/i }),
    ).toBeInTheDocument();
  });

  it("shows validation errors for empty submission", async () => {
    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/email is required/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/password is required/i),
      ).toBeInTheDocument();
    });
  });

  it("submits credentials and redirects on success", async () => {
    (auth.login as jest.Mock).mockResolvedValueOnce("fake-token");

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "student@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "secret123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(auth.login).toHaveBeenCalledWith(
        "student@example.com",
        "secret123",
      );
      expect(toastMocks.showSuccess).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("surface errors from login attempts", async () => {
    (auth.login as jest.Mock).mockRejectedValueOnce({
      response: { data: { detail: "Invalid credentials" } },
    });

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "student@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: "badpass" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(toastMocks.showError).toHaveBeenCalledWith(
        "Invalid credentials",
      );
    });
  });

  it("links to registration page", () => {
    render(<LoginPage />);

    expect(
      screen.getByRole("link", { name: /sign up/i }),
    ).toHaveAttribute("href", "/register");
  });
});
