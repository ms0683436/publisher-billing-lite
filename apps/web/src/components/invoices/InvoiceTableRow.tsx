import { memo, useCallback } from "react";
import { TableRow, TableCell } from "@mui/material";
import { MoneyDisplay } from "../common/MoneyDisplay";
import type { InvoiceListItem } from "../../types/invoice";

interface InvoiceTableRowProps {
  invoice: InvoiceListItem;
  onRowClick: (id: number) => void;
}

export const InvoiceTableRow = memo(function InvoiceTableRow({
  invoice,
  onRowClick,
}: InvoiceTableRowProps) {
  const handleRowClick = useCallback(() => {
    onRowClick(invoice.id);
  }, [invoice.id, onRowClick]);

  return (
    <TableRow hover onClick={handleRowClick} sx={{ cursor: "pointer" }}>
      <TableCell>#{invoice.id}</TableCell>
      <TableCell>{invoice.campaign_name}</TableCell>
      <TableCell align="right">
        <MoneyDisplay value={invoice.total_billable} />
      </TableCell>
      <TableCell align="center">{invoice.line_items_count}</TableCell>
    </TableRow>
  );
});
