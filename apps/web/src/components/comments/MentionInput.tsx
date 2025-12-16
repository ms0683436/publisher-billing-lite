import { useState, useRef, useEffect, useCallback } from "react";
import {
  TextField,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  Popper,
  CircularProgress,
  Box,
  Typography,
} from "@mui/material";
import { useUserSearch } from "../../hooks/useUserSearch";

interface MentionInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  minRows?: number;
  maxRows?: number;
  disabled?: boolean;
  autoFocus?: boolean;
}

export function MentionInput({
  value,
  onChange,
  placeholder = "Write a comment... Use @username to mention someone",
  minRows = 2,
  maxRows = 6,
  disabled = false,
  autoFocus = false,
}: MentionInputProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [mentionQuery, setMentionQuery] = useState("");
  const [mentionStart, setMentionStart] = useState(-1);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { results, loading, search, clear } = useUserSearch();

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;
      const cursorPos = e.target.selectionStart ?? 0;
      onChange(newValue);

      // Check for @ mention trigger
      const textBeforeCursor = newValue.slice(0, cursorPos);
      const lastAtIndex = textBeforeCursor.lastIndexOf("@");

      if (lastAtIndex !== -1) {
        const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
        // Check if there's a space or newline between @ and cursor
        if (!/\s/.test(textAfterAt) && textAfterAt.length <= 50) {
          setMentionStart(lastAtIndex);
          setMentionQuery(textAfterAt);
          setAnchorEl(e.target);
          setSelectedIndex(0); // Reset selection when starting new search
          search(textAfterAt);
          return;
        }
      }

      // Close mention popup
      setMentionStart(-1);
      setMentionQuery("");
      setAnchorEl(null);
      clear();
    },
    [onChange, search, clear]
  );

  const handleSelectUser = useCallback(
    (username: string) => {
      if (mentionStart === -1) return;

      const before = value.slice(0, mentionStart);
      const after = value.slice(mentionStart + 1 + mentionQuery.length);
      const newValue = `${before}@${username} ${after}`;
      onChange(newValue);

      // Close popup
      setMentionStart(-1);
      setMentionQuery("");
      setAnchorEl(null);
      clear();

      // Focus back to input
      inputRef.current?.focus();
    },
    [value, mentionStart, mentionQuery, onChange, clear]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!anchorEl || results.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < results.length - 1 ? prev + 1 : 0
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : results.length - 1
          );
          break;
        case "Tab":
        case "Enter":
          if (results[selectedIndex]) {
            e.preventDefault();
            handleSelectUser(results[selectedIndex].username);
          }
          break;
        case "Escape":
          e.preventDefault();
          setAnchorEl(null);
          clear();
          break;
      }
    },
    [anchorEl, results, selectedIndex, handleSelectUser, clear]
  );

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (anchorEl) {
        setAnchorEl(null);
        clear();
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [anchorEl, clear]);

  const open = Boolean(anchorEl) && (results.length > 0 || loading);

  return (
    <Box sx={{ position: "relative" }}>
      <TextField
        inputRef={inputRef}
        fullWidth
        multiline
        minRows={minRows}
        maxRows={maxRows}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        autoFocus={autoFocus}
        variant="outlined"
        size="small"
      />
      <Popper
        open={open}
        anchorEl={anchorEl}
        placement="bottom-start"
        style={{ zIndex: 1300 }}
      >
        <Paper
          elevation={8}
          sx={{
            minWidth: 220,
            maxWidth: 300,
            maxHeight: 240,
            overflow: "auto",
            mt: 1,
            borderRadius: 2,
          }}
        >
          {loading ? (
            <Box sx={{ p: 2, display: "flex", justifyContent: "center" }}>
              <CircularProgress size={20} />
            </Box>
          ) : (
            <List sx={{ py: 0.5 }}>
              {results.map((user, index) => (
                <ListItemButton
                  key={user.id}
                  selected={index === selectedIndex}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSelectUser(user.username);
                  }}
                  sx={{
                    py: 0.75,
                    px: 2,
                    "&.Mui-selected": {
                      bgcolor: "primary.main",
                      color: "primary.contrastText",
                      "&:hover": {
                        bgcolor: "primary.dark",
                      },
                    },
                  }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="body2" fontWeight={500}>
                        @{user.username}
                      </Typography>
                    }
                  />
                </ListItemButton>
              ))}
            </List>
          )}
        </Paper>
      </Popper>
    </Box>
  );
}
