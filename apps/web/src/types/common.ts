export interface Pagination {
  limit?: number;
  offset?: number;
}

export type SortDirection = "asc" | "desc";

export type CampaignSortField =
  | "id"
  | "name"
  | "total_booked"
  | "total_actual"
  | "total_billable"
  | "line_items_count";

export type InvoiceSortField =
  | "id"
  | "campaign_name"
  | "total_billable"
  | "line_items_count";

export interface SortParams<T extends string> {
  sortBy?: T;
  sortDir?: SortDirection;
}

export interface SearchParams {
  search?: string;
}

export interface CampaignListParams
  extends Pagination,
    SearchParams,
    SortParams<CampaignSortField> {}

export interface InvoiceListParams
  extends Pagination,
    SearchParams,
    SortParams<InvoiceSortField> {}
