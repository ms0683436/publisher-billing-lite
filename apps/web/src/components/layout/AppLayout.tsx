import { useState } from "react";
import { Outlet } from "react-router-dom";
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Menu,
  MenuItem,
  Divider,
  CircularProgress,
} from "@mui/material";
import {
  Logout as LogoutIcon,
  KeyboardArrowDown as ArrowDownIcon,
} from "@mui/icons-material";
import { Navigation } from "./Navigation";
import { NotificationBell } from "../notifications/NotificationBell";
import { useAuth } from "../../hooks/useAuth";

export function AppLayout() {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const open = Boolean(anchorEl);

  const menuButtonId = "account-menu-button";
  const menuId = "account-menu";

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleClose();
    setIsLoggingOut(true);
    try {
      await logout();
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ mr: 4 }}>
            Publisher Billing
          </Typography>
          <Navigation />
          <Box sx={{ flexGrow: 1 }} />
          {user && (
            <>
              <NotificationBell />
              <Button
                color="inherit"
                onClick={handleClick}
                endIcon={<ArrowDownIcon />}
                id={menuButtonId}
                aria-controls={open ? menuId : undefined}
                aria-haspopup="true"
                aria-expanded={open ? "true" : undefined}
                disabled={isLoggingOut}
              >
                {user.username}
              </Button>
              <Menu
                id={menuId}
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                MenuListProps={{
                  "aria-labelledby": menuButtonId,
                }}
                anchorOrigin={{
                  vertical: "bottom",
                  horizontal: "right",
                }}
                transformOrigin={{
                  vertical: "top",
                  horizontal: "right",
                }}
              >
                <MenuItem disabled sx={{ opacity: 1 }}>
                  <Typography variant="body2">{user.email}</Typography>
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout} disabled={isLoggingOut}>
                  {isLoggingOut ? (
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                  ) : (
                    <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
                  )}
                  Logout
                </MenuItem>
              </Menu>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ mt: 4, mb: 4, mx: 4, flex: 1 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
