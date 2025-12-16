import { Outlet } from "react-router-dom";
import { Box, AppBar, Toolbar, Typography } from "@mui/material";
import { Navigation } from "./Navigation";
import { UserSelector } from "../common/UserSelector";

export function AppLayout() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ mr: 4 }}>
            Publisher Billing
          </Typography>
          <Navigation />
          <Box sx={{ flexGrow: 1 }} />
          <UserSelector />
        </Toolbar>
      </AppBar>
      <Box component="main" sx={{ mt: 4, mb: 4, mx: 4, flex: 1 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
