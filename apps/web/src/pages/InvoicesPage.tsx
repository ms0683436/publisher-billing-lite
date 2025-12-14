import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
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
} from "@mui/material";
import { useInvoices } from "../hooks/useInvoices";
import { MoneyDisplay } from "../components/common/MoneyDisplay";

export function InvoicesPage() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const pagination = useMemo(
    () => ({
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    }),
    [page, rowsPerPage]
  );

  const { invoices, total, loading, error } = useInvoices(pagination);

  const navigate = useNavigate();

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
      <Typography variant="h4" gutterBottom>
        Invoices
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Invoice #</TableCell>
              <TableCell>Campaign</TableCell>
              <TableCell align="right">Total Billable</TableCell>
              <TableCell align="center">Line Items</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {invoices.map((invoice) => (
              <TableRow
                key={invoice.id}
                hover
                onClick={() => navigate(`/invoices/${invoice.id}`)}
                sx={{ cursor: "pointer" }}
              >
                <TableCell>#{invoice.id}</TableCell>
                <TableCell>{invoice.campaign_name}</TableCell>
                <TableCell align="right">
                  <MoneyDisplay value={invoice.total_billable} />
                </TableCell>
                <TableCell align="center">{invoice.line_items_count}</TableCell>
              </TableRow>
            ))}
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
    </>
  );
}
