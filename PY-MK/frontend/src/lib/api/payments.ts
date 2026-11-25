import { request } from "./client";

/** C3: hitos de pago de un proyecto. Solo estado: sin pasarela ni datos bancarios. */
export type EstadoPago = "pending" | "invoiced" | "paid";
export type Moneda = "PEN" | "USD";

export type HitoPago = {
  id: number; project_id: number; title: string; amount: string; currency: Moneda;
  due_date: string | null; status: EstadoPago; overdue: boolean; note: string | null; paid_at: string | null;
};
export type TotalPago = { currency: Moneda; total: string; paid: string; pending: string };
export type HitosPago = { project_id: number; can_manage: boolean; milestones: HitoPago[]; totals: TotalPago[] };

export type HitoPagoIn = {
  title: string; amount: string; currency: Moneda; due_date?: string | null; status?: EstadoPago; note?: string | null;
};

export function getPaymentMilestones(projectId: number): Promise<HitosPago> {
  return request<HitosPago>(`/payment-milestones/projects/${projectId}`);
}
export function createPaymentMilestone(projectId: number, payload: HitoPagoIn): Promise<HitosPago> {
  return request<HitosPago>(`/payment-milestones/projects/${projectId}`, { method: "POST", body: JSON.stringify(payload) });
}
export function updatePaymentMilestone(id: number, payload: Partial<HitoPagoIn>): Promise<HitosPago> {
  return request<HitosPago>(`/payment-milestones/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}
export function deletePaymentMilestone(id: number): Promise<HitosPago> {
  return request<HitosPago>(`/payment-milestones/${id}`, { method: "DELETE" });
}
