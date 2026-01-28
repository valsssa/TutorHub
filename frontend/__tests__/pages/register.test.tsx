import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import RegisterPage from "@/app/register/page";
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
    register: jest.fn(),
    login: jest.fn(),
  },
}));

describe("RegisterPage", () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
    });
  });

  it("renders registration form controls", () => {
    render(<RegisterPage />);

    expect(
      screen.getByRole("heading", { name: /create account/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /create account/i }),
    ).toBeInTheDocument();
  });

  it("validates required fields", async () => {
    render(<RegisterPage />);

    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/email is required/i),
      ).toBeInTheDocument();
      expect(
        screen.getByText(/password is required/i),
      ).toBeInTheDocument();
    });
  });

  it("submits student registration and redirects to login", async () => {
    (auth.register as jest.Mock).mockResolvedValueOnce({
      id: 1,
      email: "student@example.com",
      role: "student",
    });

    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "student@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(auth.register).toHaveBeenCalledWith(
        "student@example.com",
        "password123",
        "student",
      );
      expect(toastMocks.showSuccess).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });

  it("submits tutor registration and redirects to onboarding", async () => {
    (auth.register as jest.Mock).mockResolvedValueOnce({
      id: 20,
      email: "tutor@example.com",
      role: "tutor",
    });
    (auth.login as jest.Mock).mockResolvedValueOnce("token");

    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "tutor@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(
      screen.getByLabelText(/i want to register as a tutor/i),
    );
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(auth.register).toHaveBeenCalledWith(
        "tutor@example.com",
        "password123",
        "tutor",
      );
      expect(auth.login).toHaveBeenCalledWith(
        "tutor@example.com",
        "password123",
      );
      expect(toastMocks.showSuccess).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith("/tutor/onboarding");
    });
  });

  it("shows errors surfaced from backend", async () => {
    (auth.register as jest.Mock).mockRejectedValueOnce({
      response: { data: { detail: "Email already registered" } },
    });

    render(<RegisterPage />);

    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: "existing@example.com" },
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(toastMocks.showError).toHaveBeenCalledWith(
        "Email already registered",
      );
    });
  });

  it("links back to login screen", () => {
    render(<RegisterPage />);

    expect(
      screen.getByRole("link", { name: /sign in/i }),
    ).toHaveAttribute("href", "/login");
  });
});
