import { request } from "./client";
import type { TipoEntorno } from "./systems";

/**
 * 35-P-02: registro de despliegues de los sistemas del cliente.
 *
 * El backend responde con un esquema distinto según el rol. El cliente solo
 * recibe despliegues a `prod` que llegaron (`ok` o `revertido`) y NUNCA el
 * checklist, el plan de vuelta atrás ni quién lo hizo: esos campos son
 * opcionales aquí, no los des por presentes.
 *
 * Reglas que devuelve la API (muéstralas tal cual, vienen en español):
 * - 422 si el entorno es de otro sistema.
 * - 422 si es un `ok` a `prod` sin respaldo y prueba de humo marcados.
 * - 422 si la versión, el resumen o el plan llevan algo con forma de clave.
 * - Un `ok` a `prod` publica "Versión X publicada" en la bitácora del proyecto.
 */
export type ResultadoDespliegue = "ok" | "fallido" | "revertido";

export type Despliegue = {
  id: number;
  system_id: number;
  system_name: string;
  environment_kind: TipoEntorno;
  version: string;
  summary: string;
  deployed_at: string;
  result: ResultadoDespliegue;
  /** Solo equipo. NULL si el entorno se quitó después (el tipo se conserva). */
  environment_id?: number | null;
  /** Solo equipo. */
  deployed_by?: number | null;
  /** Solo equipo. */
  deployed_by_name?: string | null;
  /** Solo equipo: checklist interno. */
  backup_done?: boolean;
  smoke_test_passed?: boolean;
  rollback_plan_written?: boolean;
  rollback_plan?: string | null;
  /** Solo equipo. */
  project_id?: number | null;
  /** Solo equipo: el avance publicado en la bitácora, si lo hubo. */
  published_update_id?: number | null;
  /** Solo equipo: admin, o el colaborador que lo registró. */
  can_edit?: boolean;
};

export type ListaDespliegues = { can_register: boolean; deployments: Despliegue[] };

export type DespliegueIn = {
  system_id: number;
  environment_id: number;
  /** Etiqueta o SHA corto. */
  version: string;
  /** Qué cambió, en lenguaje de cliente. */
  summary: string;
  /** ISO; por defecto, ahora. No puede ser futura. */
  deployed_at?: string | null;
  backup_done?: boolean;
  smoke_test_passed?: boolean;
  rollback_plan_written?: boolean;
  rollback_plan?: string | null;
  result?: ResultadoDespliegue;
  /** Por defecto, el proyecto de origen del sistema. */
  project_id?: number | null;
};
export type DespliegueUpdate = Partial<Omit<DespliegueIn, "system_id" | "environment_id" | "project_id">>;

export function getDeployments(filtros: { system_id?: number; environment_id?: number; project_id?: number } = {}): Promise<ListaDespliegues> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(filtros)) if (v) q.set(k, String(v));
  const s = q.toString();
  return request<ListaDespliegues>(`/deployments${s ? `?${s}` : ""}`);
}
export function getDeployment(id: number): Promise<Despliegue> {
  return request<Despliegue>(`/deployments/${id}`);
}
export function createDeployment(payload: DespliegueIn): Promise<Despliegue> {
  return request<Despliegue>("/deployments", { method: "POST", body: JSON.stringify(payload) });
}
export function updateDeployment(id: number, payload: DespliegueUpdate): Promise<Despliegue> {
  return request<Despliegue>(`/deployments/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}
/** Solo admin; para un registro erróneo. El avance ya publicado en la bitácora se queda. */
export function deleteDeployment(id: number): Promise<{ deleted: number }> {
  return request<{ deleted: number }>(`/deployments/${id}`, { method: "DELETE" });
}
