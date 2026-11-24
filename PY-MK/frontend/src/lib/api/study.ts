import { request } from "./client";

export type EstadoModulo = "pending" | "in_progress" | "completed";

export type PlanResumen = {
  id: number; name: string; slug: string; area: string; description: string | null;
  target_certification: string | null; vendor: string | null; exam_code: string | null;
  estimated_hours: number | null; modules_count: number;
};

export type Modulo = {
  id: number; position: number; title: string; objective: string | null; topics: string | null;
  lab: string | null; estimated_hours: number | null; weight_percent: number | null;
};

export type PlanDetalle = PlanResumen & { modules: Modulo[] };

export type Inscripcion = {
  id: number; plan_id: number; plan_name: string; exam_code: string | null;
  target_date: string | null; weekly_hours: number | null;
  percent: number; modules_done: number; modules_total: number; hours_done: number; hours_total: number;
};

export type AvanceModulo = Modulo & {
  status: string; hours_spent: number | null; evidence_url: string | null; notes: string | null;
  progress_id: number | null; validated: boolean;
};

export type InscripcionDetalle = Inscripcion & { modules: AvanceModulo[] };

export type FilaEquipo = {
  enrollment_id: number; user_id: number; user_name: string; plan_name: string;
  percent: number; modules_done: number; modules_total: number; pending_validation: number;
};

export const getPlanes = () => request<PlanResumen[]>("/study/plans");
export const getPlan = (id: number) => request<PlanDetalle>(`/study/plans/${id}`);
export const inscribirse = (planId: number, body: { target_date?: string | null; weekly_hours?: number | null } = {}) =>
  request<Inscripcion>(`/study/plans/${planId}/enroll`, { method: "POST", body: JSON.stringify(body) });
export const getMisInscripciones = () => request<Inscripcion[]>("/study/me");
export const getMiInscripcion = (id: number) => request<InscripcionDetalle>(`/study/me/${id}`);
export const marcarAvance = (
  enrollmentId: number, moduleId: number,
  body: { status: EstadoModulo; hours_spent?: number | null; evidence_url?: string | null; notes?: string | null },
) => request<Inscripcion>(`/study/me/${enrollmentId}/modules/${moduleId}`, { method: "PATCH", body: JSON.stringify(body) });
export const getAvanceEquipo = () => request<FilaEquipo[]>("/study/team");
export const validarModulo = (progressId: number) =>
  request<{ id: number; status: string }>(`/study/progress/${progressId}/validate`, { method: "POST" });
export const getDetalleEquipo = (enrollmentId: number) => request<InscripcionDetalle>(`/study/team/${enrollmentId}`);
