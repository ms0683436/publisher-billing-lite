import { useState, useMemo } from "react";
import {
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  CircularProgress,
  Alert,
  Box,
  Button,
  IconButton,
  Tooltip,
  Snackbar,
} from "@mui/material";
import {
  Circle as CircleIcon,
  DoneAll as DoneAllIcon,
} from "@mui/icons-material";
import { useNotifications } from "../hooks/useNotifications";
import { formatRelativeTime } from "../utils/date";

export function NotificationsPage() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Loading state for async operations
  const [actionLoading, setActionLoading] = useState<number | "all" | null>(
    null
  );

  // Error toast state
  const [errorToastOpen, setErrorToastOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const pagination = useMemo(
    () => ({
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    }),
    [page, rowsPerPage]
  );

  const { notifications, total, unreadCount, loading, error, markAsRead, markAllAsRead } =
    useNotifications({ pagination });

  const handleMarkAsRead = async (id: number) => {
    setActionLoading(id);
    try {
      await markAsRead(id);
    } catch {
      setErrorMessage("Failed to mark notification as read");
      setErrorToastOpen(true);
    } finally {
      setActionLoading(null);
    }
  };

  const handleMarkAllAsRead = async () => {
    setActionLoading("all");
    try {
      await markAllAsRead();
    } catch {
      setErrorMessage("Failed to mark all as read");
      setErrorToastOpen(true);
    } finally {
      setActionLoading(null);
    }
  };

  const handleErrorToastClose = () => {
    setErrorToastOpen(false);
  };

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h4">
          Notifications
          {unreadCount > 0 && (
            <Typography
              component="span"
              variant="body1"
              color="text.secondary"
              sx={{ ml: 2 }}
            >
              ({unreadCount} unread)
            </Typography>
          )}
        </Typography>
        {unreadCount > 0 && (
          <Button
            variant="outlined"
            startIcon={<DoneAllIcon />}
            onClick={handleMarkAllAsRead}
            disabled={actionLoading === "all"}
          >
            {actionLoading === "all" ? "Marking..." : "Mark all as read"}
          </Button>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={40}></TableCell>
              <TableCell>Message</TableCell>
              <TableCell>From</TableCell>
              <TableCell>Time</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {notifications.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="text.secondary" sx={{ py: 4 }}>
                    No notifications
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              notifications.map((notification) => (
                <TableRow
                  key={notification.id}
                  sx={{
                    bgcolor: notification.is_read
                      ? "transparent"
                      : "action.hover",
                  }}
                >
                  <TableCell>
                    {!notification.is_read && (
                      <CircleIcon
                        sx={{ fontSize: 10, color: "primary.main" }}
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography
                      sx={{
                        fontWeight: notification.is_read ? "normal" : "bold",
                      }}
                    >
                      {notification.message}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {notification.actor?.username || "-"}
                  </TableCell>
                  <TableCell>
                    {formatRelativeTime(notification.created_at)}
                  </TableCell>
                  <TableCell align="center">
                    {!notification.is_read && (
                      <Tooltip title="Mark as read">
                        <IconButton
                          size="small"
                          onClick={() => handleMarkAsRead(notification.id)}
                          disabled={actionLoading === notification.id}
                        >
                          {actionLoading === notification.id ? (
                            <CircularProgress size={18} />
                          ) : (
                            <DoneAllIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </TableContainer>

      {/* Error toast */}
      <Snackbar
        open={errorToastOpen}
        autoHideDuration={5000}
        onClose={handleErrorToastClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          severity="error"
          onClose={handleErrorToastClose}
          sx={{ width: "100%" }}
        >
          {errorMessage}
        </Alert>
      </Snackbar>
    </>
  );
}
