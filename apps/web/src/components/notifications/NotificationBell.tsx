import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  IconButton,
  Badge,
  Popover,
  Box,
  Typography,
  List,
  ListItemButton,
  ListItemText,
  Button,
  Divider,
  CircularProgress,
  Alert,
  Snackbar,
  Paper,
} from "@mui/material";
import {
  Notifications as NotificationsIcon,
  Circle as CircleIcon,
  Close as CloseIcon,
} from "@mui/icons-material";
import { useNotifications } from "../../hooks/useNotifications";
import { useNotificationStream } from "../../hooks/useNotificationStream";
import { formatRelativeTime } from "../../utils/date";
import type { Notification } from "../../types/notification";

export function NotificationBell() {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const open = Boolean(anchorEl);

  // Toast state for new notification alerts
  const [toastOpen, setToastOpen] = useState(false);
  const [toastNotification, setToastNotification] =
    useState<Notification | null>(null);

  // Error toast state
  const [errorToastOpen, setErrorToastOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const {
    notifications,
    unreadCount,
    loading,
    error,
    refetch,
    markAsRead,
    markAllAsRead,
    addNotification,
  } = useNotifications({ enableRealtime: true });

  // Subscribe to real-time notifications
  useNotificationStream({
    onNotification: useCallback(
      (notification: Notification) => {
        addNotification!(notification);
        // Show toast for new notification
        setToastNotification(notification);
        setToastOpen(true);
      },
      [addNotification]
    ),
    // Refetch on reconnect to sync any missed notifications
    onReconnect: refetch,
    enabled: true,
  });

  const handleToastClose = () => {
    setToastOpen(false);
  };

  const handleOpen = async (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
    refetch();

    // Automatically mark all as read when opening the popover
    if (unreadCount > 0) {
      try {
        await markAllAsRead();
      } catch {
        setErrorMessage("Failed to mark notifications as read");
        setErrorToastOpen(true);
      }
    }
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationClick = async (notification: Notification) => {
    // Mark as read if not already (handles notifications that arrived while popover is open)
    if (!notification.is_read) {
      try {
        await markAsRead(notification.id);
      } catch {
        setErrorMessage("Failed to mark notification as read");
        setErrorToastOpen(true);
      }
    }
    handleClose();
    // TODO: Navigate to the relevant campaign/comment when we have routing
  };

  const handleErrorToastClose = () => {
    setErrorToastOpen(false);
  };

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleOpen}
        aria-label={`${unreadCount} unread notifications`}
        aria-haspopup="true"
        aria-expanded={open}
      >
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        slotProps={{
          paper: {
            sx: { width: 360, maxHeight: 400 },
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" component="h2">
            Notifications
          </Typography>
        </Box>

        <Divider />

        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            Failed to load notifications
          </Alert>
        )}

        {!loading && !error && notifications.length === 0 && (
          <Box sx={{ p: 3, textAlign: "center" }}>
            <Typography color="text.secondary">No notifications</Typography>
          </Box>
        )}

        {!loading && !error && notifications.length > 0 && (
          <List disablePadding>
            {notifications.map((notification) => (
              <ListItemButton
                key={notification.id}
                onClick={() => handleNotificationClick(notification)}
                sx={{
                  bgcolor: notification.is_read
                    ? "transparent"
                    : "action.hover",
                }}
              >
                <ListItemText
                  primary={
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
                    >
                      {!notification.is_read && (
                        <CircleIcon
                          sx={{
                            fontSize: 8,
                            color: "primary.main",
                            flexShrink: 0,
                          }}
                        />
                      )}
                      <Typography
                        variant="body2"
                        component="span"
                        sx={{
                          fontWeight: notification.is_read ? "normal" : "bold",
                        }}
                      >
                        {notification.message}
                      </Typography>
                    </Box>
                  }
                  secondary={formatRelativeTime(notification.created_at)}
                />
              </ListItemButton>
            ))}
          </List>
        )}

        <Divider />
        <Box sx={{ p: 1, textAlign: "center" }}>
          <Button
            size="small"
            onClick={() => {
              handleClose();
              navigate("/notifications");
            }}
          >
            View All
          </Button>
        </Box>
      </Popover>

      {/* Toast notification for new messages */}
      <Snackbar
        open={toastOpen}
        autoHideDuration={5000}
        onClose={handleToastClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Paper
          elevation={6}
          sx={{
            p: 2,
            minWidth: 300,
            maxWidth: 400,
            display: "flex",
            alignItems: "flex-start",
            gap: 1,
          }}
        >
          <NotificationsIcon color="primary" sx={{ mt: 0.5 }} />
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle2" fontWeight="bold">
              New Notification
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {toastNotification?.message}
            </Typography>
          </Box>
          <IconButton size="small" onClick={handleToastClose}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Paper>
      </Snackbar>

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
