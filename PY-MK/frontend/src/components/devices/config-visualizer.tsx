"use client";

import { useRef, useState } from "react";
import { AlertTriangle, FileWarning, ShieldAlert, UploadCloud } from "lucide-react";

import { CandidateConnection, DeviceItem, createConnection, deduceConnections, saveDeviceConfig } from "@/lib/api";
import { notifyError, notifySuccess, notifyWarning } from "@/lib/alerts";
import { Modal } from "@/components/ui/modal";
import {
  detectVendor,
  hygieneAlerts,
  parseCiscoIOS,
  ParseResult,
  summarizeConfig,
  SUPPORTED_COMMANDS,
} from "@/lib/config-parser";
import {
  downloadTopologyDrawio,
  downloadTopologyPdf,
  downloadTopologyPng,
  downloadTopologySvg,
} from "@/lib/topology-export";

type Props = { devices: DeviceItem[]; clientId?: number };

export function ConfigVisualizer({ devices, clientId }: Props) {
  const [deviceId, setDeviceId] = useState("");
  const [fileName, setFileName] = useState("");
  const [rawText, setRawText] = useState<string | null>(null);
  const [result, setResult] = useState<ParseResult | null>(null);
  const [rejected, setRejected] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [wantsToSaveRaw, setWantsToSaveRaw] = useState(false);
  const [candidates, setCandidates] = useState<CandidateConnection[] | null>(null);
  const [selectedCandidates, setSelectedCandidates] = useState<Set<number>>(new Set());
  const [deducing, setDeducing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFile(file: File) {
    setFileName(file.name);
    setResult(null);
    setRejected(null);
    setCandidates(null);
    setSelectedCandidates(new Set());
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? "");
      setRawText(text);
      const vendor = detectVendor(text);
      if (vendor !== "cisco_ios") {
        const label = vendor === "unsupported" ? "un formato no reconocido" : vendor;
        setRejected(
          `Este archivo parece ser de ${label}. Por ahora el parser solo soporta Cisco IOS — no se interpretó a medias.`
        );
        return;
      }
      setResult(parseCiscoIOS(text));
    };
    reader.onerror = () => notifyError("No se pudo leer el archivo");
    reader.readAsText(file);
  }

  async function handleDeduce() {
    if (!result || !deviceId) return;
    setDeducing(true);
    try {
      const found = await deduceConnections(Number(deviceId), {
        interfaces: result.interfaces.map((i) => ({ name: i.name, ip_address: i.ipAddress, subnet_mask: i.subnetMask })),
        static_routes: result.staticRoutes.map((r) => ({ destination: r.destination, mask: r.mask, next_hop: r.nextHop })),
      });
      setCandidates(found);
      setSelectedCandidates(new Set(found.map((c) => c.target_device_id)));
      if (found.length === 0) notifyWarning("No se dedujeron conexiones", "No hay coincidencias de subred o next-hop con otros dispositivos del cliente.");
    } catch (err) {
      notifyError("No se pudo deducir la topología", err instanceof Error ? err.message : undefined);
    } finally {
      setDeducing(false);
    }
  }

  function toggleCandidate(targetId: number) {
    setSelectedCandidates((old) => {
      const next = new Set(old);
      if (next.has(targetId)) next.delete(targetId); else next.add(targetId);
      return next;
    });
  }

  async function handleApply() {
    if (!candidates || !deviceId) return;
    setApplying(true);
    let created = 0;
    let failed = 0;
    try {
      for (const candidate of candidates) {
        if (!selectedCandidates.has(candidate.target_device_id)) continue;
        try {
          await createConnection({
            source_device_id: Number(deviceId),
            target_device_id: candidate.target_device_id,
            link_type: candidate.link_type_guess,
          });
          created += 1;
        } catch {
          failed += 1;
        }
      }
      if (created) notifySuccess(`${created} conexión${created === 1 ? "" : "es"} creada${created === 1 ? "" : "s"}`);
      if (failed) notifyWarning(`${failed} no se pudieron crear`, "Puede que ya existieran.");
      setCandidates(null);
    } finally {
      setApplying(false);
    }
  }

  async function handleExport(format: "svg" | "png" | "pdf" | "drawio") {
    if (!clientId) return;
    setExporting(format);
    try {
      if (format === "svg") await downloadTopologySvg(clientId);
      else if (format === "png") await downloadTopologyPng(clientId);
      else if (format === "drawio") await downloadTopologyDrawio(clientId);
      else await downloadTopologyPdf(clientId);
    } catch (err) {
      notifyError("No se pudo exportar", err instanceof Error ? err.message : undefined);
    } finally {
      setExporting(null);
    }
  }

  async function handleSave() {
    if (!result || !deviceId) return;
    setSaving(true);
    try {
      await saveDeviceConfig({
        device_id: Number(deviceId),
        vendor_detected: result.vendor,
        parsed_json: JSON.stringify(result),
        parse_warnings: result.warnings.length ? JSON.stringify(result.warnings) : null,
        raw_config: wantsToSaveRaw ? rawText : null,
      });
      notifySuccess("Configuración guardada");
    } catch (err) {
      notifyError("No se pudo guardar", err instanceof Error ? err.message : undefined);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page-stack">
      <article className="panel filters-panel">
        <p className="eyebrow">Config Visualizer</p>
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: 12 }}>
          Sube un <code>running-config</code> de Cisco IOS. El parseo ocurre en tu navegador —
          el archivo no se envía al servidor salvo que decidas guardarlo abajo.
        </p>
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <select value={deviceId} onChange={(e) => setDeviceId(e.target.value)}>
            <option value="">Asociar a un dispositivo (opcional para solo visualizar)</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>{d.hostname}</option>
            ))}
          </select>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.cfg,.conf"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
          <button type="button" className="button-secondary" onClick={() => fileInputRef.current?.click()}>
            <UploadCloud size={16} /> {fileName || "Elegir archivo"}
          </button>
        </div>
      </article>

      {rejected && (
        <article className="panel" style={{ borderColor: "var(--danger)" }}>
          <p style={{ display: "flex", gap: 8, alignItems: "center", color: "var(--danger)" }}>
            <AlertTriangle size={18} /> {rejected}
          </p>
        </article>
      )}

      {result && (
        <>
          <article className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Resumen</p>
                <h3 style={{ fontWeight: 500, fontSize: "0.95rem" }}>{summarizeConfig(result)}</h3>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {deviceId && (
                  <button type="button" className="button-secondary" disabled={deducing} onClick={handleDeduce}>
                    {deducing ? "Analizando…" : "Aplicar a la topología"}
                  </button>
                )}
                {deviceId && (
                  <button type="button" className="button-primary" disabled={saving} onClick={handleSave}>
                    {saving ? "Guardando…" : "Guardar en el dispositivo"}
                  </button>
                )}
              </div>
            </div>
            {deviceId && (
              <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.8rem", color: "var(--muted)" }}>
                <input type="checkbox" checked={wantsToSaveRaw} onChange={(e) => setWantsToSaveRaw(e.target.checked)} />
                Guardar también el archivo original (texto sin procesar)
              </label>
            )}
          </article>

          {hygieneAlerts(result).length > 0 && (
            <article className="panel" style={{ borderColor: "var(--warning)" }}>
              <p className="eyebrow" style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <ShieldAlert size={16} /> Alertas de higiene ({hygieneAlerts(result).length})
              </p>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.82rem" }}>
                {hygieneAlerts(result).map((a, i) => <li key={i}>{a.message}</li>)}
              </ul>
            </article>
          )}

          {result.warnings.length > 0 && (
            <article className="panel" style={{ borderColor: "var(--warning)" }}>
              <p className="eyebrow" style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <FileWarning size={16} /> Sintaxis no reconocida ({result.warnings.length})
              </p>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.82rem", color: "var(--muted)" }}>
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </article>
          )}

          <article className="panel">
            <p className="eyebrow">Interfaces</p>
            <div className="table-like">
              <div className="table-row table-head" style={{ gridTemplateColumns: "1.2fr 1fr 1fr 1fr 1.5fr" }}>
                <span>Interfaz</span><span>Modo</span><span>VLAN</span><span>IP</span><span>Descripción</span>
              </div>
              {result.interfaces.map((iface) => (
                <div className="table-row" key={iface.name} style={{ gridTemplateColumns: "1.2fr 1fr 1fr 1fr 1.5fr" }}>
                  <span style={{ fontWeight: 600 }}>{iface.name}</span>
                  <span>
                    <span className={`badge ${iface.adminStatus === "down" ? "badge-archived" : "badge-active"}`}>
                      {iface.mode ?? "sin definir"} · {iface.adminStatus === "down" ? "apagada" : "activa"}
                    </span>
                  </span>
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {iface.mode === "trunk"
                      ? `troncal${iface.nativeVlan ? ` (nativa ${iface.nativeVlan})` : ""}${iface.allowedVlans ? `: ${iface.allowedVlans}` : ""}`
                      : iface.accessVlan ?? "—"}
                  </span>
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                    {iface.ipAddress ? `${iface.ipAddress} / ${iface.subnetMask}` : "—"}
                  </span>
                  <span style={{ fontSize: "0.82rem", color: "var(--muted)" }}>{iface.description ?? "—"}</span>
                </div>
              ))}
              {result.interfaces.length === 0 && (
                <div className="empty-state">No se detectaron interfaces en este archivo.</div>
              )}
            </div>
          </article>

          {(result.vlans.length > 0 || result.staticRoutes.length > 0) && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <article className="panel">
                <p className="eyebrow">VLANs</p>
                {result.vlans.length === 0 ? (
                  <div className="empty-state">Sin VLANs declaradas a nivel global.</div>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.85rem" }}>
                    {result.vlans.map((v) => <li key={v.id}>VLAN {v.id}{v.name ? ` — ${v.name}` : ""}</li>)}
                  </ul>
                )}
              </article>
              <article className="panel">
                <p className="eyebrow">Rutas estáticas</p>
                {result.staticRoutes.length === 0 ? (
                  <div className="empty-state">Sin rutas estáticas.</div>
                ) : (
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.85rem" }}>
                    {result.staticRoutes.map((r, i) => (
                      <li key={i}>{r.destination}/{r.mask} → {r.nextHop}</li>
                    ))}
                  </ul>
                )}
              </article>
            </div>
          )}
        </>
      )}

      {clientId && (
        <article className="panel">
          <p className="eyebrow">Exportar diagrama de topología</p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button type="button" className="button-secondary" disabled={exporting === "svg"} onClick={() => handleExport("svg")}>{exporting === "svg" ? "Exportando…" : "SVG"}</button>
            <button type="button" className="button-secondary" disabled={exporting === "png"} onClick={() => handleExport("png")}>{exporting === "png" ? "Exportando…" : "PNG"}</button>
            <button type="button" className="button-secondary" disabled={exporting === "pdf"} onClick={() => handleExport("pdf")}>{exporting === "pdf" ? "Exportando…" : "PDF"}</button>
            <button type="button" className="button-secondary" disabled={exporting === "drawio"} onClick={() => handleExport("drawio")}>{exporting === "drawio" ? "Exportando…" : "drawio"}</button>
          </div>
        </article>
      )}

      <article className="panel" style={{ opacity: 0.75 }}>
        <p className="eyebrow">Comandos soportados</p>
        <p style={{ fontSize: "0.78rem", color: "var(--muted)" }}>
          Solo Cisco IOS. Sintaxis fuera de esta lista dentro de un bloque <code>interface</code> o{" "}
          <code>vlan</code> queda registrada arriba como advertencia; el resto del archivo (aaa, crypto,
          ntp, banners, ACLs, líneas con/vty, etc.) está fuera de alcance y se ignora sin interpretarlo.
        </p>
        <ul style={{ margin: "8px 0 0", paddingLeft: 20, fontSize: "0.78rem", color: "var(--muted)" }}>
          {SUPPORTED_COMMANDS.map((c) => <li key={c}><code>{c}</code></li>)}
        </ul>
      </article>

      <Modal
        isOpen={candidates !== null}
        title="Conexiones deducidas del parseo"
        onClose={() => setCandidates(null)}
        footer={
          <button type="button" className="button-primary" disabled={applying || selectedCandidates.size === 0} onClick={handleApply}>
            {applying ? "Aplicando…" : `Crear ${selectedCandidates.size} conexión${selectedCandidates.size === 1 ? "" : "es"}`}
          </button>
        }
      >
        <p style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: 12 }}>
          Deducidas por coincidencia de subred o next-hop de ruta estática contra los demás dispositivos
          de este cliente. No hay descubrimiento de vecinos (CDP/LLDP) — revisa cada una antes de confirmar.
        </p>
        {candidates && candidates.length === 0 && <p>No se encontraron candidatos.</p>}
        {candidates?.map((c) => (
          <label key={c.target_device_id} style={{ display: "flex", gap: 10, alignItems: "flex-start", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
            <input type="checkbox" checked={selectedCandidates.has(c.target_device_id)} onChange={() => toggleCandidate(c.target_device_id)} style={{ marginTop: 3 }} />
            <span>
              <strong>{c.target_hostname}</strong>
              <br />
              <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{c.reason}</span>
            </span>
          </label>
        ))}
      </Modal>
    </div>
  );
}
