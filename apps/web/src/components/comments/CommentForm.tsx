import { useState } from "react";
import { Box, Button, CircularProgress } from "@mui/material";
import { MentionInput } from "./MentionInput";

interface CommentFormProps {
  onSubmit: (content: string) => Promise<void>;
  onCancel?: () => void;
  initialValue?: string;
  submitLabel?: string;
  placeholder?: string;
  autoFocus?: boolean;
}

export function CommentForm({
  onSubmit,
  onCancel,
  initialValue = "",
  submitLabel = "Post",
  placeholder,
  autoFocus = false,
}: CommentFormProps) {
  const [content, setContent] = useState(initialValue);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    const trimmed = content.trim();
    if (!trimmed) return;

    setSubmitting(true);
    try {
      await onSubmit(trimmed);
      setContent("");
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Cmd/Ctrl + Enter to submit
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Box onKeyDown={handleKeyDown}>
      <MentionInput
        value={content}
        onChange={setContent}
        placeholder={placeholder}
        disabled={submitting}
        autoFocus={autoFocus}
      />
      <Box sx={{ mt: 1, display: "flex", gap: 1, justifyContent: "flex-end" }}>
        {onCancel && (
          <Button
            size="small"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancel
          </Button>
        )}
        <Button
          size="small"
          variant="contained"
          onClick={handleSubmit}
          disabled={submitting || !content.trim()}
          startIcon={submitting ? <CircularProgress size={16} /> : undefined}
        >
          {submitLabel}
        </Button>
      </Box>
    </Box>
  );
}
