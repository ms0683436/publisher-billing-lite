import { apiClient } from "./client";
import type { InvoiceListResponse, InvoiceDetail } from "../types/invoice";
import type { Pagination } from "../types/common";

export async function fetchInvoices(
  pagination?: Pagination
): Promise<InvoiceListResponse> {
  const params = new URLSearchParams();
  if (pagination?.limit) params.set("limit", String(pagination.limit));
  if (pagination?.offset) params.set("offset", String(pagination.offset));

  const query = params.toString();
  return apiClient<InvoiceListResponse>(
    `/api/v1/invoices${query ? `?${query}` : ""}`
  );
}

export async function fetchInvoice(id: number): Promise<InvoiceDetail> {
  return apiClient<InvoiceDetail>(`/api/v1/invoices/${id}`);
}
