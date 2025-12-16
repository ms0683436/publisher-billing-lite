import {
  FormControl,
  Select,
  MenuItem,
  CircularProgress,
  Typography,
  Box,
} from "@mui/material";
import type { SelectChangeEvent } from "@mui/material";
import { useCurrentUser } from "../../hooks/useCurrentUser";

export function UserSelector() {
  const { currentUser, users, loading, error, selectUser } = useCurrentUser();

  const handleChange = (event: SelectChangeEvent<number>) => {
    selectUser(Number(event.target.value));
  };

  if (loading) {
    return <CircularProgress size={20} color="inherit" />;
  }

  if (error) {
    return (
      <Typography color="error" variant="body2">
        Failed to load users
      </Typography>
    );
  }

  if (users.length === 0) {
    return (
      <Typography variant="body2" color="inherit">
        No users available
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2" color="inherit">
        User:
      </Typography>
      <FormControl size="small" variant="outlined">
        <Select
          value={currentUser?.id ?? ""}
          onChange={handleChange}
          sx={{
            color: "inherit",
            ".MuiOutlinedInput-notchedOutline": {
              borderColor: "rgba(255, 255, 255, 0.5)",
            },
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "rgba(255, 255, 255, 0.8)",
            },
            "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
              borderColor: "white",
            },
            ".MuiSvgIcon-root": {
              color: "inherit",
            },
            minWidth: 120,
          }}
        >
          {users.map((user) => (
            <MenuItem key={user.id} value={user.id}>
              {user.username}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
}
