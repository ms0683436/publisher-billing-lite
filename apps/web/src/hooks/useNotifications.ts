import { useState, useEffect, useCallback, useRef } from "react";
import {
  fetchNotifications,
  markNotificationAsRead,
  markAllNotificationsAsRead,
} from "../api/notifications";
import type { Notification, NotificationReadResponse } from "../types/notification";
import type { Pagination } from "../types/common";

const DEFAULT_LIMIT = 5;

interface UseNotificationsOptions {
  /** Pagination settings. If not provided, uses default limit of 5 (for bell). */
  pagination?: Pagination;
  /** Enable SSE integration features (addNotification, seenIds tracking). Default: false */
  enableRealtime?: boolean;
}

interface UseNotificationsResult {
  notifications: Notification[];
  total: number;
  unreadCount: number;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  markAsRead: (notificationId: number) => Promise<void>;
  markAllAsRead: () => Promise<NotificationReadResponse>;
  /** Only available when enableRealtime is true */
  addNotification?: (notification: Notification) => void;
}

/**
 * Hook for managing notifications.
 *
 * @param options.pagination - Pagination settings (limit/offset). Defaults to limit=5.
 * @param options.enableRealtime - Enable SSE integration (addNotification, duplicate tracking).
 */
export function useNotifications(
  options: UseNotificationsOptions = {}
): UseNotificationsResult {
  const { pagination, enableRealtime = false } = options;

  const limit = pagination?.limit ?? DEFAULT_LIMIT;
  const offset = pagination?.offset ?? 0;

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  // Track seen notification IDs to prevent duplicate count updates (only for realtime)
  const seenIdsRef = useRef<Set<number>>(new Set());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchNotifications({ limit, offset });
      setNotifications(response.notifications);
      setTotal(response.total);
      setUnreadCount(response.unread_count);

      // Update seen IDs to prevent duplicates on SSE reconnect
      if (enableRealtime) {
        seenIdsRef.current = new Set(response.notifications.map((n) => n.id));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [limit, offset, enableRealtime]);

  useEffect(() => {
    load();
  }, [load]);

  const markAsRead = useCallback(async (notificationId: number) => {
    await markNotificationAsRead(notificationId);

    setNotifications((prev) =>
      prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));
  }, []);

  const markAllAsRead = useCallback(async (): Promise<NotificationReadResponse> => {
    const response = await markAllNotificationsAsRead();

    if (response.success) {
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    }

    return response;
  }, []);

  const addNotification = useCallback(
    (notification: Notification) => {
      // Check for duplicate using ref (survives re-renders, checked synchronously)
      if (seenIdsRef.current.has(notification.id)) {
        return;
      }

      // Mark as seen before any state updates
      seenIdsRef.current.add(notification.id);

      // Now safe to update all state
      setNotifications((prev) => [notification, ...prev.slice(0, limit - 1)]);
      setTotal((prev) => prev + 1);
      if (!notification.is_read) {
        setUnreadCount((prev) => prev + 1);
      }
    },
    [limit]
  );

  const result: UseNotificationsResult = {
    notifications,
    total,
    unreadCount,
    loading,
    error,
    refetch: load,
    markAsRead,
    markAllAsRead,
  };

  // Only include addNotification when realtime is enabled
  if (enableRealtime) {
    result.addNotification = addNotification;
  }

  return result;
}
