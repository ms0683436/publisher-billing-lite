import { useMemo } from "react";
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
  TableSortLabel,
  CircularProgress,
  Alert,
  Box,
  TextField,
  InputAdornment,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useInvoices } from "../hooks/useInvoices";
import { useDebounce } from "../hooks/useDebounce";
import { useTableParams } from "../hooks/useTableParams";
import { MoneyDisplay } from "../components/common/MoneyDisplay";
import type { InvoiceSortField } from "../types/common";

interface SortableColumn {
  id: InvoiceSortField;
  label: string;
  align?: "left" | "right" | "center";
  sortable: boolean;
}

const columns: SortableColumn[] = [
  { id: "id", label: "Invoice #", align: "left", sortable: true },
  { id: "campaign_name", label: "Campaign", align: "left", sortable: true },
  {
    id: "total_billable",
    label: "Total Billable",
    align: "right",
    sortable: true,
  },
  {
    id: "line_items_count",
    label: "Line Items",
    align: "center",
    sortable: true,
  },
];

const validSortFields: readonly InvoiceSortField[] = [
  "id",
  "campaign_name",
  "total_billable",
  "line_items_count",
];

export function InvoicesPage() {
  const {
    page,
    rowsPerPage,
    setPage,
    setRowsPerPage,
    searchInput,
    setSearchInput,
    sortBy,
    sortDir,
    handleSort,
    params,
  } = useTableParams<InvoiceSortField>({ validSortFields });

  // Debounce search for API calls
  const debouncedSearch = useDebounce(searchInput, 300);

  const apiParams = useMemo(
    () => ({
      ...params,
      search: debouncedSearch || undefined,
    }),
    [params, debouncedSearch]
  );

  const { invoices, total, loading, error } = useInvoices(apiParams);

  const navigate = useNavigate();

  if (error) {
    return <Alert severity="error">{error.message}</Alert>;
  }

  return (
    <>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h4">Invoices</Typography>
        <TextField
          size="small"
          placeholder="Search by campaign..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            },
          }}
          sx={{ width: 300 }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column.id} align={column.align}>
                  {column.sortable ? (
                    <TableSortLabel
                      active={sortBy === column.id}
                      direction={sortBy === column.id ? sortDir : "asc"}
                      onClick={() => handleSort(column.id)}
                    >
                      {column.label}
                    </TableSortLabel>
                  ) : (
                    column.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : invoices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 4 }}>
                  No invoices found
                </TableCell>
              </TableRow>
            ) : (
              invoices.map((invoice) => (
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
                  <TableCell align="center">
                    {invoice.line_items_count}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) =>
            setRowsPerPage(parseInt(e.target.value, 10))
          }
        />
      </TableContainer>
    </>
  );
}
