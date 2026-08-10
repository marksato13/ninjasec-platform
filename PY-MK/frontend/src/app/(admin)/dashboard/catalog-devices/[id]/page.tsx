"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, Plus, Trash2 } from "lucide-react";

import {
  addCatalogDeviceLink,
  CatalogDeviceDetail,
  deleteCatalogDeviceLink,
  getCatalogDevice,
  upsertCatalogDeviceSummary,
} from "@/lib/api";
import { confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";

const LINK_TYPES = ["datasheet", "config_manual", "firmware", "eol_notice", "security_advisory"];

const LINK_TYPE_LABEL: Record<string, string> = {
  datasheet: "Datasheet",
  config_manual: "Manual de configuración",
  firmware: "Firmware",
  eol_notice: "Aviso de EOL",
  security_advisory: "Aviso de seguridad",
};

const LIFECYCLE_LABEL: Record<string, string> = {
  active: "Activo",
  eos: "Fin de venta",
  eol: "Fin de vida",
};

export default function CatalogDeviceDetailPage() {
  const params = useParams<{ id: string }>();
  const deviceId = Number(params.id);
  const currentUser = getStoredUser();
  const isAdmin = currentUser?.role === "super_admin" || currentUser?.role === "admin";
  const canEditSummary = isAdmin || currentUser?.role === "collaborator";
  const queryClient = useQueryClient();

  const [linkForm, setLinkForm] = useState({ link_type: "datasheet", url: "" });
  const [savingLink, setSavingLink] = useState(false);
  const [summaryDraft, setSummaryDraft] = useState<string | null>(null);
  const [sourceNoteDraft, setSourceNoteDraft] = useState<string | null>(null);
  const [savingSummary, setSavingSummary] = useState(false);

  const { data: device, isLoading } = useQuery<CatalogDeviceDetail>({
    queryKey: QK.catalogDevice(deviceId),
    queryFn: () => getCatalogDevice(deviceId),
  });

  function reload() {
    queryClient.invalidateQueries({ queryKey: QK.catalogDevice(deviceId) });
  }

  async function handleAddLink() {
    if (!linkForm.url) return;
    setSavingLink(true);
    try {
      await addCatalogDeviceLink(deviceId, linkForm);
      setLinkForm({ link_type: "datasheet", url: "" });
      notifySuccess("Enlace agregado");
      reload();
    } catch (err) {
      notifyError("No se pudo agregar el enlace", err instanceof Error ? err.message : undefined);
    } finally {
      setSavingLink(false);
    }
  }

  async function handleDeleteLink(linkId: number) {
    const confirmed = await confirmDelete({ title: "¿Eliminar este enlace?", text: "El enlace deja de estar disponible en la ficha del modelo." });
    if (!confirmed) return;
    try {
      await deleteCatalogDeviceLink(deviceId, linkId);
      notifySuccess("Enlace eliminado");
      reload();
    } catch (err) {
      notifyError("No se pudo eliminar el enlace", err instanceof Error ? err.message : undefined);
    }
  }

  async function handleSaveSummary() {
    if (summaryDraft === null || !summaryDraft.trim()) {
      notifyError("El resumen no puede estar vacío");
      return;
    }
    setSavingSummary(true);
    try {
      await upsertCatalogDeviceSummary(deviceId, { content: summaryDraft, source_note: sourceNoteDraft || null });
      notifySuccess("Resumen guardado");
      setSummaryDraft(null);
      setSourceNoteDraft(null);
      reload();
    } catch (err) {
      notifyError("No se pudo guardar el resumen", err instanceof Error ? err.message : undefined);
    } finally {
      setSavingSummary(false);
    }
  }

  if (isLoading) return <div className="empty-state">Cargando ficha...</div>;
  if (!device) return <div className="empty-state">Modelo no encontrado.</div>;

  const editingSummary = summaryDraft !== null;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">{device.brand}</p>
          <h2>{device.model}</h2>
        </div>
        <span className="muted-small">{LIFECYCLE_LABEL[device.lifecycle_status] ?? device.lifecycle_status}</span>
      </div>

      <div className="content-grid">
        <article className="panel">
          <div className="panel-head"><div><p className="eyebrow">Especificaciones</p><h3>Ficha técnica</h3></div></div>
          <div className="card-meta">
            <div><span className="card-label">Categoría</span><span>{device.category}{device.subcategory ? ` · ${device.subcategory}` : ""}</span></div>
            {device.osi_layer ? <div><span className="card-label">Capa OSI</span><span>{device.osi_layer}</span></div> : null}
            {device.segment ? <div><span className="card-label">Segmento</span><span>{device.segment}</span></div> : null}
            {device.port_count ? <div><span className="card-label">Puertos</span><span>{device.port_count} · {device.port_speed}</span></div> : null}
            {device.poe ? <div><span className="card-label">PoE</span><span>{device.poe_budget_w ? `${device.poe_budget_w}W de presupuesto` : "Sí"}</span></div> : null}
            <div><span className="card-label">Apilable</span><span>{device.stackable ? "Sí" : "No"}</span></div>
            <div><span className="card-label">Montaje en rack</span><span>{device.rack_mountable ? "Sí" : "No"}</span></div>
            <div><span className="card-label">Gestionable</span><span>{device.managed ? "Sí" : "No"}</span></div>
            {device.switching_capacity_gbps ? <div><span className="card-label">Capacidad de switching</span><span>{device.switching_capacity_gbps} Gbps</span></div> : null}
            {device.throughput_mbps ? <div><span className="card-label">Throughput</span><span>{device.throughput_mbps} Mbps</span></div> : null}
            {device.power_consumption_w ? <div><span className="card-label">Consumo</span><span>{device.power_consumption_w} W</span></div> : null}
            {device.price_range_usd ? <div><span className="card-label">Precio referencial</span><span>USD {device.price_range_usd}</span></div> : null}
            {device.eos_date ? <div><span className="card-label">Fin de venta</span><span>{device.eos_date}</span></div> : null}
            {device.eol_date ? <div><span className="card-label">Fin de vida</span><span>{device.eol_date}</span></div> : null}
          </div>
          {device.use_cases ? <p className="muted-small" style={{ marginTop: 12 }}><strong>Casos de uso:</strong> {device.use_cases}</p> : null}
        </article>

        <article className="panel">
          <div className="panel-head"><div><p className="eyebrow">Parque instalado</p><h3>Instancias en tu organización</h3></div></div>
          <div style={{ textAlign: "center", padding: "12px 0" }}>
            <strong style={{ fontSize: "2.4rem" }}>{device.instance_count}</strong>
            <p className="muted-small">dispositivo{device.instance_count !== 1 ? "s" : ""} registrado{device.instance_count !== 1 ? "s" : ""} con esta marca y modelo</p>
          </div>
          <p className="muted-small">
            Cruce por texto (marca/modelo del inventario), no por vínculo directo — dos dispositivos con el mismo
            fabricante y modelo escritos distinto no se contarán juntos.
          </p>
        </article>
      </div>

      <article className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Documentación</p><h3>Enlaces oficiales</h3></div>
        </div>
        {device.links.length === 0 ? (
          <div className="empty-state">Sin enlaces registrados.</div>
        ) : (
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "1fr 2fr auto" }}>
              <span>Tipo</span><span>URL</span><span>Acciones</span>
            </div>
            {device.links.map((link) => (
              <div className="table-row" key={link.id} style={{ gridTemplateColumns: "1fr 2fr auto", alignItems: "center" }}>
                <span>{LINK_TYPE_LABEL[link.link_type] ?? link.link_type}</span>
                <span>
                  <a className="link-inline" href={link.url} target="_blank" rel="noreferrer">
                    {link.url} <ExternalLink size={12} />
                  </a>
                </span>
                <span className="table-actions">
                  {isAdmin && (
                    <button className="button button-ghost button-sm" type="button" onClick={() => handleDeleteLink(link.id)}>
                      <Trash2 size={14} />
                    </button>
                  )}
                </span>
              </div>
            ))}
          </div>
        )}
        {isAdmin && (
          <div className="entity-form" style={{ marginTop: 12 }}>
            <select value={linkForm.link_type} onChange={(e) => setLinkForm((f) => ({ ...f, link_type: e.target.value }))}>
              {LINK_TYPES.map((t) => <option key={t} value={t}>{LINK_TYPE_LABEL[t]}</option>)}
            </select>
            <input
              placeholder="URL oficial del fabricante"
              value={linkForm.url}
              onChange={(e) => setLinkForm((f) => ({ ...f, url: e.target.value }))}
            />
            <button className="button button-secondary" type="button" onClick={handleAddLink} disabled={savingLink || !linkForm.url}>
              <Plus size={14} /> Agregar enlace
            </button>
          </div>
        )}
      </article>

      <article className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Resumen ejecutivo</p><h3>Elaboración propia</h3></div>
          {canEditSummary && !editingSummary && (
            <button
              className="button button-secondary"
              type="button"
              onClick={() => {
                setSummaryDraft(device.summary?.content ?? "");
                setSourceNoteDraft(device.summary?.source_note ?? "");
              }}
            >
              {device.summary ? "Editar" : "Redactar resumen"}
            </button>
          )}
        </div>
        {editingSummary ? (
          <div className="entity-form">
            <textarea
              rows={5}
              value={summaryDraft ?? ""}
              onChange={(e) => setSummaryDraft(e.target.value)}
              placeholder="Specs clave, valoración práctica, problemas conocidos, compatibilidades..."
            />
            <input
              placeholder="Fuente (ej. Datasheet oficial Cisco, 2026)"
              value={sourceNoteDraft ?? ""}
              onChange={(e) => setSourceNoteDraft(e.target.value)}
            />
            <div className="panel-actions">
              <button className="button button-primary" type="button" onClick={handleSaveSummary} disabled={savingSummary}>
                {savingSummary ? "Guardando..." : "Guardar resumen"}
              </button>
              <button className="button button-ghost" type="button" onClick={() => { setSummaryDraft(null); setSourceNoteDraft(null); }}>
                Cancelar
              </button>
            </div>
          </div>
        ) : device.summary ? (
          <>
            <p>{device.summary.content}</p>
            {device.summary.source_note ? <p className="muted-small">Fuente: {device.summary.source_note}</p> : null}
          </>
        ) : (
          <div className="empty-state">Sin resumen ejecutivo todavía.</div>
        )}
      </article>
    </section>
  );
}
