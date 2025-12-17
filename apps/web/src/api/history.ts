import { apiClient } from "./client";
import type { EntityType, ChangeHistoryListResponse } from "../types/history";

export async function fetchEntityHistory(
  entityType: EntityType,
  entityId: number,
  options?: { limit?: number; offset?: number }
): Promise<ChangeHistoryListResponse> {
  const params = new URLSearchParams();
  if (options?.limit !== undefined) {
    params.set("limit", String(options.limit));
  }
  if (options?.offset !== undefined) {
    params.set("offset", String(options.offset));
  }

  const queryString = params.toString();
  const url = `/api/v1/history/${entityType}/${entityId}${queryString ? `?${queryString}` : ""}`;

  return apiClient<ChangeHistoryListResponse>(url);
}
