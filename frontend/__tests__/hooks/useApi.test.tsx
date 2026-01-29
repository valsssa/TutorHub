/**
 * Tests for useApi hook
 * Critical: API state management is used throughout the application
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { useApi } from "@/hooks/useApi";

// Mock the useToast hook
const mockShowError = jest.fn();

jest.mock("@/components/ToastContainer", () => ({
  useToast: () => ({
    showError: mockShowError,
    showSuccess: jest.fn(),
    showInfo: jest.fn(),
  }),
}));

describe("useApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("initial state", () => {
    it("initializes with null data and no loading", () => {
      const mockApiFunction = jest.fn().mockResolvedValue({ data: "test" });

      const { result } = renderHook(() => useApi(mockApiFunction));

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe("successful execution", () => {
    it("sets loading to true during execution", async () => {
      let resolvePromise: (value: any) => void;
      const mockApiFunction = jest.fn().mockImplementation(
        () =>
          new Promise((resolve) => {
            resolvePromise = resolve;
          })
      );

      const { result } = renderHook(() => useApi(mockApiFunction));

      act(() => {
        result.current.execute();
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise!({ success: true });
      });

      expect(result.current.loading).toBe(false);
    });

    it("sets data on successful response", async () => {
      const responseData = { id: 1, name: "Test User" };
      const mockApiFunction = jest.fn().mockResolvedValue(responseData);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(responseData);
      expect(result.current.error).toBeNull();
    });

    it("returns data from execute function", async () => {
      const responseData = { id: 1, name: "Test" };
      const mockApiFunction = jest.fn().mockResolvedValue(responseData);

      const { result } = renderHook(() => useApi(mockApiFunction));

      let returnedData: typeof responseData | null = null;

      await act(async () => {
        returnedData = await result.current.execute();
      });

      expect(returnedData).toEqual(responseData);
    });

    it("passes arguments to the API function", async () => {
      const mockApiFunction = jest.fn().mockResolvedValue({ success: true });

      const { result } = renderHook(() =>
        useApi<{ success: boolean }, [number, string]>(mockApiFunction)
      );

      await act(async () => {
        await result.current.execute(123, "test-arg");
      });

      expect(mockApiFunction).toHaveBeenCalledWith(123, "test-arg");
    });
  });

  describe("error handling", () => {
    it("sets error on failed request", async () => {
      const error = new Error("Network error");
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).toBe(error);
      expect(result.current.data).toBeNull();
    });

    it("returns null on error", async () => {
      const mockApiFunction = jest.fn().mockRejectedValue(new Error("Failed"));

      const { result } = renderHook(() => useApi(mockApiFunction));

      let returnedData: any;

      await act(async () => {
        returnedData = await result.current.execute();
      });

      expect(returnedData).toBeNull();
    });

    it("shows toast with friendly message for 400 error", async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: "Invalid input" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith("Invalid input");
    });

    it("shows generic message for 400 with long detail", async () => {
      const error = {
        response: {
          status: 400,
          data: { detail: "A".repeat(200) }, // Very long error message
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "Invalid request. Please check your input and try again."
      );
    });

    it("shows session expired message for 401 error", async () => {
      const error = {
        response: {
          status: 401,
          data: { detail: "Unauthorized" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "Your session has expired. Please log in again."
      );
    });

    it("shows permission message for 403 error", async () => {
      const error = {
        response: {
          status: 403,
          data: { detail: "Forbidden" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "You don't have permission to perform this action."
      );
    });

    it("shows not found message for 404 error", async () => {
      const error = {
        response: {
          status: 404,
          data: { detail: "Not Found" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "The requested resource was not found."
      );
    });

    it("shows conflict message for 409 error", async () => {
      const error = {
        response: {
          status: 409,
          data: { detail: "Conflict" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "This action conflicts with existing data."
      );
    });

    it("shows validation message for 422 error with short detail", async () => {
      const error = {
        response: {
          status: 422,
          data: { detail: "Email is invalid" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith("Email is invalid");
    });

    it("shows rate limit message for 429 error", async () => {
      const error = {
        response: {
          status: 429,
          data: { detail: "Rate limited" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "Too many requests. Please wait a moment and try again."
      );
    });

    it("shows server error message for 500+ errors", async () => {
      const statusCodes = [500, 502, 503, 504];

      for (const status of statusCodes) {
        jest.clearAllMocks();
        const error = {
          response: {
            status,
            data: { detail: "Server error" },
          },
        };
        const mockApiFunction = jest.fn().mockRejectedValue(error);

        const { result } = renderHook(() => useApi(mockApiFunction));

        await act(async () => {
          await result.current.execute();
        });

        expect(mockShowError).toHaveBeenCalledWith(
          "Server error. Please try again later."
        );
      }
    });

    it("shows network error message when no response", async () => {
      const error = { message: "Network Error" }; // No response property
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "Network error. Please check your connection."
      );
    });

    it("shows generic error message for unknown status", async () => {
      const error = {
        response: {
          status: 418, // I'm a teapot
          data: { detail: "Teapot" },
        },
      };
      const mockApiFunction = jest.fn().mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(mockShowError).toHaveBeenCalledWith(
        "An unexpected error occurred. Please try again."
      );
    });
  });

  describe("reset function", () => {
    it("resets data, error, and loading state", async () => {
      const responseData = { id: 1 };
      const mockApiFunction = jest.fn().mockResolvedValue(responseData);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(responseData);

      act(() => {
        result.current.reset();
      });

      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it("resets error state after failed request", async () => {
      const mockApiFunction = jest.fn().mockRejectedValue(new Error("Failed"));

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).not.toBeNull();

      act(() => {
        result.current.reset();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe("multiple executions", () => {
    it("clears previous error on new execution", async () => {
      const mockApiFunction = jest
        .fn()
        .mockRejectedValueOnce(new Error("First error"))
        .mockResolvedValueOnce({ success: true });

      const { result } = renderHook(() => useApi(mockApiFunction));

      // First call - fails
      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).not.toBeNull();

      // Second call - succeeds
      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.data).toEqual({ success: true });
    });

    it("updates data on subsequent successful calls", async () => {
      const mockApiFunction = jest
        .fn()
        .mockResolvedValueOnce({ id: 1 })
        .mockResolvedValueOnce({ id: 2 });

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual({ id: 1 });

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual({ id: 2 });
    });
  });

  describe("function stability", () => {
    it("execute function remains stable across renders", () => {
      const mockApiFunction = jest.fn().mockResolvedValue({});

      const { result, rerender } = renderHook(() => useApi(mockApiFunction));

      const firstExecute = result.current.execute;

      rerender();

      expect(result.current.execute).toBe(firstExecute);
    });

    it("reset function remains stable across renders", () => {
      const mockApiFunction = jest.fn().mockResolvedValue({});

      const { result, rerender } = renderHook(() => useApi(mockApiFunction));

      const firstReset = result.current.reset;

      rerender();

      expect(result.current.reset).toBe(firstReset);
    });
  });

  describe("edge cases", () => {
    it("handles undefined response data", async () => {
      const mockApiFunction = jest.fn().mockResolvedValue(undefined);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toBeUndefined();
      expect(result.current.loading).toBe(false);
    });

    it("handles null response data", async () => {
      const mockApiFunction = jest.fn().mockResolvedValue(null);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it("handles array response data", async () => {
      const arrayData = [{ id: 1 }, { id: 2 }];
      const mockApiFunction = jest.fn().mockResolvedValue(arrayData);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(arrayData);
    });

    it("handles primitive response data", async () => {
      const mockApiFunction = jest.fn().mockResolvedValue(42);

      const { result } = renderHook(() => useApi(mockApiFunction));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toBe(42);
    });
  });

  describe("concurrent calls", () => {
    it("handles rapid successive calls", async () => {
      let callCount = 0;
      const mockApiFunction = jest.fn().mockImplementation(async () => {
        callCount++;
        await new Promise((resolve) => setTimeout(resolve, 10));
        return { callNumber: callCount };
      });

      const { result } = renderHook(() => useApi(mockApiFunction));

      // Start multiple calls rapidly
      act(() => {
        result.current.execute();
        result.current.execute();
        result.current.execute();
      });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      // All calls should have been made
      expect(mockApiFunction).toHaveBeenCalledTimes(3);
    });
  });
});
