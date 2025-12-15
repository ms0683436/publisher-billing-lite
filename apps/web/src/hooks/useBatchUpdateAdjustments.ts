import { useState, useCallback } from "react";
import { batchUpdateAdjustments } from "../api/invoiceLineItems";
import type {
  BatchAdjustmentsUpdate,
  BatchAdjustmentsResponse,
} from "../types/invoice";

export function useBatchUpdateAdjustments() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateAdjustments = useCallback(
    async (
      invoiceId: number,
      updates: BatchAdjustmentsUpdate
    ): Promise<BatchAdjustmentsResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await batchUpdateAdjustments(invoiceId, updates);
        return result;
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Batch update failed"));
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { updateAdjustments, loading, error };
}
