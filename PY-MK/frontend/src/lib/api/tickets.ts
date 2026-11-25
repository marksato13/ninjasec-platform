import { request, downloadFile, buildQuery } from "./client";

export type SupportTicketItem = {
  id: number;
  organization_id: number;
  client_id: number;
  integration_id?: number | null;
  device_id?: number | null;
  review_id?: number | null;
  finding_id?: number | null;
  title: string;
  description?: string | null;
  category?: string | null;
  priority: string;
  status: string;
  assigned_to?: number | null;
  resolution?: string | null;
  opened_at: string;
  closed_at?: string | null;
  created_at: string;
  updated_at: string;
  // 35-P-03 · solicitudes de cambio
  kind: TicketKind;
  system_id?: number | null;
  /** Solo en incidencias de un sistema aún en garantía: hasta cuándo. */
  warranty_until?: string | null;
  estimate_hours?: number | null;
  estimate_note?: string | null;
  estimated_at?: string | null;
  client_decision?: ChangeDecision | null;
  client_decision_note?: string | null;
  client_decision_at?: string | null;
  converted_project_id?: number | null;
};

/** Incidencia: algo falla. Cambio: algo nuevo sobre un sistema que ya tiene. */
export type TicketKind = "incidencia" | "cambio";
export type ChangeDecision = "approved" | "rejected";

export type SupportTicketEventItem = {
  id: number;
  ticket_id: number;
  event_type: string;
  from_status?: string | null;
  to_status?: string | null;
  user_id?: number | null;
  notes?: string | null;
  created_at: string;
};

export type SupportTicketDetail = SupportTicketItem & { events: SupportTicketEventItem[] };

export type SupportTicketStats = {
  total: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  open_count: number;
  closed_count: number;
  avg_resolution_hours: number | null;
};

type TicketFilters = { client_id?: number; ticket_status?: string; priority?: string; date_from?: string; date_to?: string };

export async function getSupportTickets(filters?: TicketFilters): Promise<SupportTicketItem[]> {
  return request<SupportTicketItem[]>(`/support-tickets/${buildQuery({ ...filters })}`);
}

export async function getSupportTicketStats(filters?: { client_id?: number; date_from?: string }): Promise<SupportTicketStats> {
  return request<SupportTicketStats>(`/support-tickets/stats${buildQuery({ ...filters })}`);
}

export async function getSupportTicket(ticketId: number): Promise<SupportTicketDetail> {
  return request<SupportTicketDetail>(`/support-tickets/${ticketId}`);
}

export async function createSupportTicket(payload: {
  client_id: number;
  integration_id?: number | null;
  device_id?: number | null;
  review_id?: number | null;
  finding_id?: number | null;
  title: string;
  description?: string | null;
  category?: string | null;
  priority: string;
  assigned_to?: number | null;
  kind?: TicketKind;
  system_id?: number | null;
}): Promise<SupportTicketItem> {
  return request<SupportTicketItem>("/support-tickets/", { method: "POST", body: JSON.stringify(payload) });
}

/** El equipo estima un cambio (admin y colaborador). Tras un rechazo, reestimar reabre la decisión. */
export async function estimateChange(ticketId: number, payload: { hours: number; note?: string | null }): Promise<SupportTicketItem> {
  return request<SupportTicketItem>(`/support-tickets/${ticketId}/estimate`, { method: "POST", body: JSON.stringify(payload) });
}

/** Solo el cliente: aprueba o rechaza la estimación. Rechazar exige un motivo de 5+ caracteres. */
export async function decideChange(ticketId: number, decision: ChangeDecision, note?: string | null): Promise<SupportTicketItem> {
  return request<SupportTicketItem>(`/support-tickets/${ticketId}/client-decision`, { method: "POST", body: JSON.stringify({ decision, note }) });
}

/** Solo admin: un cambio aprobado pasa a tarea de un proyecto existente (`project_id`) o nuevo (`project_name`). */
export async function convertChange(ticketId: number, payload: { assigned_user_id: number; project_id?: number | null; project_name?: string | null }): Promise<SupportTicketItem> {
  return request<SupportTicketItem>(`/support-tickets/${ticketId}/convert`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateSupportTicket(ticketId: number, payload: {
  title?: string | null;
  description?: string | null;
  category?: string | null;
  priority?: string | null;
  status?: string | null;
  assigned_to?: number | null;
  resolution?: string | null;
}): Promise<SupportTicketItem> {
  return request<SupportTicketItem>(`/support-tickets/${ticketId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export async function createSupportTicketEvent(ticketId: number, payload: { event_type: string; notes?: string | null }): Promise<SupportTicketEventItem> {
  return request<SupportTicketEventItem>(`/support-tickets/${ticketId}/events`, { method: "POST", body: JSON.stringify(payload) });
}

export async function createTicketFromFinding(findingId: number, payload: { priority: string; assigned_to?: number | null; category?: string | null; description_override?: string | null }): Promise<SupportTicketItem> {
  return request<SupportTicketItem>(`/support-tickets/from-finding/${findingId}`, { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteSupportTicket(ticketId: number): Promise<{ message: string }> {
  return request<{ message: string }>(`/support-tickets/${ticketId}`, { method: "DELETE" });
}

export async function importSupportTickets(file: File): Promise<{ created: number; skipped: number; errors: string[] }> {
  const body = new FormData();
  body.append("file", file);
  return request<{ created: number; skipped: number; errors: string[] }>("/support-tickets/import", { method: "POST", body });
}

export async function exportSupportTicketsXlsx(filters?: TicketFilters): Promise<void> {
  return downloadFile(`/support-tickets/export-xlsx${buildQuery({ ...filters })}`, "tickets.xlsx");
}
