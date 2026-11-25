import { request } from "./client";

/**
 * 35-P-01: sistemas del cliente y sus entornos.
 *
 * El backend responde con un esquema distinto según el rol: el cliente NO
 * recibe `repository_url`, `origin_project_id`, `client_name`,
 * `secrets_location` ni `visible_to_client`, y solo ve los entornos visibles.
 * Por eso esos campos son opcionales aquí: no los des por presentes.
 */
export type EstadoSistema = "en_construccion" | "en_produccion" | "en_mantenimiento" | "retirado";
export type PlanSoporte = "ninguno" | "basico" | "profesional" | "a_medida";
export type TipoEntorno = "dev" | "staging" | "prod";

export type EntornoSistema = {
  id: number;
  kind: TipoEntorno;
  url: string | null;
  hosting: string | null;
  domain_expires_at: string | null;
  certificate_expires_at: string | null;
  /** Dominio o certificado vence en 30 días o menos (o ya venció). */
  expiring_soon: boolean;
  /** Solo equipo. Dice DÓNDE están las claves, nunca cuáles son. */
  secrets_location?: string | null;
  /** Solo equipo. */
  visible_to_client?: boolean;
};

export type SistemaCliente = {
  id: number;
  client_id: number;
  name: string;
  description: string | null;
  stack: string | null;
  status: EstadoSistema;
  warranty_until: string | null;
  /** Garantía vence en 30 días o menos (falso si está retirado). */
  warranty_expiring: boolean;
  support_plan: PlanSoporte;
  environments: EntornoSistema[];
  /** Solo equipo. */
  client_name?: string | null;
  /** Solo equipo. */
  repository_url?: string | null;
  /** Solo equipo. */
  origin_project_id?: number | null;
};

export type FichaSistema = SistemaCliente & { can_manage: boolean };
export type ListaSistemas = { can_manage: boolean; systems: SistemaCliente[] };

export type SistemaIn = {
  client_id: number;
  name: string;
  description?: string | null;
  stack?: string | null;
  repository_url?: string | null;
  status?: EstadoSistema;
  warranty_until?: string | null;
  support_plan?: PlanSoporte;
  origin_project_id?: number | null;
};
export type SistemaUpdate = Partial<Omit<SistemaIn, "client_id">>;

export type EntornoIn = {
  kind: TipoEntorno;
  url?: string | null;
  hosting?: string | null;
  domain_expires_at?: string | null;
  certificate_expires_at?: string | null;
  secrets_location?: string | null;
  visible_to_client?: boolean;
};

export function getClientSystems(clientId?: number): Promise<ListaSistemas> {
  const q = clientId ? `?client_id=${clientId}` : "";
  return request<ListaSistemas>(`/client-systems${q}`);
}
export function getClientSystem(id: number): Promise<FichaSistema> {
  return request<FichaSistema>(`/client-systems/${id}`);
}
export function createClientSystem(payload: SistemaIn): Promise<FichaSistema> {
  return request<FichaSistema>("/client-systems", { method: "POST", body: JSON.stringify(payload) });
}
export function updateClientSystem(id: number, payload: SistemaUpdate): Promise<FichaSistema> {
  return request<FichaSistema>(`/client-systems/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}
/** Solo en construcción; uno que llegó a producción se marca `retirado` (409). */
export function deleteClientSystem(id: number): Promise<{ deleted: number }> {
  return request<{ deleted: number }>(`/client-systems/${id}`, { method: "DELETE" });
}
export function createSystemEnvironment(systemId: number, payload: EntornoIn): Promise<FichaSistema> {
  return request<FichaSistema>(`/client-systems/${systemId}/environments`, {
    method: "POST", body: JSON.stringify(payload),
  });
}
export function updateSystemEnvironment(envId: number, payload: Partial<EntornoIn>): Promise<FichaSistema> {
  return request<FichaSistema>(`/client-systems/environments/${envId}`, {
    method: "PUT", body: JSON.stringify(payload),
  });
}
export function deleteSystemEnvironment(envId: number): Promise<FichaSistema> {
  return request<FichaSistema>(`/client-systems/environments/${envId}`, { method: "DELETE" });
}
