import { apiClient } from "./client";
import type {
  InvoiceLineItemUpdate,
  InvoiceLineItemResponse,
} from "../types/invoice";

export async function updateInvoiceLineItemAdjustments(
  invoiceLineItemId: number,
  data: InvoiceLineItemUpdate
): Promise<InvoiceLineItemResponse> {
  return apiClient<InvoiceLineItemResponse>(
    `/api/v1/invoice-line-items/${invoiceLineItemId}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}
