import type { User } from "./user";

export interface Notification {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
  comment_id: number | null;
  actor: User | null;
  created_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface NotificationReadResponse {
  success: boolean;
  read_count: number;
}
