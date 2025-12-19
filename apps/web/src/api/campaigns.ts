import { apiClient } from "./client";
import { buildUrl } from "./utils";
import type { CampaignListResponse, CampaignDetail } from "../types/campaign";
import type { CampaignListParams } from "../types/common";

export async function fetchCampaigns(
  params?: CampaignListParams
): Promise<CampaignListResponse> {
  const url = buildUrl("/api/v1/campaigns", {
    limit: params?.limit,
    offset: params?.offset,
    search: params?.search,
    sort_by: params?.sortBy,
    sort_dir: params?.sortDir,
  });
  return apiClient<CampaignListResponse>(url);
}

export async function fetchCampaign(id: number): Promise<CampaignDetail> {
  return apiClient<CampaignDetail>(`/api/v1/campaigns/${id}`);
}
