import { useState, useEffect, useCallback } from "react";
import { fetchInvoices } from "../api/invoices";
import type { InvoiceListItem } from "../types/invoice";
import type { InvoiceListParams } from "../types/common";

export function useInvoices(params?: InvoiceListParams) {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const { limit, offset, search, sortBy, sortDir } = params ?? {};

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchInvoices({
        limit,
        offset,
        search,
        sortBy,
        sortDir,
      });
      setInvoices(response.invoices);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [limit, offset, search, sortBy, sortDir]);

  useEffect(() => {
    load();
  }, [load]);

  return { invoices, total, loading, error, refetch: load };
}
