import { useState, useEffect, useCallback } from "react";
import { fetchInvoices } from "../api/invoices";
import type { InvoiceListItem } from "../types/invoice";
import type { Pagination } from "../types/common";

export function useInvoices(pagination?: Pagination) {
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const limit = pagination?.limit;
  const offset = pagination?.offset;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchInvoices({ limit, offset });
      setInvoices(response.invoices);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => {
    load();
  }, [load]);

  return { invoices, total, loading, error, refetch: load };
}
