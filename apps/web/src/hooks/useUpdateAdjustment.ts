import { useState, useCallback } from "react";
import { updateInvoiceLineItemAdjustments } from "../api/invoiceLineItems";
import type { InvoiceLineItemResponse } from "../types/invoice";

export function useUpdateAdjustment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateAdjustment = useCallback(
    async (
      invoiceLineItemId: number,
      adjustments: string
    ): Promise<InvoiceLineItemResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await updateInvoiceLineItemAdjustments(
          invoiceLineItemId,
          { adjustments }
        );
        return result;
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Update failed"));
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { updateAdjustment, loading, error };
}
