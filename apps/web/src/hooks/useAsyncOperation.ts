import { useState, useCallback, useEffect, useRef } from "react";

interface UseAsyncOperationOptions<TParams, TResult> {
  /** The async function to execute */
  operation: (params: TParams, signal?: AbortSignal) => Promise<TResult>;
  /** Parameters to pass to the operation */
  params: TParams;
  /** Whether to run immediately on mount/params change (default: true) */
  immediate?: boolean;
}

interface UseAsyncOperationReturn<TResult> {
  data: TResult | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

/**
 * Generic hook for managing async operations with loading, error states, and abort support.
 * Reduces code duplication across data fetching hooks.
 */
export function useAsyncOperation<TParams, TResult>({
  operation,
  params,
  immediate = true,
}: UseAsyncOperationOptions<TParams, TResult>): UseAsyncOperationReturn<TResult> {
  const [data, setData] = useState<TResult | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<Error | null>(null);

  // Use ref to track current abort controller
  const abortControllerRef = useRef<AbortController | null>(null);

  const execute = useCallback(async () => {
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const result = await operation(params, controller.signal);
      // Only update state if this request wasn't aborted
      if (!controller.signal.aborted) {
        setData(result);
      }
    } catch (err) {
      // Ignore abort errors
      if (err instanceof Error && err.name === "AbortError") {
        return;
      }
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err : new Error("Unknown error"));
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [operation, params]);

  useEffect(() => {
    if (immediate) {
      execute();
    }

    // Cleanup: abort any pending request when component unmounts or params change
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [execute, immediate]);

  return {
    data,
    loading,
    error,
    refetch: execute,
  };
}
