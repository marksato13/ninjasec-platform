"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bug, Building2, ShieldCheck } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { DeviceCveEntry, getClients, getDeviceCves } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { getSeverityLabel } from "@/lib/labels";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { cveTone, epssTone } from "@/components/ui/severity";


export default function VulnerabilitiesPage() {
  const [clientId, setClientId] = useState<number | "">("");
  const { data: clients = [] } = useQuery({ queryKey: QK.clients(), queryFn: getClients });
  const activeClientId = clientId === "" ? undefined : clientId;

  const { data: devices = [], isLoading } = useQuery({
    queryKey: QK.deviceCves(activeClientId),
    queryFn: () => getDeviceCves(activeClientId as number),
    enabled: activeClientId !== undefined,
  });

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ninja Sec</p>
          <h2>Inventario de vulnerabilidades</h2>
        </div>
      </div>

      <article className="panel filters-panel">
        <div className="filters-grid" style={{ gridTemplateColumns: "minmax(0, 1fr) minmax(0, 2fr)", marginBottom: 0 }}>
          <label className="form-field">
            <span className="form-label">Cliente</span>
            <select
              className="input"
              value={clientId}
              onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">Elige un cliente</option>
              {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
            </select>
          </label>
          <p className="muted-small" style={{ margin: 0, alignSelf: "center" }}>
            Cruza la marca y el modelo de cada equipo con CVE conocidas (CIRCL) y las ordena por EPSS, la
            probabilidad real de explotación (FIRST.org), no solo por la severidad CVSS.
          </p>
        </div>
      </article>

      {!activeClientId && (
        clients.length === 0 ? (
          <EmptyState
            icon={Building2}
            title="Todavía no hay clientes"
            description="El inventario se arma con los equipos de cada cliente. Registra uno y sus equipos para empezar."
          />
        ) : (
          <EmptyState
            icon={Bug}
            title="Elige un cliente"
            description="Verás sus equipos con las vulnerabilidades conocidas, de la más probable de explotar a la menos."
          />
        )
      )}
      {isLoading && <div className="empty-state">Cargando vulnerabilidades…</div>}
      {activeClientId && !isLoading && devices.length === 0 && (
        <EmptyState
          icon={ShieldCheck}
          title="Sin vulnerabilidades conocidas"
          description="Ningún equipo de este cliente coincide con CVE publicadas. Revisa que marca y modelo estén bien escritos."
        />
      )}

      {devices.map((device: DeviceCveEntry) => (
        <div className="panel" style={{ overflowX: "auto" }} key={device.device_id}>
          <h3>{device.hostname} <span style={{ fontSize: "0.8rem", color: "var(--muted)", fontWeight: 400 }}>({device.vendor} {device.model})</span></h3>
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "1fr 3fr 0.8fr 0.8fr 0.8fr" }}>
              <span>CVE</span><span>Descripción</span><span>CVSS</span><span>Severidad</span><span title="Probabilidad de explotación en 30 días (FIRST.org)">EPSS</span>
            </div>
            {device.cves.map((cve) => (
              <div className="table-row" key={cve.cve_id} style={{ gridTemplateColumns: "1fr 3fr 0.8fr 0.8fr 0.8fr" }}>
                <span style={{ fontWeight: 600 }}>{cve.cve_id}</span>
                <span className="muted-small">{cve.description}</span>
                <span>{cve.cvss_score.toFixed(1)}</span>
                <span><SeverityBadge tone={cveTone(cve.severity)}>{getSeverityLabel(cve.severity)}</SeverityBadge></span>
                <span><SeverityBadge tone={epssTone(cve.epss_score)}>{(cve.epss_score * 100).toFixed(2)} %</SeverityBadge></span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
