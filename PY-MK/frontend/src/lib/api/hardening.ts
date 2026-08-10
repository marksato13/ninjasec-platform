import { request, downloadFile } from "./client";

export type HardeningRule = {
  id: number;
  code: string;
  title: string;
  category: string;
  severity: string;
  description: string;
  verification_method: "auto" | "manual";
};

export type RuleEvaluation = {
  rule: HardeningRule;
  result: "pass" | "fail" | "manual" | "not_applicable";
  evidence: string;
};

export type GapSummary = {
  total: number;
  passed: number;
  failed: number;
  manual: number;
  not_applicable: number;
  compliance_percent: number;
};

export const getHardeningRules = () => request<HardeningRule[]>("/hardening/rules");
export const evaluateHardening = (clientId: number) => request<RuleEvaluation[]>(`/hardening/evaluate?client_id=${clientId}`);
export const getHardeningSummary = (clientId: number) => request<GapSummary>(`/hardening/summary?client_id=${clientId}`);
export const downloadHardeningPdf = (clientId: number, filename = "gap_analysis.pdf") =>
  downloadFile(`/hardening/export/pdf?client_id=${clientId}`, filename);
