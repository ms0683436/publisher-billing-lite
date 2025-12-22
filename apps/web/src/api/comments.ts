import { apiClient } from "./client";
import type {
  Comment,
  CommentListResponse,
  CommentCreateRequest,
  CommentUpdateRequest,
} from "../types/comment";

export async function fetchCampaignComments(
  campaignId: number,
  signal?: AbortSignal
): Promise<CommentListResponse> {
  return apiClient<CommentListResponse>(
    `/api/v1/campaigns/${campaignId}/comments`,
    { signal }
  );
}

export async function createComment(
  data: CommentCreateRequest,
  userId: number
): Promise<Comment> {
  return apiClient<Comment>("/api/v1/comments", {
    method: "POST",
    body: JSON.stringify(data),
    headers: {
      "X-User-Id": String(userId),
    },
  });
}

export async function updateComment(
  commentId: number,
  data: CommentUpdateRequest,
  userId: number
): Promise<Comment> {
  return apiClient<Comment>(`/api/v1/comments/${commentId}`, {
    method: "PUT",
    body: JSON.stringify(data),
    headers: {
      "X-User-Id": String(userId),
    },
  });
}

export async function deleteComment(
  commentId: number,
  userId: number
): Promise<void> {
  await apiClient<void>(`/api/v1/comments/${commentId}`, {
    method: "DELETE",
    headers: {
      "X-User-Id": String(userId),
    },
  });
}
