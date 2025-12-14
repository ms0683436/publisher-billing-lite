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
  Chip,
  Box,
} from "@mui/material";
import { useCampaigns } from "../hooks/useCampaigns";
import { MoneyDisplay } from "../components/common/MoneyDisplay";

export function CampaignsPage() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const pagination = useMemo(
    () => ({
      limit: rowsPerPage,
      offset: page * rowsPerPage,
    }),
    [page, rowsPerPage]
  );

  const { campaigns, total, loading, error } = useCampaigns(pagination);

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
        Campaigns
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell align="right">Total Booked</TableCell>
              <TableCell align="right">Total Actual</TableCell>
              <TableCell align="right">Total Billable</TableCell>
              <TableCell align="center">Line Items</TableCell>
              <TableCell align="center">Invoice</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {campaigns.map((campaign) => (
              <TableRow
                key={campaign.id}
                hover
                onClick={() => navigate(`/campaigns/${campaign.id}`)}
                sx={{ cursor: "pointer" }}
              >
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
                <TableCell align="center">{campaign.line_items_count}</TableCell>
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
