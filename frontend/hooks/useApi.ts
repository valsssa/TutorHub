import { useState, useCallback } from "react";
import { useToast } from "@/components/ToastContainer";

/**
 * Maps HTTP status codes and API errors to user-friendly messages
 * Prevents exposing internal error details to users
 */
function getUserFriendlyErrorMessage(error: any): string {
  const status = error.response?.status;
  const detail = error.response?.data?.detail;

  // Handle specific HTTP status codes
  switch (status) {
    case 400:
      // Validation errors can sometimes be shown, but sanitize
      if (typeof detail === "string" && detail.length < 100) {
        return detail;
      }
      return "Invalid request. Please check your input and try again.";
    case 401:
      return "Your session has expired. Please log in again.";
    case 403:
      return "You don't have permission to perform this action.";
    case 404:
      return "The requested resource was not found.";
    case 409:
      return "This action conflicts with existing data.";
    case 422:
      // Validation errors
      if (typeof detail === "string" && detail.length < 100) {
        return detail;
      }
      return "Please check your input and try again.";
    case 429:
      return "Too many requests. Please wait a moment and try again.";
    case 500:
    case 502:
    case 503:
    case 504:
      return "Server error. Please try again later.";
    default:
      // Network errors
      if (!error.response) {
        return "Network error. Please check your connection.";
      }
      return "An unexpected error occurred. Please try again.";
  }
}

interface UseApiReturn<T, Args extends unknown[]> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  execute: (...args: Args) => Promise<T | null>;
  reset: () => void;
}

export function useApi<T, Args extends unknown[] = unknown[]>(
  apiFunction: (...args: Args) => Promise<T>,
): UseApiReturn<T, Args> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { showError } = useToast();

  const execute = useCallback(
    async (...args: Args) => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiFunction(...args);
        setData(result);
        return result;
      } catch (err: any) {
        const error = err as Error;
        setError(error);
        showError(getUserFriendlyErrorMessage(err));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, showError],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}
