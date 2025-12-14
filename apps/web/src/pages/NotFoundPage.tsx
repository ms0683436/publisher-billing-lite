import { useNavigate } from "react-router-dom";
import { Typography, Button, Box } from "@mui/material";

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "50vh",
      }}
    >
      <Typography variant="h1" gutterBottom>
        404
      </Typography>
      <Typography variant="h5" color="text.secondary" gutterBottom>
        Page not found
      </Typography>
      <Button variant="contained" onClick={() => navigate("/campaigns")}>
        Go to Campaigns
      </Button>
    </Box>
  );
}
