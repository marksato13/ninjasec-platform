"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getClients, getHealthScore, downloadHealthScorePdf } from "@/lib/api";
import { notifyError } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

const LABEL_COLOR: Record<string, string> = { "Saludable": "#10b981", "Con observaciones": "#f59e0b", "Requiere atención": "#dc2626" };

export default function SocReportPage() {
  const [clientId, setClientId] = useState<number | "">("");
  const [exporting, setExporting] = useState(false);
  const { data: clients = [] } = useQuery({ queryKey: QK.clients(), queryFn: getClients });
  const activeClientId = clientId === "" ? undefined : clientId;

  const { data: score, isLoading } = useQuery({
    queryKey: QK.healthScore(activeClientId),
    queryFn: () => getHealthScore(activeClientId as number),
    enabled: activeClientId !== undefined,
  });

  async function handleExport() {
    if (!activeClientId) return;
    setExporting(true);
    try {
      await downloadHealthScorePdf(activeClientId, `salud_seguridad_${activeClientId}.pdf`);
    } catch (err) {
      notifyError("No se pudo exportar", err instanceof Error ? err.message : undefined);
    } finally {
      setExporting(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="flex items-center justify-between">
        <h2>Informe ejecutivo — salud de seguridad</h2>
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
        Índice 0-100 en lenguaje ejecutivo, no técnico — combina hallazgos de revisiones abiertos, reglas de
        hardening incumplidas (31-P1), hosts de alto riesgo (30-P2) y CVEs de alta probabilidad de explotación
        (32-P1). Cada categoría tiene un tope de deducción para que ninguna señal por sí sola hunda el score.
      </p>

      {!activeClientId && <p>Selecciona un cliente para ver su índice de salud.</p>}
      {isLoading && <p>Cargando…</p>}

      {score && (
        <>
          <div className="panel" style={{ textAlign: "center", padding: "32px" }}>
            <div style={{ fontSize: "4rem", fontWeight: 800, color: LABEL_COLOR[score.label] ?? "#64748b" }}>{score.score}</div>
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: LABEL_COLOR[score.label] ?? "#64748b" }}>{score.label}</div>
            <p style={{ marginTop: 12, maxWidth: 560, marginLeft: "auto", marginRight: "auto" }}>{score.narrative}</p>
          </div>

          <div className="panel overflow-x-auto">
            <h3>¿Cómo se calcula?</h3>
            <div className="table-like">
              <div className="table-row table-head" style={{ gridTemplateColumns: "3fr 1fr 1fr" }}>
                <span>Categoría</span><span>Cantidad</span><span>Puntos restados</span>
              </div>
              {score.breakdown.map((item) => (
                <div className="table-row" key={item.category} style={{ gridTemplateColumns: "3fr 1fr 1fr" }}>
                  <span>{item.category}</span>
                  <span>{item.count}</span>
                  <span style={{ color: item.deduction > 0 ? "#dc2626" : "var(--muted)" }}>-{item.deduction}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
