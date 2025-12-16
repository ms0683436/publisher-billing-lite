import { Box, Typography, Alert, CircularProgress } from "@mui/material";
import { useComments } from "../../hooks/useComments";
import { useCurrentUser } from "../../hooks/useCurrentUser";
import { CommentForm } from "./CommentForm";
import { CommentList } from "./CommentList";

interface CommentSectionProps {
  campaignId: number;
}

export function CommentSection({ campaignId }: CommentSectionProps) {
  const { currentUser } = useCurrentUser();
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
    if (!currentUser) return;
    await addComment(content, currentUser.id);
  };

  const handleReply = async (content: string, parentId: number) => {
    if (!currentUser) return;
    await addComment(content, currentUser.id, parentId);
  };

  const handleEdit = async (commentId: number, content: string) => {
    if (!currentUser) return;
    await editComment(commentId, content, currentUser.id);
  };

  const handleDelete = async (commentId: number, parentId: number | null) => {
    if (!currentUser) return;
    await removeComment(commentId, currentUser.id, parentId);
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

      {!currentUser && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Select a user from the header to post comments.
        </Alert>
      )}

      <CommentList
        comments={comments}
        currentUserId={currentUser?.id ?? null}
        onReply={handleReply}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {currentUser && (
        <Box sx={{ mt: 3 }}>
          <CommentForm onSubmit={handleAddComment} />
        </Box>
      )}
    </Box>
  );
}
