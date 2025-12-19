import { useState, useEffect, useCallback } from "react";
import { fetchCampaigns } from "../api/campaigns";
import type { CampaignListItem } from "../types/campaign";
import type { CampaignListParams } from "../types/common";

export function useCampaigns(params?: CampaignListParams) {
  const [campaigns, setCampaigns] = useState<CampaignListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const { limit, offset, search, sortBy, sortDir } = params ?? {};

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchCampaigns({
        limit,
        offset,
        search,
        sortBy,
        sortDir,
      });
      setCampaigns(response.campaigns);
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

  return { campaigns, total, loading, error, refetch: load };
}
