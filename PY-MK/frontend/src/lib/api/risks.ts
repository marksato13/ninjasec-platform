import { request } from "./client";

export type RiskCatalogItem = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  category: string;
  is_global: boolean;
};

export type RiskAsset = {
  id: number;
  client_id: number;
  device_id: number | null;
  name: string;
  asset_type: string;
  confidentiality: number;
  integrity: number;
  availability: number;
  business_value: number;
  owner_user_id: number | null;
  created_at: string;
  updated_at: string;
};

export type RiskAssetCreatePayload = Omit<RiskAsset, "id" | "business_value" | "created_at" | "updated_at" | "device_id" | "owner_user_id"> & {
  device_id?: number | null;
  owner_user_id?: number | null;
};

export type RiskItem = {
  id: number;
  client_id: number;
  asset_id: number;
  title: string;
  description: string | null;
  threat: string | null;
  vulnerability: string | null;
  likelihood: number;
  impact: number;
  inherent_score: number;
  treatment: string | null;
  residual_likelihood: number | null;
  residual_impact: number | null;
  residual_score: number | null;
  status: string;
  owner_user_id: number | null;
  review_date: string | null;
  created_at: string;
  updated_at: string;
  threats: RiskCatalogItem[];
  vulnerabilities: RiskCatalogItem[];
};

export type RiskCreatePayload = {
  client_id: number;
  asset_id: number;
  title: string;
  likelihood: number;
  impact: number;
  threat_ids?: number[];
  vulnerability_ids?: number[];
};

export type HeatmapCell = { likelihood: number; impact: number; risks: RiskItem[] };

export const getRiskAssets = (clientId?: number) =>
  request<RiskAsset[]>(`/risks/assets${clientId ? `?client_id=${clientId}` : ""}`);
export const createRiskAsset = (payload: RiskAssetCreatePayload) =>
  request<RiskAsset>("/risks/assets", { method: "POST", body: JSON.stringify(payload) });

export const getRisks = (clientId?: number) =>
  request<RiskItem[]>(`/risks/${clientId ? `?client_id=${clientId}` : ""}`);
export const createRisk = (payload: RiskCreatePayload) =>
  request<RiskItem>("/risks/", { method: "POST", body: JSON.stringify(payload) });
export const updateRiskFactors = (id: number, likelihood: number, impact: number) =>
  request<RiskItem>(`/risks/${id}`, { method: "PUT", body: JSON.stringify({ likelihood, impact }) });
export const updateRiskAssociations = (id: number, threat_ids: number[], vulnerability_ids: number[]) =>
  request<RiskItem>(`/risks/${id}/associations`, { method: "PUT", body: JSON.stringify({ threat_ids, vulnerability_ids }) });

export const getRiskThreats = () => request<RiskCatalogItem[]>("/risks/threats");
export const createRiskThreat = (payload: { code: string; name: string; category: string; description?: string }) =>
  request<RiskCatalogItem>("/risks/threats", { method: "POST", body: JSON.stringify(payload) });
export const getRiskVulnerabilities = () => request<RiskCatalogItem[]>("/risks/vulnerabilities");
export const createRiskVulnerability = (payload: { code: string; name: string; category: string; description?: string }) =>
  request<RiskCatalogItem>("/risks/vulnerabilities", { method: "POST", body: JSON.stringify(payload) });

export const getRiskHeatmap = (clientId?: number) =>
  request<HeatmapCell[]>(`/risks/heatmap${clientId ? `?client_id=${clientId}` : ""}`);
