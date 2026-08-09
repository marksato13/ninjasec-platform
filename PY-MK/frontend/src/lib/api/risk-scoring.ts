import { request } from "./client";

export type ExternalReputationDetail = { source: string; score: number; category: string };

export type HostScore = {
  ip_address: string;
  internal_alert_count: number;
  internal_score: number;
  external_score: number;
  composite_score: number;
  external_sources: ExternalReputationDetail[];
};

export const getHostScores = (clientId: number) =>
  request<HostScore[]>(`/risk-scoring/hosts?client_id=${clientId}`);
