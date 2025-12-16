import { Box, Typography } from "@mui/material";
import type { Comment } from "../../types/comment";
import { CommentItem } from "./CommentItem";

interface CommentListProps {
  comments: Comment[];
  currentUserId: number | null;
  onReply: (content: string, parentId: number) => Promise<void>;
  onEdit: (commentId: number, content: string) => Promise<void>;
  onDelete: (commentId: number, parentId: number | null) => Promise<void>;
}

export function CommentList({
  comments,
  currentUserId,
  onReply,
  onEdit,
  onDelete,
}: CommentListProps) {
  if (comments.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
        No comments yet. Be the first to comment!
      </Typography>
    );
  }

  return (
    <Box>
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          currentUserId={currentUserId}
          depth={0}
          onReply={onReply}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </Box>
  );
}
