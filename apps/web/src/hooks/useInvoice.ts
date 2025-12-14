import { useState, useEffect, useCallback } from "react";
import { fetchInvoice } from "../api/invoices";
import type { InvoiceDetail } from "../types/invoice";

export function useInvoice(id: number) {
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInvoice(id);
      setInvoice(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return { invoice, loading, error, refetch: load };
}
