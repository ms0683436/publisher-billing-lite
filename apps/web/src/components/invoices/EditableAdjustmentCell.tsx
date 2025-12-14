import { useState, useCallback } from "react";
import {
  Box,
  TextField,
  IconButton,
  CircularProgress,
  Tooltip,
  Snackbar,
  Alert,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import { useUpdateAdjustment } from "../../hooks/useUpdateAdjustment";
import { MoneyDisplay } from "../common/MoneyDisplay";

interface EditableAdjustmentCellProps {
  invoiceLineItemId: number;
  currentValue: string;
  onSaved: () => void;
}

export function EditableAdjustmentCell({
  invoiceLineItemId,
  currentValue,
  onSaved,
}: EditableAdjustmentCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(currentValue);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>("");

  const { updateAdjustment, loading, error } = useUpdateAdjustment();

  const normalizeTo2dp = useCallback((value: string): string => {
    const trimmed = value.trim();
    if (trimmed === "" || trimmed === "-" || trimmed === "." || trimmed === "-.") {
      return "0.00";
    }

    let sign = "";
    let rest = trimmed;
    if (rest.startsWith("-")) {
      sign = "-";
      rest = rest.slice(1);
    }

    const [rawInt = "", rawFrac = ""] = rest.split(".");
    const intDigits = rawInt.replace(/\D/g, "");
    const fracDigits = rawFrac.replace(/\D/g, "");

    const intPart = (intDigits.replace(/^0+(?=\d)/, "") || "0");
    const fracPart = (fracDigits.slice(0, 2) + "00").slice(0, 2);

    return `${sign}${intPart}.${fracPart}`;
  }, []);

  const openErrorSnackbar = useCallback((message?: string) => {
    setSnackbarMessage(message || "Update failed");
    setSnackbarOpen(true);
  }, []);

  const handleStartEdit = useCallback(() => {
    setEditValue(currentValue);
    setValidationError(null);
    setIsEditing(true);
  }, [currentValue]);

  const handleCancel = useCallback(() => {
    setEditValue(currentValue);
    setValidationError(null);
    setIsEditing(false);
  }, [currentValue]);

  const validateDecimal = (value: string): boolean => {
    const regex = /^-?\d*\.?\d{0,2}$/;
    return regex.test(value) || value === "" || value === "-";
  };

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setEditValue(newValue);

      if (newValue && !validateDecimal(newValue)) {
        setValidationError("Enter a valid decimal (e.g., -10.50)");
      } else {
        setValidationError(null);
      }
    },
    []
  );

  const handleSave = useCallback(async () => {
    if (validationError) return;

    const valueToSave = normalizeTo2dp(editValue);

    const result = await updateAdjustment(invoiceLineItemId, valueToSave);
    if (result) {
      setIsEditing(false);
      onSaved();
    } else {
      openErrorSnackbar(error?.message);
    }
  }, [
    editValue,
    validationError,
    invoiceLineItemId,
    normalizeTo2dp,
    updateAdjustment,
    onSaved,
    openErrorSnackbar,
    error?.message,
  ]);

  const handleBlur = useCallback(() => {
    if (validationError) return;
    setEditValue((prev) => normalizeTo2dp(prev));
  }, [normalizeTo2dp, validationError]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !validationError) {
        handleSave();
      } else if (e.key === "Escape") {
        handleCancel();
      }
    },
    [handleSave, handleCancel, validationError]
  );

  if (isEditing) {
    return (
      <>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 1 }}>
          <TextField
            value={editValue}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            size="small"
            autoFocus
            error={!!validationError}
            helperText={validationError}
            disabled={loading}
            sx={{
              width: 140,
              "& .MuiInputBase-input": {
                textAlign: "right",
              },
            }}
            slotProps={{
              htmlInput: {
                inputMode: "decimal",
                pattern: "-?\\d*(\\.\\d{0,2})?",
              },
            }}
          />
          {loading ? (
            <CircularProgress size={20} />
          ) : (
            <>
              <Tooltip title="Save (Enter)">
                <IconButton
                  size="small"
                  color="primary"
                  onClick={handleSave}
                  disabled={!!validationError}
                >
                  <CheckIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Cancel (Esc)">
                <IconButton size="small" onClick={handleCancel}>
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}
        </Box>
        <Snackbar
          open={snackbarOpen}
          autoHideDuration={4000}
          onClose={() => setSnackbarOpen(false)}
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
        >
          <Alert
            onClose={() => setSnackbarOpen(false)}
            severity="error"
            variant="filled"
          >
            {snackbarMessage}
          </Alert>
        </Snackbar>
      </>
    );
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-end",
          gap: 1,
        }}
      >
        <MoneyDisplay value={currentValue} />
        <Tooltip title="Edit adjustment">
          <IconButton size="small" onClick={handleStartEdit}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={() => setSnackbarOpen(false)}
          severity="error"
          variant="filled"
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
}
