import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AvatarUploader from "@/components/AvatarUploader";
import { useAvatar } from "@/lib/useAvatar";

jest.mock("@/lib/useAvatar");

const toastMocks = {
  showSuccess: jest.fn(),
  showError: jest.fn(),
  showInfo: jest.fn(),
};

jest.mock("@/components/ToastContainer", () => ({
  useToast: () => toastMocks,
}));

const createObjectURLMock = jest.fn(() => "blob:mock");
const revokeObjectURLMock = jest.fn();
const uploadMock = jest.fn();
const removeMock = jest.fn();

class MockImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  width = 400;
  height = 400;

  set src(_: string) {
    setTimeout(() => this.onload && this.onload());
  }
}

describe("AvatarUploader", () => {
  beforeAll(() => {
    global.URL.createObjectURL = createObjectURLMock;
    global.URL.revokeObjectURL = revokeObjectURLMock;
    // @ts-expect-error - override global Image for tests
    global.Image = MockImage;
  });

  beforeEach(() => {
    jest.clearAllMocks();
    uploadMock.mockResolvedValue({
      avatarUrl: "https://example.com/avatar.webp",
      expiresAt: "2025-02-14T00:00:00Z",
    });
    removeMock.mockResolvedValue(undefined);
    (useAvatar as jest.Mock).mockImplementation(
      ({ onChange }: { onChange?: (url: string | null) => void }) => ({
        avatarUrl: null,
        setAvatarUrl: jest.fn(),
        uploadAvatar: async (file: File) => {
          await uploadMock(file);
          const result = {
            avatarUrl: "https://example.com/avatar.webp",
            expiresAt: "2025-02-14T00:00:00Z",
          };
          onChange?.(result.avatarUrl);
          return result;
        },
        removeAvatar: async () => {
          await removeMock();
          onChange?.(null);
        },
        uploading: false,
        deleting: false,
      }),
    );
  });

  it("calls upload hook when selecting a valid file", async () => {
    const onAvatarChange = jest.fn();
    render(<AvatarUploader onAvatarChange={onAvatarChange} />);

    const fileInput = screen.getByTestId("avatar-file-input") as HTMLInputElement;
    const file = new File([new Uint8Array([1, 2, 3])], "avatar.png", {
      type: "image/png",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(uploadMock).toHaveBeenCalledWith(file);
      expect(toastMocks.showSuccess).toHaveBeenCalled();
      expect(onAvatarChange).toHaveBeenCalledWith("https://example.com/avatar.webp");
    });
  });

  it("shows remove button for self-service uploads", () => {
    render(<AvatarUploader />);
    expect(screen.getByRole("button", { name: /remove/i })).toBeInTheDocument();
  });

  it("omits remove button when admin override", () => {
    render(<AvatarUploader adminUserId={42} />);
    expect(screen.queryByRole("button", { name: /remove/i })).not.toBeInTheDocument();
  });

  it("shows validation error when uploading unsupported type", async () => {
    render(<AvatarUploader />);

    const fileInput = screen.getByTestId("avatar-file-input") as HTMLInputElement;
    const file = new File([new Uint8Array([1, 2])], "avatar.gif", {
      type: "image/gif",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(toastMocks.showError).toHaveBeenCalledWith("Only JPEG and PNG images are supported");
      expect(screen.getByText(/only jpeg and png images are supported/i)).toBeInTheDocument();
      expect(uploadMock).not.toHaveBeenCalled();
    });
  });

  it("invokes remove hook on remove button", async () => {
    (useAvatar as jest.Mock).mockImplementation(
      ({ onChange }: { onChange?: (url: string | null) => void }) => ({
        avatarUrl: "https://example.com/avatar.webp",
        setAvatarUrl: jest.fn(),
        uploadAvatar: async (file: File) => {
          await uploadMock(file);
          const result = {
            avatarUrl: "https://example.com/avatar.webp",
            expiresAt: "2025-02-14T00:00:00Z",
          };
          onChange?.(result.avatarUrl);
          return result;
        },
        removeAvatar: async () => {
          await removeMock();
          onChange?.(null);
        },
        uploading: false,
        deleting: false,
      }),
    );

    render(<AvatarUploader />);

    fireEvent.click(screen.getByRole("button", { name: /remove/i }));

    await waitFor(() => {
      expect(removeMock).toHaveBeenCalled();
    });
  });
});
