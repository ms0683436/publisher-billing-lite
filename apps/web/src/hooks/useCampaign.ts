import { useState, useEffect, useCallback } from "react";
import { fetchCampaign } from "../api/campaigns";
import type { CampaignDetail } from "../types/campaign";

export function useCampaign(id: number) {
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCampaign(id);
      setCampaign(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  return { campaign, loading, error, refetch: load };
}
