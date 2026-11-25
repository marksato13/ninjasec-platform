import { request } from "./client";

/** area_id: el backend aún no lo expone en ServiceRead; mientras falte, el servicio cuenta para los dos modos. */
export type ServiceItem = { id: number; title: string; slug: string; area_id?: number | null; category?: string | null; summary?: string | null; description?: string | null; price_label?: string | null; is_public?: boolean; active: boolean };
export type ServiceRequestItem = { id: number; service_id: number; requester_name: string; requester_email: string; status: string; request_type?: string | null; message?: string | null; created_at?: string | null; client_id?: number | null; project_id?: number | null };

export async function getServices(): Promise<ServiceItem[]> {
  return request<ServiceItem[]>("/services/");
}

export async function createService(payload: { organization_id: number; title: string; slug: string; category?: string | null; summary?: string | null; description?: string | null; price_label?: string | null; is_public?: boolean; active?: boolean }): Promise<ServiceItem> {
  return request<ServiceItem>("/services/", { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteService(serviceId: number): Promise<{ message: string }> {
  return request<{ message: string }>(`/services/${serviceId}`, { method: "DELETE" });
}

export async function getServiceRequests(): Promise<ServiceRequestItem[]> {
  return request<ServiceRequestItem[]>("/services/requests");
}

export async function createServiceRequest(payload: { service_id: number; requester_name: string; requester_email: string; message?: string | null; request_type?: string | null; client_id?: number | null }): Promise<ServiceRequestItem> {
  // Con `request` viaja el token si hay sesion: asi el backend enlaza la
  // solicitud del portal a la empresa del cliente. Sin sesion sigue siendo publica.
  return request<ServiceRequestItem>("/services/requests", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateServiceRequestStatus(requestId: number, status: string): Promise<ServiceRequestItem> {
  return request<ServiceRequestItem>(`/services/requests/${requestId}`, { method: "PATCH", body: JSON.stringify({ status }) });
}

// Solicitud aprobada -> proyecto, con el area del servicio. `client_id` solo hace
// falta si la solicitud llego del formulario publico (sin cliente).
export async function convertServiceRequest(requestId: number, payload: { project_type_id: number; client_id?: number | null; name?: string | null; description?: string | null }): Promise<ServiceRequestItem> {
  return request<ServiceRequestItem>(`/services/requests/${requestId}/convert`, { method: "POST", body: JSON.stringify(payload) });
}
