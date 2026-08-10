"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { RuleEvaluation, downloadHardeningPdf, evaluateHardening, getClients, getHardeningSummary } from "@/lib/api";
import { notifyError } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

const RESULT_LABEL: Record<string, string> = { pass: "Cumple", fail: "No cumple", manual: "Manual", not_applicable: "No aplica" };
const RESULT_COLOR: Record<string, string> = { pass: "#bbf7d0", fail: "#fecaca", manual: "#e2e8f0", not_applicable: "#f1f5f9" };

export default function HardeningPage() {
  const [clientId, setClientId] = useState<number | "">("");
  const [exporting, setExporting] = useState(false);
  const { data: clients = [] } = useQuery({ queryKey: QK.clients(), queryFn: getClients });
  const activeClientId = clientId === "" ? undefined : clientId;

  const { data: evaluations = [], isLoading } = useQuery({
    queryKey: QK.hardeningEval(activeClientId),
    queryFn: () => evaluateHardening(activeClientId as number),
    enabled: activeClientId !== undefined,
  });
  const { data: summary } = useQuery({
    queryKey: QK.hardeningSummary(activeClientId),
    queryFn: () => getHardeningSummary(activeClientId as number),
    enabled: activeClientId !== undefined,
  });

  async function handleExport() {
    if (!activeClientId) return;
    setExporting(true);
    try {
      await downloadHardeningPdf(activeClientId, `gap_analysis_${activeClientId}.pdf`);
    } catch (err) {
      notifyError("No se pudo exportar", err instanceof Error ? err.message : undefined);
    } finally {
      setExporting(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="flex items-center justify-between">
        <h2>Hardening técnico (31-P1)</h2>
        <div style={{ display: "flex", gap: 12 }}>
          <select className="input w-64" value={clientId} onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Seleccionar cliente</option>
            {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
          </select>
          {activeClientId && (
            <button type="button" className="button button-secondary" disabled={exporting} onClick={handleExport}>
              {exporting ? "Exportando…" : "Exportar PDF"}
            </button>
          )}
        </div>
      </div>

      <p style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
        Verificación técnica automática cruzando integraciones y eventos reales del cliente (30-P1) contra un catálogo
        de reglas estilo CIS Benchmarks. No confundir con el módulo 24 (Declaración de Aplicabilidad ISO 27001,
        manual) — se complementan.
      </p>

      {!activeClientId && <p>Selecciona un cliente para ver su gap analysis.</p>}

      {summary && (
        <div className="marketing-grid marketing-grid--three">
          <div className="panel"><p className="eyebrow">Cumplimiento verificable</p><h3>{summary.compliance_percent}%</h3></div>
          <div className="panel"><p className="eyebrow">Reglas evaluadas</p><h3>{summary.passed} cumple / {summary.failed} no cumple</h3></div>
          <div className="panel"><p className="eyebrow">Requieren verificación manual</p><h3>{summary.manual} · {summary.not_applicable} no aplican</h3></div>
        </div>
      )}

      {isLoading && activeClientId && <p>Cargando…</p>}

      {evaluations.length > 0 && (
        <div className="panel overflow-x-auto">
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "0.8fr 2fr 1fr 1fr 3fr" }}>
              <span>Código</span><span>Regla</span><span>Categoría</span><span>Resultado</span><span>Evidencia</span>
            </div>
            {evaluations.map((evaluation: RuleEvaluation) => (
              <div className="table-row" key={evaluation.rule.id} style={{ gridTemplateColumns: "0.8fr 2fr 1fr 1fr 3fr" }}>
                <span style={{ fontWeight: 600 }}>{evaluation.rule.code}</span>
                <span>{evaluation.rule.title}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{evaluation.rule.category}</span>
                <span className="badge" style={{ background: RESULT_COLOR[evaluation.result] }}>{RESULT_LABEL[evaluation.result]}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{evaluation.evidence}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
