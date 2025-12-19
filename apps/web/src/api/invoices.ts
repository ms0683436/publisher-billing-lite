import { apiClient } from "./client";
import { buildUrl } from "./utils";
import type { InvoiceListResponse, InvoiceDetail } from "../types/invoice";
import type { InvoiceListParams } from "../types/common";

export async function fetchInvoices(
  params?: InvoiceListParams
): Promise<InvoiceListResponse> {
  const url = buildUrl("/api/v1/invoices", {
    limit: params?.limit,
    offset: params?.offset,
    search: params?.search,
    sort_by: params?.sortBy,
    sort_dir: params?.sortDir,
  });
  return apiClient<InvoiceListResponse>(url);
}

export async function fetchInvoice(id: number): Promise<InvoiceDetail> {
  return apiClient<InvoiceDetail>(`/api/v1/invoices/${id}`);
}
