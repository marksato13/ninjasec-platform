"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { GuidedTree, NetdoctorIssue, getGuidedTree, getNetdoctorIssues } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { getSeverityLabel } from "@/lib/labels";

const VENDORS = [
  { value: "cisco_ios", label: "Cisco IOS" },
  { value: "mikrotik", label: "MikroTik" },
  { value: "huawei", label: "Huawei" },
  { value: "ubiquiti", label: "Ubiquiti" },
];

const SEVERITY_COLOR: Record<string, string> = { critical: "#fecaca", high: "#fed7aa", medium: "#fef08a", low: "#bbf7d0" };

function IssueCard({ issue, vendor }: { issue: NetdoctorIssue; vendor: string }) {
  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">{issue.category} · {issue.code}</p>
          <h3>{issue.title}</h3>
        </div>
        <span className="badge" style={{ background: SEVERITY_COLOR[issue.severity] ?? "#e2e8f0" }}>{getSeverityLabel(issue.severity)}</span>
      </div>
      <p style={{ fontSize: "0.85rem" }}><strong>Síntomas:</strong> {issue.symptoms}</p>
      <p style={{ fontSize: "0.85rem" }}><strong>Causas probables:</strong> {issue.probable_causes}</p>
      <p style={{ fontSize: "0.85rem" }}>
        <strong>Comando de diagnóstico ({VENDORS.find((v) => v.value === vendor)?.label ?? vendor}):</strong>{" "}
        <code>{issue.diagnostic_commands[vendor] ?? "No disponible para este vendor"}</code>
      </p>
      <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}><strong>Remediación:</strong> {issue.remediation}</p>
    </article>
  );
}

function GuidedWizard({ tree, vendor }: { tree: GuidedTree; vendor: string }) {
  const [nodeId, setNodeId] = useState("start");
  const [history, setHistory] = useState<string[]>([]);
  const { data: issues = [] } = useQuery({ queryKey: QK.netdoctorIssues(), queryFn: () => getNetdoctorIssues() });
  const node = tree[nodeId];
  const matchedIssue = node?.issue_code ? issues.find((i) => i.code === node.issue_code) : undefined;

  function choose(next: string) {
    setHistory((h) => [...h, nodeId]);
    setNodeId(next);
  }
  function restart() {
    setHistory([]);
    setNodeId("start");
  }
  function back() {
    const prev = history[history.length - 1];
    if (prev) {
      setHistory((h) => h.slice(0, -1));
      setNodeId(prev);
    }
  }

  if (!node) return null;

  return (
    <div className="panel">
      <p className="eyebrow">Modo guiado</p>
      {node.question && (
        <>
          <h3>{node.question}</h3>
          <div className="hero-actions">
            {node.options?.map((option) => (
              <button key={option.label} type="button" className="button button-secondary" onClick={() => choose(option.next)}>
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
      {matchedIssue && <IssueCard issue={matchedIssue} vendor={vendor} />}
      <div className="hero-actions" style={{ marginTop: 12 }}>
        {history.length > 0 && <button type="button" className="button button-ghost" onClick={back}>← Atrás</button>}
        <button type="button" className="button button-ghost" onClick={restart}>Reiniciar</button>
      </div>
    </div>
  );
}

export default function NetdoctorPage() {
  const [mode, setMode] = useState<"catalog" | "guided">("guided");
  const [vendor, setVendor] = useState("cisco_ios");
  const [category, setCategory] = useState("");

  const { data: issues = [] } = useQuery({ queryKey: QK.netdoctorIssues(category), queryFn: () => getNetdoctorIssues({ category: category || undefined }) });
  const { data: tree } = useQuery({ queryKey: QK.netdoctorTree(), queryFn: getGuidedTree });
  const categories = useMemo(() => Array.from(new Set(issues.map((i) => i.category))).sort(), [issues]);

  return (
    <section className="page-stack">
      <div className="flex items-center justify-between">
        <h2>NetDoctor — diagnóstico multi-vendor</h2>
        <div style={{ display: "flex", gap: 12 }}>
          <select className="input" value={vendor} onChange={(e) => setVendor(e.target.value)}>
            {VENDORS.map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
          </select>
          <button type="button" className={`button ${mode === "guided" ? "button-primary" : "button-secondary"}`} onClick={() => setMode("guided")}>Modo guiado</button>
          <button type="button" className={`button ${mode === "catalog" ? "button-primary" : "button-secondary"}`} onClick={() => setMode("catalog")}>Catálogo</button>
        </div>
      </div>

      <p className="muted-small">
        Sin conexión SSH real — el comando se muestra como texto para ejecutarlo manualmente. La conexión directa a
        dispositivos (28-P3) requiere credenciales cifradas y autorización escrita del cliente, todavía no implementada.
      </p>

      {mode === "guided" && tree && <GuidedWizard tree={tree} vendor={vendor} />}

      {mode === "catalog" && (
        <>
          <select className="input w-64" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Todas las categorías</option>
            {categories.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          {issues.map((issue) => <IssueCard key={issue.code} issue={issue} vendor={vendor} />)}
        </>
      )}
    </section>
  );
}
