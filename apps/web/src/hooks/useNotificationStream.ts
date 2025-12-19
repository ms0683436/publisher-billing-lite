import { useEffect, useRef, useCallback } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { getAccessToken } from "../api/client";
import type { Notification } from "../types/notification";

interface UseNotificationStreamOptions {
  onNotification: (notification: Notification) => void;
  /** Called when SSE reconnects (after initial connection). Use this to refetch data. */
  onReconnect?: () => void;
  enabled?: boolean;
}

/**
 * Validates that a parsed object has the required Notification fields.
 */
function isValidNotification(data: unknown): data is Notification {
  if (typeof data !== "object" || data === null) return false;
  const obj = data as Record<string, unknown>;
  return (
    typeof obj.id === "number" &&
    typeof obj.message === "string" &&
    typeof obj.type === "string" &&
    typeof obj.is_read === "boolean"
  );
}

/**
 * Hook for receiving real-time notifications via SSE.
 *
 * Uses @microsoft/fetch-event-source for SSE with custom headers support.
 * Implements exponential backoff for reconnection on errors.
 */
export function useNotificationStream({
  onNotification,
  onReconnect,
  enabled = true,
}: UseNotificationStreamOptions) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null
  );
  const reconnectDelayRef = useRef(1000); // Start with 1 second
  const connectRef = useRef<() => void>(() => {});
  const hasConnectedOnceRef = useRef(false);

  const connect = useCallback(() => {
    if (!enabled) return;

    const token = getAccessToken();
    if (!token) {
      // No token, skip connection (will retry when user logs in)
      return;
    }

    // Abort existing connection if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const url = "/api/v1/notifications/stream";

    fetchEventSource(url, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: abortController.signal,
      onopen: async (response) => {
        if (response.ok) {
          // Reset reconnect delay on successful connection
          reconnectDelayRef.current = 1000;

          // Call onReconnect if this is a reconnection (not first connect)
          if (hasConnectedOnceRef.current && onReconnect) {
            onReconnect();
          }
          hasConnectedOnceRef.current = true;
        } else {
          throw new Error(`SSE connection failed: ${response.status}`);
        }
      },
      onmessage: (event) => {
        try {
          const data = JSON.parse(event.data);

          // Validate the notification structure
          if (!isValidNotification(data)) {
            if (import.meta.env.DEV) {
              console.debug(
                "[useNotificationStream] Invalid notification structure:",
                data
              );
            }
            return;
          }

          onNotification(data);
        } catch (e) {
          // Log parse errors in development for debugging
          if (import.meta.env.DEV) {
            console.debug(
              "[useNotificationStream] Failed to parse SSE message:",
              event.data,
              e
            );
          }
        }
      },
      onerror: (err) => {
        // Don't schedule reconnect if this was a user-initiated abort
        if (abortController.signal.aborted) {
          return;
        }

        // Exponential backoff with max delay of 30 seconds
        const delay = Math.min(reconnectDelayRef.current, 30000);
        reconnectDelayRef.current = delay * 2;

        reconnectTimeoutRef.current = setTimeout(() => {
          connectRef.current();
        }, delay);

        // Throw to stop the default retry behavior
        throw err;
      },
      openWhenHidden: true, // Keep connection when tab is hidden
    });
  }, [enabled, onNotification, onReconnect]);

  // Keep the ref in sync with the latest connect function
  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  return { disconnect };
}
