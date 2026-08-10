import { request } from "./client";

export type NetdoctorIssue = {
  id: number;
  code: string;
  title: string;
  category: string;
  severity: string;
  symptoms: string;
  probable_causes: string;
  diagnostic_commands: Record<string, string>;
  remediation: string;
};

export type GuidedTreeOption = { label: string; next: string };
export type GuidedTreeNode = { question?: string; options?: GuidedTreeOption[]; issue_code?: string };
export type GuidedTree = Record<string, GuidedTreeNode>;

export const getNetdoctorIssues = (params?: { category?: string; vendor?: string }) => {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.vendor) query.set("vendor", params.vendor);
  const qs = query.toString();
  return request<NetdoctorIssue[]>(`/netdoctor/issues${qs ? `?${qs}` : ""}`);
};

export const getNetdoctorIssue = (code: string) => request<NetdoctorIssue>(`/netdoctor/issues/${code}`);
export const getGuidedTree = () => request<GuidedTree>("/netdoctor/guided-tree");
