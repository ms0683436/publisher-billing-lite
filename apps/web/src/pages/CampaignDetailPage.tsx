import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
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
  Chip,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useCampaign } from "../hooks/useCampaign";
import { MoneyDisplay } from "../components/common/MoneyDisplay";
import { CommentSection } from "../components/comments";

export function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { campaign, loading, error } = useCampaign(Number(id));

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

  if (!campaign) {
    return <Alert severity="warning">Campaign not found</Alert>;
  }

  return (
    <>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate("/campaigns")}
        >
          Back to Campaigns
        </Button>
      </Box>

      <Typography variant="h4" gutterBottom>
        {campaign.name}
      </Typography>

      {campaign.invoice_summary && (
        <Box sx={{ mb: 4 }}>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Actual
                  </Typography>
                  <Typography variant="h5">
                    <MoneyDisplay value={campaign.invoice_summary.total_actual} />
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Adjustments
                  </Typography>
                  <Typography variant="h5">
                    <MoneyDisplay
                      value={campaign.invoice_summary.total_adjustments}
                    />
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Total Billable
                  </Typography>
                  <Typography variant="h5" color="primary">
                    <MoneyDisplay
                      value={campaign.invoice_summary.total_billable}
                    />
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, md: 3 }}>
              <Card>
                <CardContent>
                  <Typography color="text.secondary" gutterBottom>
                    Invoice
                  </Typography>
                  <Chip
                    label={`#${campaign.invoice_summary.id}`}
                    color="primary"
                    onClick={() =>
                      navigate(`/invoices/${campaign.invoice_summary!.id}`)
                    }
                    sx={{ cursor: "pointer" }}
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      <Accordion defaultExpanded disableGutters slotProps={{ transition: { timeout: 0 } }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            Line Items ({campaign.line_items.length})
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ p: 0 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell align="right">Booked Amount</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {campaign.line_items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.name}</TableCell>
                    <TableCell align="right">
                      <MoneyDisplay value={item.booked_amount} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      <Divider sx={{ my: 4 }} />

      <CommentSection campaignId={Number(id)} />
    </>
  );
}
