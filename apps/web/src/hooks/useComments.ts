import { useState, useEffect, useCallback } from "react";
import {
  fetchCampaignComments,
  createComment,
  updateComment,
  deleteComment,
} from "../api/comments";
import type { Comment } from "../types/comment";

export function useComments(campaignId: number) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchCampaignComments(campaignId);
      setComments(response.comments);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Unknown error"));
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    load();
  }, [load]);

  const addComment = useCallback(
    async (content: string, userId: number, parentId?: number) => {
      const newComment = await createComment(
        {
          content,
          campaign_id: campaignId,
          parent_id: parentId ?? null,
        },
        userId
      );

      if (parentId) {
        // Add reply to parent comment
        setComments((prev) =>
          prev.map((c) =>
            c.id === parentId
              ? {
                  ...c,
                  replies: [...c.replies, newComment],
                  replies_count: c.replies_count + 1,
                }
              : c
          )
        );
      } else {
        // Add new top-level comment at the end (oldest to newest order)
        setComments((prev) => [...prev, newComment]);
        setTotal((prev) => prev + 1);
      }

      return newComment;
    },
    [campaignId]
  );

  const editComment = useCallback(
    async (commentId: number, content: string, userId: number) => {
      const updated = await updateComment(commentId, { content }, userId);

      setComments((prev) =>
        prev.map((c) => {
          if (c.id === commentId) {
            return updated;
          }
          // Check in replies
          if (c.replies.some((r) => r.id === commentId)) {
            return {
              ...c,
              replies: c.replies.map((r) => (r.id === commentId ? updated : r)),
            };
          }
          return c;
        })
      );

      return updated;
    },
    []
  );

  const removeComment = useCallback(
    async (commentId: number, userId: number, parentId?: number | null) => {
      await deleteComment(commentId, userId);

      if (parentId) {
        // Remove reply from parent
        setComments((prev) =>
          prev.map((c) =>
            c.id === parentId
              ? {
                  ...c,
                  replies: c.replies.filter((r) => r.id !== commentId),
                  replies_count: c.replies_count - 1,
                }
              : c
          )
        );
      } else {
        // Remove top-level comment
        setComments((prev) => prev.filter((c) => c.id !== commentId));
        setTotal((prev) => prev - 1);
      }
    },
    []
  );

  return {
    comments,
    total,
    loading,
    error,
    refetch: load,
    addComment,
    editComment,
    removeComment,
  };
}
