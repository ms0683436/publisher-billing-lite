export interface LineItemInInvoice {
  id: number;
  campaign_id: number;
  name: string;
  booked_amount: string;
  actual_amount: string;
  adjustments: string;
  billable_amount: string;
  invoice_line_item_id: number;
}

export interface InvoiceListItem {
  id: number;
  campaign_id: number;
  campaign_name: string;
  total_billable: string;
  line_items_count: number;
}

export interface InvoiceDetail {
  id: number;
  campaign_id: number;
  campaign_name: string;
  created_at: string;
  updated_at: string;
  line_items: LineItemInInvoice[];
  total_actual: string;
  total_adjustments: string;
  total_billable: string;
}

export interface InvoiceListResponse {
  invoices: InvoiceListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface InvoiceLineItemResponse {
  id: number;
  invoice_id: number;
  line_item_id: number;
  actual_amount: string;
  adjustments: string;
  billable_amount: string;
  updated_at: string;
}

export interface AdjustmentItem {
  invoice_line_item_id: number;
  adjustments: string;
}

export interface BatchAdjustmentsUpdate {
  updates: AdjustmentItem[];
}

export interface BatchAdjustmentsResponse {
  invoice_id: number;
  updated: InvoiceLineItemResponse[];
}
