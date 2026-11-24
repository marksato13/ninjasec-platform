import { request } from "./client";

/**
 * Seguimiento de un proyecto: la misma vista para el cliente y para el especialista.
 * El servidor ya filtra lo que cada quien puede ver; esto solo la pinta.
 */

export type FaseClave = "diagnostico" | "planificacion" | "implementacion" | "transferencia" | "acompanamiento";
export type EstadoFase = "done" | "current" | "todo";
export type TipoAvance = "update" | "milestone" | "phase_change" | "task_done";

export type FaseSeguimiento = {
  key: FaseClave; label: string; description: string; state: EstadoFase;
  tasks_total: number; tasks_done: number;
};
export type Ahora = { task_id: number; title: string; person: string; phase: string | null };
export type Persona = { name: string; role: string | null; open_tasks: number; done_tasks: number; working_now: boolean };
export type EquipoProyecto = {
  id: number; hostname: string; type: string | null; vendor: string | null; model: string | null; status: string;
};
export type Avance = {
  id: number; kind: TipoAvance; phase: string | null; title: string; body: string | null;
  link_url: string | null; author: string | null; created_at: string; visible_to_client: boolean;
};
export type Candidato = EquipoProyecto & { linked: boolean };

export type VistaSeguimiento = {
  id: number; name: string; description: string | null; line: "dev" | "infra";
  status: string; phase: FaseClave; paused: boolean; start_date: string | null; end_date: string | null;
  progress_percent: number; tasks_total: number; tasks_done: number;
  phases: FaseSeguimiento[]; now: Ahora[]; next_up: string[];
  team: Persona[]; devices: EquipoProyecto[]; updates: Avance[];
  last_activity_at: string | null; can_manage: boolean; candidate_devices: Candidato[] | null;
};

export const getSeguimiento = (id: number) => request<VistaSeguimiento>(`/tracking/projects/${id}`);

export const cambiarFase = (id: number, phase: FaseClave, note?: string | null) =>
  request<VistaSeguimiento>(`/tracking/projects/${id}/phase`, {
    method: "PATCH", body: JSON.stringify({ phase, note: note || null }),
  });

export const publicarAvance = (
  id: number,
  body: { title: string; body?: string | null; kind: "update" | "milestone"; link_url?: string | null; visible_to_client: boolean },
) => request<VistaSeguimiento>(`/tracking/projects/${id}/updates`, { method: "POST", body: JSON.stringify(body) });

export const fijarEquipos = (id: number, device_ids: number[]) =>
  request<VistaSeguimiento>(`/tracking/projects/${id}/devices`, { method: "PUT", body: JSON.stringify({ device_ids }) });
