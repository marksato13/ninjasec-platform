import { buildQuery, request } from "./client";

// Ventanas de trabajo: permiso del cliente para tocar algo que puede cortar su
// servicio. Flujo: el equipo la pide (72 h antes), el cliente la aprueba o la
// rechaza, el equipo la ejecuta y la cierra.

export type WorkWindowStatus =
  | "requested"
  | "approved"
  | "rejected"
  | "in_progress"
  | "completed"
  | "rolled_back"
  | "cancelled";

export type WorkWindowImpact = "low" | "medium" | "high";

export type WorkWindowItem = {
  id: number;
  organization_id: number;
  project_id: number;
  requested_by_user_id?: number | null;
  title: string;
  change_description: string;
  systems_affected?: string | null;
  impact: WorkWindowImpact;
  rollback_plan: string;
  is_emergency: boolean;
  starts_at: string;
  ends_at: string;
  status: WorkWindowStatus;
  client_decision_by_user_id?: number | null;
  client_decision_at?: string | null;
  client_comment?: string | null;
  execution_note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type WorkWindowCreatePayload = {
  project_id: number;
  title: string;
  change_description: string;
  systems_affected?: string | null;
  impact: WorkWindowImpact;
  rollback_plan: string;
  is_emergency?: boolean;
  starts_at: string; // ISO 8601 con zona
  ends_at: string;
};

export async function getWorkWindows(filters?: { project_id?: number; window_status?: WorkWindowStatus }): Promise<WorkWindowItem[]> {
  return request<WorkWindowItem[]>(`/work-windows/${buildQuery(filters ?? {})}`);
}

export async function getWorkWindow(id: number): Promise<WorkWindowItem> {
  return request<WorkWindowItem>(`/work-windows/${id}`);
}

export async function requestWorkWindow(payload: WorkWindowCreatePayload): Promise<WorkWindowItem> {
  return request<WorkWindowItem>("/work-windows/", { method: "POST", body: JSON.stringify(payload) });
}

export async function decideWorkWindow(id: number, payload: { approve: boolean; comment?: string | null }): Promise<WorkWindowItem> {
  return request<WorkWindowItem>(`/work-windows/${id}/decision`, { method: "POST", body: JSON.stringify(payload) });
}

export async function changeWorkWindowStatus(
  id: number,
  payload: { status: Extract<WorkWindowStatus, "in_progress" | "completed" | "rolled_back" | "cancelled">; note?: string | null },
): Promise<WorkWindowItem> {
  return request<WorkWindowItem>(`/work-windows/${id}/status`, { method: "POST", body: JSON.stringify(payload) });
}
