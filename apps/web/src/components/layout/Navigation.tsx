import { NavLink } from "react-router-dom";
import { Button, Box } from "@mui/material";

export function Navigation() {
  return (
    <Box sx={{ display: "flex", gap: 2 }}>
      <Button
        component={NavLink}
        to="/campaigns"
        color="inherit"
        sx={{
          "&:hover": {
            backgroundColor: "rgba(255, 255, 255, 0.2)",
          },
          "&.active": {
            borderBottom: "2px solid white",
            borderRadius: 0,
          },
        }}
      >
        Campaigns
      </Button>
      <Button
        component={NavLink}
        to="/invoices"
        color="inherit"
        sx={{
          "&:hover": {
            backgroundColor: "rgba(255, 255, 255, 0.2)",
          },
          "&.active": {
            borderBottom: "2px solid white",
            borderRadius: 0,
          },
        }}
      >
        Invoices
      </Button>
    </Box>
  );
}
