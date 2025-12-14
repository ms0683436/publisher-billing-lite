export interface LineItemInCampaign {
  id: number;
  campaign_id: number;
  name: string;
  booked_amount: string;
}

export interface InvoiceSummary {
  id: number;
  campaign_id: number;
  total_actual: string;
  total_adjustments: string;
  total_billable: string;
  line_items_count: number;
}

export interface CampaignListItem {
  id: number;
  name: string;
  total_booked: string;
  total_actual: string;
  total_billable: string;
  line_items_count: number;
  invoice_id: number | null;
}

export interface CampaignDetail {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  line_items: LineItemInCampaign[];
  invoice_summary: InvoiceSummary | null;
}

export interface CampaignListResponse {
  campaigns: CampaignListItem[];
  total: number;
  limit: number;
  offset: number;
}
