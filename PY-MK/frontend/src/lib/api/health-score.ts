import { downloadFile, request } from "./client";

export type HealthScoreBreakdownItem = { category: string; count: number; deduction: number };

export type HealthScore = {
  client_id: number;
  client_name: string;
  score: number;
  label: string;
  narrative: string;
  breakdown: HealthScoreBreakdownItem[];
};

export const getHealthScore = (clientId: number) => request<HealthScore>(`/health-score?client_id=${clientId}`);
export const downloadHealthScorePdf = (clientId: number, filename = "salud_seguridad.pdf") =>
  downloadFile(`/health-score/export/pdf?client_id=${clientId}`, filename);
