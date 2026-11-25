import { getStoredToken, isTokenExpired } from "@/lib/auth";
import { notifySessionExpired, SessionExpiredError } from "@/lib/session-expired";

import { request } from "./client";

export type AreaCert = "sec" | "dev" | "both";

export type SkillItem = { id: number; name: string; category?: string | null; is_active: boolean; created_at?: string | null };
export type UserSkillItem = { id: number; user_id: number; skill_id: number; skill_name?: string | null; level?: string | null; status: string; rejection_reason?: string | null; verified_by?: number | null; verified_at?: string | null; created_at?: string | null };
export type UserCertificationItem = {
  id: number; user_id: number; name: string; issuer?: string | null; credential_id?: string | null; url?: string | null;
  status: string; rejection_reason?: string | null; verified_by?: number | null; verified_at?: string | null;
  issued_at?: string | null; expires_at?: string | null; created_at?: string | null;
  is_expired: boolean; days_until_expiry: number | null; effective_status: string;
  area?: AreaCert | null; has_file?: boolean; file_name?: string | null; file_type?: string | null; file_size?: number | null;
};
export type PendingApprovalsCount = { pending: number };

/** Lo que el cliente ve de una certificacion: sin adjunto ni codigo de credencial. */
export type CertificacionPublica = {
  name: string; issuer: string | null; area: AreaCert | null;
  issued_at: string | null; expires_at: string | null; url: string | null;
};
export type MiembroCertificado = {
  user_id: number; full_name: string; role_in_project: string | null; certifications: CertificacionPublica[];
};
export type FilaMatriz = {
  user_id: number; full_name: string; role: string;
  certifications: CertificacionPublica[]; skills: { name: string; level: string | null }[];
};

export type CertificationPayload = {
  name: string; issuer?: string | null; credential_id?: string | null; url?: string | null;
  issued_at?: string | null; expires_at?: string | null; area?: AreaCert | null;
};

export async function getSkills(): Promise<SkillItem[]> { return request<SkillItem[]>("/skills/"); }
export async function createSkill(payload: { name: string; category?: string | null }): Promise<SkillItem> { return request<SkillItem>("/skills/", { method: "POST", body: JSON.stringify(payload) }); }
export async function getUserSkills(): Promise<UserSkillItem[]> { return request<UserSkillItem[]>("/skills/user-skills"); }
export async function createUserSkill(payload: { skill_id: number; level?: string | null; user_id?: number | null }): Promise<UserSkillItem> { return request<UserSkillItem>("/skills/user-skills", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateUserSkill(id: number, payload: { level?: string | null }): Promise<UserSkillItem> { return request<UserSkillItem>(`/skills/user-skills/${id}`, { method: "PUT", body: JSON.stringify(payload) }); }
export async function verifyUserSkill(id: number, status: string, rejectionReason?: string): Promise<UserSkillItem> { return request<UserSkillItem>(`/skills/user-skills/${id}/verify`, { method: "POST", body: JSON.stringify({ status, rejection_reason: rejectionReason }) }); }
export async function getUserCertifications(): Promise<UserCertificationItem[]> { return request<UserCertificationItem[]>("/user-certifications/"); }
export async function createUserCertification(payload: CertificationPayload): Promise<UserCertificationItem> { return request<UserCertificationItem>("/user-certifications/", { method: "POST", body: JSON.stringify(payload) }); }
export async function updateUserCertification(id: number, payload: Partial<CertificationPayload>): Promise<UserCertificationItem> { return request<UserCertificationItem>(`/user-certifications/${id}`, { method: "PUT", body: JSON.stringify(payload) }); }
export async function verifyUserCertification(id: number, status: string, rejectionReason?: string): Promise<UserCertificationItem> { return request<UserCertificationItem>(`/user-certifications/${id}/verify`, { method: "POST", body: JSON.stringify({ status, rejection_reason: rejectionReason }) }); }
export async function getPendingApprovalsCount(): Promise<PendingApprovalsCount> { return request<PendingApprovalsCount>("/skills/approvals/pending-count"); }

export async function uploadCertificateFile(id: number, file: File): Promise<UserCertificationItem> {
  const body = new FormData();
  body.append("file", file);
  return request<UserCertificationItem>(`/user-certifications/${id}/file`, { method: "POST", body });
}

export const getTeamMatrix = () => request<FilaMatriz[]>("/user-certifications/matrix");
export const getProjectTeamCertifications = (projectId: number) =>
  request<MiembroCertificado[]>(`/projects/${projectId}/team-certifications`);

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8024/api/v1";

/**
 * Trae el certificado adjunto como blob, con la sesion. Devuelve una URL local
 * (blob:) que quien la pide debe liberar con URL.revokeObjectURL.
 */
export async function getCertificateFileUrl(id: number): Promise<{ url: string; type: string }> {
  const token = getStoredToken();
  if (token && isTokenExpired(token)) {
    notifySessionExpired();
    throw new SessionExpiredError();
  }
  const response = await fetch(`${API_BASE}/user-certifications/${id}/file`, {
    cache: "no-store",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (response.status === 401 && token) {
    notifySessionExpired();
    throw new SessionExpiredError();
  }
  if (!response.ok) throw new Error(response.status === 404 ? "El certificado no tiene archivo" : `Error ${response.status}`);
  const blob = await response.blob();
  return { url: URL.createObjectURL(blob), type: blob.type };
}
