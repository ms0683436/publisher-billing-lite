import { useState, useCallback, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Grid,
  TextField,
  Snackbar,
  IconButton,
  Tooltip,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import EditIcon from "@mui/icons-material/Edit";
import SaveIcon from "@mui/icons-material/Save";
import CancelIcon from "@mui/icons-material/Cancel";
import HistoryIcon from "@mui/icons-material/History";
import { useInvoice } from "../hooks/useInvoice";
import { useBatchUpdateAdjustments } from "../hooks/useBatchUpdateAdjustments";
import { MoneyDisplay } from "../components/common/MoneyDisplay";
import { HistoryDialog } from "../components/history/HistoryDialog";

function normalizeTo2dp(value: string): string {
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

  const intPart = intDigits.replace(/^0+(?=\d)/, "") || "0";
  const fracPart = (fracDigits.slice(0, 2) + "00").slice(0, 2);

  return `${sign}${intPart}.${fracPart}`;
}

function validateDecimal(value: string): boolean {
  const regex = /^-?\d*\.?\d{0,2}$/;
  return regex.test(value) || value === "" || value === "-";
}

export function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { invoice, loading, error, refetch } = useInvoice(Number(id));
  const {
    updateAdjustments,
    loading: saving,
    error: saveError,
  } = useBatchUpdateAdjustments();

  const [isEditMode, setIsEditMode] = useState(false);
  const [editedValues, setEditedValues] = useState<Map<number, string>>(
    new Map()
  );
  const [fieldErrors, setFieldErrors] = useState<Map<number, string>>(
    new Map()
  );
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [historyDialogItem, setHistoryDialogItem] = useState<{
    id: number;
    name: string;
  } | null>(null);

  const handleEnterEditMode = useCallback(() => {
    if (!invoice) return;
    const initial = new Map<number, string>();
    invoice.line_items.forEach((item) => {
      initial.set(item.invoice_line_item_id, item.adjustments);
    });
    setEditedValues(initial);
    setFieldErrors(new Map());
    setIsEditMode(true);
  }, [invoice]);

  const handleCancelEdit = useCallback(() => {
    setIsEditMode(false);
    setEditedValues(new Map());
    setFieldErrors(new Map());
  }, []);

  const handleFieldChange = useCallback(
    (invoiceLineItemId: number, value: string) => {
      setEditedValues((prev) => new Map(prev).set(invoiceLineItemId, value));

      if (value && !validateDecimal(value)) {
        setFieldErrors((prev) =>
          new Map(prev).set(
            invoiceLineItemId,
            "Enter a valid decimal (e.g., -10.50)"
          )
        );
      } else {
        setFieldErrors((prev) => {
          const next = new Map(prev);
          next.delete(invoiceLineItemId);
          return next;
        });
      }
    },
    []
  );

  const handleFieldBlur = useCallback((invoiceLineItemId: number) => {
    setEditedValues((prev) => {
      const current = prev.get(invoiceLineItemId);
      if (current === undefined) return prev;
      return new Map(prev).set(invoiceLineItemId, normalizeTo2dp(current));
    });
  }, []);

  const handleSaveAll = useCallback(async () => {
    if (!invoice || fieldErrors.size > 0) return;

    // Only send changed adjustments
    const updates = invoice.line_items
      .filter((item) => {
        const edited = editedValues.get(item.invoice_line_item_id);
        return (
          edited !== undefined && normalizeTo2dp(edited) !== item.adjustments
        );
      })
      .map((item) => ({
        invoice_line_item_id: item.invoice_line_item_id,
        adjustments: normalizeTo2dp(editedValues.get(item.invoice_line_item_id)!),
      }));

    if (updates.length === 0) return;

    const result = await updateAdjustments(invoice.id, { updates });
    if (result) {
      setIsEditMode(false);
      setEditedValues(new Map());
      refetch();
    } else {
      setSnackbarMessage(saveError?.message || "Update failed");
      setSnackbarOpen(true);
    }
  }, [invoice, editedValues, fieldErrors, updateAdjustments, refetch, saveError]);

  const hasChanges = useMemo(() => {
    if (!invoice) return false;
    return invoice.line_items.some((item) => {
      const edited = editedValues.get(item.invoice_line_item_id);
      return (
        edited !== undefined && normalizeTo2dp(edited) !== item.adjustments
      );
    });
  }, [invoice, editedValues]);

  const hasErrors = fieldErrors.size > 0;

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

  if (!invoice) {
    return <Alert severity="warning">Invoice not found</Alert>;
  }

  return (
    <>
      <Box sx={{ mb: 3, display: "flex", justifyContent: "space-between" }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/invoices")}
        >
          Back to Invoices
        </Button>

        {!isEditMode ? (
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={handleEnterEditMode}
          >
            Edit Adjustments
          </Button>
        ) : (
          <Box sx={{ display: "flex", gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={handleCancelEdit}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
              onClick={handleSaveAll}
              disabled={saving || hasErrors || !hasChanges}
            >
              Save All
            </Button>
          </Box>
        )}
      </Box>

      <Typography variant="h4" gutterBottom>
        Invoice #{invoice.id}
      </Typography>

      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Campaign: {invoice.campaign_name}
      </Typography>

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Actual
              </Typography>
              <Typography variant="h5">
                <MoneyDisplay value={invoice.total_actual} />
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Adjustments
              </Typography>
              <Typography variant="h5">
                <MoneyDisplay value={invoice.total_adjustments} />
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Billable
              </Typography>
              <Typography variant="h5" color="primary">
                <MoneyDisplay value={invoice.total_billable} />
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" gutterBottom>
        Line Items
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Booked</TableCell>
              <TableCell align="right">Actual</TableCell>
              <TableCell align="right">Adjustments</TableCell>
              <TableCell align="right">Billable</TableCell>
              <TableCell align="center" sx={{ width: 60 }}></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoice.line_items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.name}</TableCell>
                <TableCell align="right">
                  <MoneyDisplay value={item.booked_amount} />
                </TableCell>
                <TableCell align="right">
                  <MoneyDisplay value={item.actual_amount} />
                </TableCell>
                <TableCell align="right">
                  {isEditMode ? (
                    <TextField
                      value={
                        editedValues.get(item.invoice_line_item_id) ??
                        item.adjustments
                      }
                      onChange={(e) =>
                        handleFieldChange(
                          item.invoice_line_item_id,
                          e.target.value
                        )
                      }
                      onBlur={() => handleFieldBlur(item.invoice_line_item_id)}
                      size="small"
                      error={fieldErrors.has(item.invoice_line_item_id)}
                      helperText={fieldErrors.get(item.invoice_line_item_id)}
                      disabled={saving}
                      sx={{
                        width: 120,
                        "& .MuiInputBase-input": {
                          textAlign: "right",
                        },
                      }}
                      slotProps={{
                        htmlInput: {
                          inputMode: "decimal",
                        },
                      }}
                    />
                  ) : (
                    <MoneyDisplay value={item.adjustments} />
                  )}
                </TableCell>
                <TableCell align="right">
                  <MoneyDisplay value={item.billable_amount} />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="View history">
                    <IconButton
                      size="small"
                      onClick={() =>
                        setHistoryDialogItem({
                          id: item.invoice_line_item_id,
                          name: item.name,
                        })
                      }
                    >
                      <HistoryIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {historyDialogItem && (
        <HistoryDialog
          open={true}
          onClose={() => setHistoryDialogItem(null)}
          entityType="invoice_line_item"
          entityId={historyDialogItem.id}
          title={`History: ${historyDialogItem.name}`}
          fieldLabels={{ adjustments: "Adjustments" }}
        />
      )}

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
