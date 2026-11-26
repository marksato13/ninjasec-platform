import { request } from "./client";

/**
 * 35-P-05: pruebas de aceptación (UAT) de un proyecto.
 *
 * El equipo (admin o colaborador del proyecto) escribe los casos; el cliente
 * los marca `aprobado` u `observado` desde el portal. Cuando todos están
 * aprobados, `summary.ready_for_signoff` es true: es el momento de proponer
 * el acta de conformidad (35-P-06).
 *
 * El backend responde con un esquema distinto según el rol: el cliente NUNCA
 * recibe `created_by`, `decided_by`, `created_at` ni `updated_at`. Esos campos
 * son opcionales aquí; no los des por presentes. Usa `can_manage` (equipo) y
 * `can_decide` (cliente) para decidir qué botones mostrar.
 *
 * Reglas que devuelve la API (muéstralas tal cual, vienen en español):
 * - 422 al observar sin nota de al menos 5 caracteres.
 * - 409 al decidir, cambiar o quitar un caso ya aprobado (es evidencia del acta).
 * - 403 si el equipo intenta decidir por el cliente, o el cliente escribir casos.
 * - 422 si un texto lleva algo con forma de clave.
 * - Si el equipo cambia título, pasos o resultado esperado de un caso observado,
 *   vuelve a `pendiente` (el cliente lo comprueba otra vez).
 */
export type EstadoCaso = "pendiente" | "aprobado" | "observado";

export type CasoAceptacion = {
  id: number;
  project_id: number;
  position: number;
  title: string;
  steps: string;
  expected: string;
  status: EstadoCaso;
  client_note: string | null;
  decided_at: string | null;
  /** Solo equipo. */
  decided_by?: number | null;
  /** Solo equipo. */
  created_by?: number | null;
  /** Solo equipo. */
  created_at?: string;
  /** Solo equipo. */
  updated_at?: string;
};

export type ResumenAceptacion = {
  total: number;
  pendiente: number;
  aprobado: number;
  observado: number;
  /** Hay casos y todos están aprobados: proponer el acta de conformidad. */
  ready_for_signoff: boolean;
};

export type VistaAceptacion = {
  project_id: number;
  /** true para el equipo: puede escribir, corregir y (admin) quitar casos. */
  can_manage: boolean;
  /** true para el cliente: puede aprobar u observar. */
  can_decide: boolean;
  summary: ResumenAceptacion;
  cases: CasoAceptacion[];
};

export type CasoAceptacionInput = {
  title: string;
  steps: string;
  expected: string;
  /** Si se omite, va al final. */
  position?: number;
};

export type DecisionCaso = { decision: "aprobado" | "observado"; note?: string | null };

const BASE = "/acceptance-cases";

export async function getAcceptanceCases(projectId: number): Promise<VistaAceptacion> {
  return request<VistaAceptacion>(`${BASE}/projects/${projectId}`);
}

export async function createAcceptanceCase(projectId: number, payload: CasoAceptacionInput): Promise<VistaAceptacion> {
  return request<VistaAceptacion>(`${BASE}/projects/${projectId}`, { method: "POST", body: JSON.stringify(payload) });
}

export async function updateAcceptanceCase(caseId: number, payload: Partial<CasoAceptacionInput>): Promise<VistaAceptacion> {
  return request<VistaAceptacion>(`${BASE}/${caseId}`, { method: "PUT", body: JSON.stringify(payload) });
}

/** Solo admin, y solo casos no aprobados. Devuelve la vista actualizada. */
export async function deleteAcceptanceCase(caseId: number): Promise<VistaAceptacion> {
  return request<VistaAceptacion>(`${BASE}/${caseId}`, { method: "DELETE" });
}

/** Solo el cliente del proyecto. */
export async function decideAcceptanceCase(caseId: number, payload: DecisionCaso): Promise<VistaAceptacion> {
  return request<VistaAceptacion>(`${BASE}/${caseId}/decision`, { method: "POST", body: JSON.stringify(payload) });
}
