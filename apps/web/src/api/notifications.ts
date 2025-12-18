import { apiClient } from "./client";
import type {
  NotificationListResponse,
  NotificationReadResponse,
} from "../types/notification";

export interface NotificationListParams {
  limit?: number;
  offset?: number;
}

export async function fetchNotifications(
  params: NotificationListParams = {}
): Promise<NotificationListResponse> {
  const searchParams = new URLSearchParams();
  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    searchParams.set("offset", String(params.offset));
  }

  const query = searchParams.toString();
  return apiClient<NotificationListResponse>(
    `/api/v1/notifications${query ? `?${query}` : ""}`
  );
}

export async function markNotificationAsRead(
  notificationId: number
): Promise<NotificationReadResponse> {
  return apiClient<NotificationReadResponse>(
    `/api/v1/notifications/${notificationId}/read`,
    { method: "PATCH" }
  );
}

export async function markAllNotificationsAsRead(): Promise<NotificationReadResponse> {
  return apiClient<NotificationReadResponse>("/api/v1/notifications/read-all", {
    method: "PATCH",
  });
}
