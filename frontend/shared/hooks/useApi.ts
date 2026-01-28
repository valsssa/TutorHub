/**
 * Custom hook for API calls with loading and error states
 */
import { useState, useEffect, useCallback } from "react";
import { AxiosError } from "axios";
import { useToast } from "@/components/ToastContainer";

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: AxiosError) => void;
  autoFetch?: boolean;
  showErrorToast?: boolean;
}

interface UseApiReturn<T, TFunc extends (...args: any[]) => Promise<T>> {
  data: T | null;
  loading: boolean;
  error: AxiosError | null;
  refetch: (...args: Parameters<TFunc>) => Promise<void>;
  execute: (...args: Parameters<TFunc>) => Promise<T | null>;
}

export function useApi<T = any, TFunc extends (...args: any[]) => Promise<T> = (...args: any[]) => Promise<T>>(
  apiFunction: TFunc,
  options: UseApiOptions<T> = {},
): UseApiReturn<T, TFunc> {
  const {
    onSuccess,
    onError,
    autoFetch = false,
    showErrorToast = true,
  } = options;

  const { showError } = useToast();
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState<AxiosError | null>(null);

  const execute = useCallback(
    async (...args: Parameters<TFunc>): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const result = await apiFunction(...args);
        setData(result);
        onSuccess?.(result);
        return result;
      } catch (err) {
        const axiosError = err as AxiosError;
        setError(axiosError);

        if (showErrorToast) {
          const message =
            (axiosError.response?.data as any)?.detail ||
            axiosError.message ||
            "An error occurred";
          showError(message);
        }

        onError?.(axiosError);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, onSuccess, onError, showErrorToast, showError],
  );

  const refetch = useCallback(async (...args: Parameters<TFunc>) => {
    await execute(...args);
  }, [execute]);

  useEffect(() => {
    if (autoFetch) {
      void execute(...([] as unknown as Parameters<TFunc>));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoFetch]);

  return { data, loading, error, refetch, execute };
}
