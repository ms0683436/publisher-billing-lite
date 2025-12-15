import { apiClient } from "./client";
import type {
  BatchAdjustmentsResponse,
  BatchAdjustmentsUpdate,
} from "../types/invoice";

export async function batchUpdateAdjustments(
  invoiceId: number,
  data: BatchAdjustmentsUpdate
): Promise<BatchAdjustmentsResponse> {
  return apiClient<BatchAdjustmentsResponse>(
    `/api/v1/invoices/${invoiceId}/adjustments`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    }
  );
}
