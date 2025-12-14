import { apiClient } from "./client";
import type { CampaignListResponse, CampaignDetail } from "../types/campaign";
import type { Pagination } from "../types/common";

export async function fetchCampaigns(
  pagination?: Pagination
): Promise<CampaignListResponse> {
  const params = new URLSearchParams();
  if (pagination?.limit) params.set("limit", String(pagination.limit));
  if (pagination?.offset) params.set("offset", String(pagination.offset));

  const query = params.toString();
  return apiClient<CampaignListResponse>(
    `/api/v1/campaigns${query ? `?${query}` : ""}`
  );
}

export async function fetchCampaign(id: number): Promise<CampaignDetail> {
  return apiClient<CampaignDetail>(`/api/v1/campaigns/${id}`);
}
