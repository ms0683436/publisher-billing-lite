import { Box, Typography, Alert, CircularProgress } from "@mui/material";
import { useComments } from "../../hooks/useComments";
import { useAuth } from "../../hooks/useAuth";
import { CommentForm } from "./CommentForm";
import { CommentList } from "./CommentList";

interface CommentSectionProps {
  campaignId: number;
}

export function CommentSection({ campaignId }: CommentSectionProps) {
  const { user } = useAuth();
  const {
    comments,
    total,
    loading,
    error,
    addComment,
    editComment,
    removeComment,
  } = useComments(campaignId);

  const handleAddComment = async (content: string) => {
    if (!user) return;
    await addComment(content, user.id);
  };

  const handleReply = async (content: string, parentId: number) => {
    if (!user) return;
    await addComment(content, user.id, parentId);
  };

  const handleEdit = async (commentId: number, content: string) => {
    if (!user) return;
    await editComment(commentId, content, user.id);
  };

  const handleDelete = async (commentId: number, parentId: number | null) => {
    if (!user) return;
    await removeComment(commentId, user.id, parentId);
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load comments: {error.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Comments ({total})
      </Typography>

      <CommentList
        comments={comments}
        currentUserId={user?.id ?? null}
        onReply={handleReply}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {user && (
        <Box sx={{ mt: 3 }}>
          <CommentForm onSubmit={handleAddComment} />
        </Box>
      )}
    </Box>
  );
}
