"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DeviceCveEntry, getClients, getDeviceCves } from "@/lib/api";
import { QK } from "@/lib/query-keys";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#fecaca", high: "#fed7aa", medium: "#fef08a", low: "#bbf7d0", unknown: "#e2e8f0",
};

function epssBadge(score: number) {
  if (score >= 0.5) return "#fecaca";
  if (score >= 0.1) return "#fed7aa";
  if (score > 0) return "#fef08a";
  return "#e2e8f0";
}

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
      <div className="flex items-center justify-between">
        <h2>Inventario de vulnerabilidades (CVE + EPSS)</h2>
        <select className="input w-64" value={clientId} onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Seleccionar cliente</option>
          {clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}
        </select>
      </div>

      <p style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
        Cruza el vendor/modelo de cada dispositivo con CVEs conocidos (CIRCL) y los prioriza por EPSS —
        probabilidad real de explotación (FIRST.org) — en vez de solo por severidad CVSS. Un CVE con CVSS
        alto pero EPSS bajo puede quedar por debajo de uno con CVSS medio pero EPSS alto.
      </p>

      {!activeClientId && <p>Selecciona un cliente para ver su inventario de vulnerabilidades.</p>}
      {isLoading && <p>Cargando…</p>}
      {activeClientId && !isLoading && devices.length === 0 && <p>Sin CVEs conocidos para los dispositivos de este cliente.</p>}

      {devices.map((device: DeviceCveEntry) => (
        <div className="panel overflow-x-auto" key={device.device_id}>
          <h3>{device.hostname} <span style={{ fontSize: "0.8rem", color: "var(--muted)", fontWeight: 400 }}>({device.vendor} {device.model})</span></h3>
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "1fr 3fr 0.8fr 0.8fr 0.8fr" }}>
              <span>CVE</span><span>Descripción</span><span>CVSS</span><span>Severidad</span><span>EPSS</span>
            </div>
            {device.cves.map((cve) => (
              <div className="table-row" key={cve.cve_id} style={{ gridTemplateColumns: "1fr 3fr 0.8fr 0.8fr 0.8fr" }}>
                <span style={{ fontWeight: 600 }}>{cve.cve_id}</span>
                <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{cve.description}</span>
                <span>{cve.cvss_score.toFixed(1)}</span>
                <span className="badge" style={{ background: SEVERITY_COLOR[cve.severity] ?? SEVERITY_COLOR.unknown }}>{cve.severity}</span>
                <span className="badge" style={{ background: epssBadge(cve.epss_score) }}>{(cve.epss_score * 100).toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
