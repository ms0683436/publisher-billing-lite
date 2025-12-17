import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Tooltip,
} from "@mui/material";
import { History as HistoryIcon } from "@mui/icons-material";
import type { ChangeHistory } from "../../types/history";
import { formatRelativeTime, formatFullDate } from "../../utils/date";

interface HistoryTimelineProps {
  history: ChangeHistory[];
  loading: boolean;
  error: Error | null;
  fieldLabels?: Record<string, string>;
  formatValue?: (field: string, value: unknown) => string;
}

function defaultFormatValue(_field: string, value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  return String(value);
}

export function HistoryTimeline({
  history,
  loading,
  error,
  fieldLabels = {},
  formatValue = defaultFormatValue,
}: HistoryTimelineProps) {
  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 1 }}>
        {error.message}
      </Alert>
    );
  }

  if (history.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: "center" }}>
        <Typography color="text.secondary">No change history</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 1 }}>
      {history.map((entry, index) => (
        <Box
          key={entry.id}
          sx={{
            display: "flex",
            gap: 2,
            pb: 2,
            mb: 2,
            borderBottom: index < history.length - 1 ? 1 : 0,
            borderColor: "divider",
          }}
        >
          {/* Timeline dot */}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              pt: 0.5,
            }}
          >
            <HistoryIcon fontSize="small" color="action" />
          </Box>

          {/* Content */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            {/* Header: user and time */}
            <Box
              sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}
            >
              <Typography variant="subtitle2" fontWeight={600}>
                @{entry.changed_by_username}
              </Typography>
              <Tooltip title={formatFullDate(entry.created_at)} arrow>
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ cursor: "default" }}
                >
                  {formatRelativeTime(entry.created_at)}
                </Typography>
              </Tooltip>
            </Box>

            {/* Changes */}
            <Box sx={{ mt: 1 }}>
              {Object.keys(entry.new_value).map((field) => {
                const oldVal = entry.old_value?.[field];
                const newVal = entry.new_value[field];
                const label = fieldLabels[field] || field;

                return (
                  <Box key={field} sx={{ mb: 0.5 }}>
                    <Typography variant="body2" component="span">
                      <Typography
                        component="span"
                        variant="body2"
                        color="text.secondary"
                      >
                        {label}:
                      </Typography>{" "}
                      <Typography
                        component="span"
                        variant="body2"
                        sx={{
                          textDecoration: "line-through",
                          color: "text.secondary",
                        }}
                      >
                        {formatValue(field, oldVal)}
                      </Typography>
                      {" → "}
                      <Typography
                        component="span"
                        variant="body2"
                        fontWeight={500}
                      >
                        {formatValue(field, newVal)}
                      </Typography>
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </Box>
        </Box>
      ))}
    </Box>
  );
}
