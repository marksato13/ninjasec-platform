import { buildQuery, downloadFile, request } from "./client";

export type AuditItem = { id: number; action: string; entity_type: string; entity_id?: string | null; user_id?: number | null; created_at?: string | null; metadata_json?: string | null };

export async function getAuditLogs(limit?: number): Promise<AuditItem[]> {
  const qs = limit ? `?limit=${limit}` : "";
  return request<AuditItem[]>(`/audit-logs/${qs}`);
}

export type AuditFilters = {
  action?: string;
  entity_type?: string;
  entity_id?: string;
};

export async function exportAuditLogs(format: "pdf" | "xlsx", filters: AuditFilters): Promise<void> {
  const query = buildQuery({ format, ...filters });
  await downloadFile(`/audit-logs/export${query}`, `auditoria.${format}`);
}
