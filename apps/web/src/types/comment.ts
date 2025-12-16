import type { User } from "./user";

export interface Comment {
  id: number;
  content: string;
  campaign_id: number;
  author: User;
  mentions: User[];
  parent_id: number | null;
  replies: Comment[];
  replies_count: number;
  created_at: string;
  updated_at: string;
}

export interface CommentListResponse {
  comments: Comment[];
  total: number;
}

export interface CommentCreateRequest {
  content: string;
  campaign_id: number;
  parent_id?: number | null;
}

export interface CommentUpdateRequest {
  content: string;
}
