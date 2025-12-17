import {
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Box,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { HistoryTimeline } from "./HistoryTimeline";
import { useChangeHistory } from "../../hooks/useChangeHistory";
import type { EntityType } from "../../types/history";

interface HistoryDialogProps {
  open: boolean;
  onClose: () => void;
  entityType: EntityType;
  entityId: number;
  title?: string;
  fieldLabels?: Record<string, string>;
  formatValue?: (field: string, value: unknown) => string;
}

export function HistoryDialog({
  open,
  onClose,
  entityType,
  entityId,
  title = "Change History",
  fieldLabels,
  formatValue,
}: HistoryDialogProps) {
  const { history, total, loading, error } = useChangeHistory(
    entityType,
    entityId
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography variant="h6">{title}</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        {!loading && total > 0 && (
          <Typography variant="caption" color="text.secondary">
            {total} {total === 1 ? "change" : "changes"}
          </Typography>
        )}
      </DialogTitle>
      <DialogContent dividers>
        <HistoryTimeline
          history={history}
          loading={loading}
          error={error}
          fieldLabels={fieldLabels}
          formatValue={formatValue}
        />
      </DialogContent>
    </Dialog>
  );
}
