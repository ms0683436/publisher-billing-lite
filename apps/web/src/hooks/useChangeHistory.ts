import { useState, useEffect, useCallback } from "react";
import { fetchEntityHistory } from "../api/history";
import type { EntityType, ChangeHistory } from "../types/history";

export function useChangeHistory(entityType: EntityType, entityId: number) {
  const [history, setHistory] = useState<ChangeHistory[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchEntityHistory(entityType, entityId);
      setHistory(response.history);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [entityType, entityId]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    history,
    total,
    loading,
    error,
    refetch: load,
  };
}
