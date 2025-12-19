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
  Chip,
  Box,
  TextField,
  InputAdornment,
} from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";
import { useCampaigns } from "../hooks/useCampaigns";
import { useDebounce } from "../hooks/useDebounce";
import { useTableParams } from "../hooks/useTableParams";
import { MoneyDisplay } from "../components/common/MoneyDisplay";
import type { CampaignSortField } from "../types/common";

interface SortableColumn {
  id: CampaignSortField;
  label: string;
  align?: "left" | "right" | "center";
  sortable: boolean;
}

const columns: SortableColumn[] = [
  { id: "id", label: "ID", align: "left", sortable: true },
  { id: "name", label: "Name", align: "left", sortable: true },
  { id: "total_booked", label: "Total Booked", align: "right", sortable: true },
  { id: "total_actual", label: "Total Actual", align: "right", sortable: true },
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

const validSortFields: readonly CampaignSortField[] = [
  "id",
  "name",
  "total_booked",
  "total_actual",
  "total_billable",
  "line_items_count",
];

export function CampaignsPage() {
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
  } = useTableParams<CampaignSortField>({ validSortFields });

  // Debounce search for API calls
  const debouncedSearch = useDebounce(searchInput, 300);

  const apiParams = useMemo(
    () => ({
      ...params,
      search: debouncedSearch || undefined,
    }),
    [params, debouncedSearch]
  );

  const { campaigns, total, loading, error } = useCampaigns(apiParams);

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
        <Typography variant="h4">Campaigns</Typography>
        <TextField
          size="small"
          placeholder="Search campaigns..."
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
              <TableCell align="center">Invoice</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : campaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                  No campaigns found
                </TableCell>
              </TableRow>
            ) : (
              campaigns.map((campaign) => (
                <TableRow
                  key={campaign.id}
                  hover
                  onClick={() => navigate(`/campaigns/${campaign.id}`)}
                  sx={{ cursor: "pointer" }}
                >
                  <TableCell>{campaign.id}</TableCell>
                  <TableCell>{campaign.name}</TableCell>
                  <TableCell align="right">
                    <MoneyDisplay value={campaign.total_booked} />
                  </TableCell>
                  <TableCell align="right">
                    <MoneyDisplay value={campaign.total_actual} />
                  </TableCell>
                  <TableCell align="right">
                    <MoneyDisplay value={campaign.total_billable} />
                  </TableCell>
                  <TableCell align="center">
                    {campaign.line_items_count}
                  </TableCell>
                  <TableCell align="center">
                    {campaign.invoice_id ? (
                      <Chip
                        label={`#${campaign.invoice_id}`}
                        size="small"
                        color="primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/invoices/${campaign.invoice_id}`);
                        }}
                      />
                    ) : (
                      <Chip label="None" size="small" variant="outlined" />
                    )}
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
