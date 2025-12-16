import { useState } from "react";
import { Box, Typography, IconButton, Tooltip } from "@mui/material";
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Reply as ReplyIcon,
} from "@mui/icons-material";
import type { Comment } from "../../types/comment";
import { CommentForm } from "./CommentForm";

interface CommentItemProps {
  comment: Comment;
  currentUserId: number | null;
  depth?: number;
  onReply?: (content: string, parentId: number) => Promise<void>;
  onEdit: (commentId: number, content: string) => Promise<void>;
  onDelete: (commentId: number, parentId: number | null) => Promise<void>;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString();
}

export function CommentItem({
  comment,
  currentUserId,
  depth = 0,
  onReply,
  onEdit,
  onDelete,
}: CommentItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showReplyForm, setShowReplyForm] = useState(false);

  const isAuthor = currentUserId === comment.author.id;
  const canReply = depth === 0 && onReply;

  const handleEditSubmit = async (content: string) => {
    await onEdit(comment.id, content);
    setIsEditing(false);
  };

  const handleDelete = async () => {
    await onDelete(comment.id, comment.parent_id);
  };

  const handleReplySubmit = async (content: string) => {
    if (onReply) {
      await onReply(content, comment.id);
      setShowReplyForm(false);
    }
  };

  // Render mentions with highlighting
  const renderContent = (text: string) => {
    const parts = text.split(/(@\w+)/g);
    return parts.map((part, i) => {
      if (part.startsWith("@")) {
        const username = part.slice(1);
        const isMentioned = comment.mentions.some(
          (m) => m.username.toLowerCase() === username.toLowerCase()
        );
        return (
          <Typography
            key={i}
            component="span"
            sx={{
              color: isMentioned ? "primary.main" : "inherit",
              fontWeight: isMentioned ? 500 : "inherit",
            }}
          >
            {part}
          </Typography>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
            <Typography variant="subtitle2" fontWeight={600}>
              @{comment.author.username}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {formatDate(comment.created_at)}
              {comment.updated_at !== comment.created_at && " (edited)"}
            </Typography>
          </Box>

          {isEditing ? (
            <CommentForm
              initialValue={comment.content}
              onSubmit={handleEditSubmit}
              onCancel={() => setIsEditing(false)}
              submitLabel="Save"
              autoFocus
            />
          ) : (
            <Typography
              variant="body2"
              sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
            >
              {renderContent(comment.content)}
            </Typography>
          )}
        </Box>

        {/* Action buttons in top-right corner */}
        {!isEditing && (
          <Box sx={{ display: "flex", gap: 0.5 }}>
            {canReply && (
              <Tooltip title="Reply">
                <IconButton
                  size="small"
                  onClick={() => setShowReplyForm(true)}
                >
                  <ReplyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {isAuthor && (
              <Tooltip title="Edit">
                <IconButton size="small" onClick={() => setIsEditing(true)}>
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {isAuthor && (
              <Tooltip title="Delete">
                <IconButton size="small" onClick={handleDelete}>
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        )}
      </Box>

      {/* Reply form */}
      {showReplyForm && (
        <Box sx={{ mt: 2, ml: 4 }}>
          <CommentForm
            onSubmit={handleReplySubmit}
            onCancel={() => setShowReplyForm(false)}
            submitLabel="Reply"
            placeholder="Write a reply..."
            autoFocus
          />
        </Box>
      )}

      {/* Nested replies (only for top-level comments) */}
      {depth === 0 && comment.replies.length > 0 && (
        <Box sx={{ ml: 4, mt: 2, borderLeft: 2, borderColor: "divider", pl: 2 }}>
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              currentUserId={currentUserId}
              depth={1}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}
