export type EntityType =
  | "invoice_line_item"
  | "campaign"
  | "line_item"
  | "comment";

export interface ChangeHistory {
  id: number;
  entity_type: EntityType;
  entity_id: number;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown>;
  changed_by_user_id: number;
  changed_by_username: string;
  created_at: string;
}

export interface ChangeHistoryListResponse {
  history: ChangeHistory[];
  total: number;
}
