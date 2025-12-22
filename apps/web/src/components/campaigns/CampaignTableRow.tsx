import { memo, useCallback, type MouseEvent } from "react";
import { TableRow, TableCell, Chip } from "@mui/material";
import { MoneyDisplay } from "../common/MoneyDisplay";
import type { CampaignListItem } from "../../types/campaign";

interface CampaignTableRowProps {
  campaign: CampaignListItem;
  onRowClick: (id: number) => void;
  onInvoiceClick: (id: number) => void;
}

export const CampaignTableRow = memo(function CampaignTableRow({
  campaign,
  onRowClick,
  onInvoiceClick,
}: CampaignTableRowProps) {
  const handleRowClick = useCallback(() => {
    onRowClick(campaign.id);
  }, [campaign.id, onRowClick]);

  const handleInvoiceClick = useCallback(
    (e: MouseEvent) => {
      e.stopPropagation();
      if (campaign.invoice_id) {
        onInvoiceClick(campaign.invoice_id);
      }
    },
    [campaign.invoice_id, onInvoiceClick]
  );

  return (
    <TableRow hover onClick={handleRowClick} sx={{ cursor: "pointer" }}>
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
      <TableCell align="center">{campaign.line_items_count}</TableCell>
      <TableCell align="center">
        {campaign.invoice_id ? (
          <Chip
            label={`#${campaign.invoice_id}`}
            size="small"
            color="primary"
            onClick={handleInvoiceClick}
          />
        ) : (
          <Chip label="None" size="small" variant="outlined" />
        )}
      </TableCell>
    </TableRow>
  );
});
