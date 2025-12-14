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
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useInvoice } from "../hooks/useInvoice";
import { MoneyDisplay } from "../components/common/MoneyDisplay";
import { EditableAdjustmentCell } from "../components/invoices/EditableAdjustmentCell";

export function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { invoice, loading, error, refetch } = useInvoice(Number(id));

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
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/invoices")}
        >
          Back to Invoices
        </Button>
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
                  <EditableAdjustmentCell
                    invoiceLineItemId={item.invoice_line_item_id}
                    currentValue={item.adjustments}
                    onSaved={refetch}
                  />
                </TableCell>
                <TableCell align="right">
                  <MoneyDisplay value={item.billable_amount} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
