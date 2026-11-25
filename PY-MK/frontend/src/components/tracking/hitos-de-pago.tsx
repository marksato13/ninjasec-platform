"use client";

import { useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Wallet } from "lucide-react";

import {
  createPaymentMilestone,
  deletePaymentMilestone,
  getPaymentMilestones,
  updatePaymentMilestone,
  type EstadoPago,
  type HitoPago,
  type HitosPago,
  type Moneda,
} from "@/lib/api";
import { confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

const ESTADO: Record<EstadoPago, { label: string; cls: string }> = {
  pending: { label: "Pendiente", cls: "badge-pending" },
  invoiced: { label: "Facturado", cls: "badge-draft" },
  paid: { label: "Pagado", cls: "badge-active" },
};

function dinero(monto: string | number, moneda: string) {
  return new Intl.NumberFormat("es-PE", { style: "currency", currency: moneda }).format(Number(monto));
}

function fecha(iso: string | null) {
  if (!iso) return "Sin fecha";
  // Una fecha sola (AAAA-MM-DD) se lee como local, no como medianoche UTC.
  const [a, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(a, m - 1, d).toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" });
}

/**
 * C3: hitos de pago del proyecto. El cliente los ve; el admin los registra y
 * cambia su estado. Solo estado: no hay pasarela ni datos bancarios.
 * Quien no puede ver pagos (un colaborador) recibe 403 y la sección no aparece.
 */
export function HitosDePago({ projectId }: { projectId: number }) {
  const qc = useQueryClient();
  const clave = QK.paymentMilestones(projectId);
  const consulta = useQuery({
    queryKey: clave,
    queryFn: () => getPaymentMilestones(projectId),
    enabled: Number.isFinite(projectId) && projectId > 0,
    retry: false,
  });
  const [titulo, setTitulo] = useState("");
  const [monto, setMonto] = useState("");
  const [moneda, setMoneda] = useState<Moneda>("PEN");
  const [vence, setVence] = useState("");
  const [nota, setNota] = useState("");
  const [guardando, setGuardando] = useState(false);

  if (consulta.isLoading || consulta.error || !consulta.data) return null;
  const { milestones, totals, can_manage } = consulta.data;
  if (!can_manage && milestones.length === 0) return null;

  const fijar = (vista: HitosPago) => qc.setQueryData(clave, vista);
  const fila = can_manage ? "table-row-5" : "table-row-wide";

  async function crear(e: FormEvent) {
    e.preventDefault();
    setGuardando(true);
    try {
      fijar(await createPaymentMilestone(projectId, {
        title: titulo, amount: monto, currency: moneda, due_date: vence || null, note: nota || null,
      }));
      setTitulo(""); setMonto(""); setVence(""); setNota("");
      notifySuccess("Hito de pago registrado");
    } catch (err) {
      notifyError("No se pudo registrar el hito", err instanceof Error ? err.message : "");
    } finally {
      setGuardando(false);
    }
  }

  async function cambiarEstado(h: HitoPago, estado: EstadoPago) {
    try {
      fijar(await updatePaymentMilestone(h.id, { status: estado }));
    } catch (err) {
      notifyError("No se pudo cambiar el estado", err instanceof Error ? err.message : "");
    }
  }

  async function quitar(h: HitoPago) {
    const ok = await confirmDelete({ title: "¿Quitar este hito de pago?", text: `«${h.title}» dejará de verse para el cliente.`, confirmText: "Quitar" });
    if (!ok) return;
    try {
      fijar(await deletePaymentMilestone(h.id));
    } catch (err) {
      notifyError("No se pudo quitar el hito", err instanceof Error ? err.message : "");
    }
  }

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <h3 style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
            <Wallet size={18} aria-hidden="true" /> Hitos de pago
          </h3>
          <p className="muted-small" style={{ margin: 0 }}>
            {can_manage
              ? "Lo que ve el cliente. Cambia el estado cuando factures o recibas el pago."
              : "Lo acordado para cada etapa del proyecto y en qué estado está."}
          </p>
        </div>
      </div>

      {totals.length > 0 && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 12 }}>
          {totals.map((t) => (
            <div key={t.currency} className="muted-small">
              <strong style={{ color: "var(--text)" }}>{dinero(t.total, t.currency)}</strong> en total ·{" "}
              {dinero(t.paid, t.currency)} pagado · {dinero(t.pending, t.currency)} por pagar
            </div>
          ))}
        </div>
      )}

      {milestones.length === 0 ? (
        <p className="muted-small">Todavía no hay hitos de pago en este proyecto.</p>
      ) : (
        <div className="table-like">
          <div className={`table-row table-head ${fila}`}>
            <span>Hito</span><span>Monto</span><span>Vence</span><span>Estado</span>{can_manage && <span />}
          </div>
          {milestones.map((h) => (
            <div className={`table-row ${fila}`} key={h.id} style={{ alignItems: "center" }}>
              <div>
                <strong>{h.title}</strong>
                {h.note && <div className="muted-small">{h.note}</div>}
              </div>
              <span style={{ whiteSpace: "nowrap" }}>{dinero(h.amount, h.currency)}</span>
              <div style={{ whiteSpace: "nowrap" }}>
                {fecha(h.due_date)}
                {h.overdue && <div><span className="badge badge-rejected">Vencido</span></div>}
              </div>
              <div>
                {can_manage ? (
                  <select className="input input--xs" value={h.status} aria-label={`Estado de ${h.title}`}
                    onChange={(e) => cambiarEstado(h, e.target.value as EstadoPago)} style={{ marginTop: 0, width: "auto" }}>
                    {(Object.keys(ESTADO) as EstadoPago[]).map((k) => <option key={k} value={k}>{ESTADO[k].label}</option>)}
                  </select>
                ) : (
                  <span className={`badge ${ESTADO[h.status].cls}`}>{ESTADO[h.status].label}</span>
                )}
                {h.paid_at && <div className="muted-small">el {fecha(h.paid_at)}</div>}
              </div>
              {can_manage && (
                <div className="table-actions">
                  {h.status !== "paid" && (
                    <button className="button button-ghost button-sm" type="button" onClick={() => quitar(h)}>Quitar</button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {can_manage && (
        <form onSubmit={crear} style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", marginTop: 14 }}>
          <input className="input" style={{ gridColumn: "span 2" }} placeholder="Hito (p. ej. Anticipo 50 %)" value={titulo}
            onChange={(e) => setTitulo(e.target.value)} required minLength={3} maxLength={160} aria-label="Nombre del hito" />
          <input className="input" type="number" min="0.01" step="0.01" placeholder="Monto" value={monto}
            onChange={(e) => setMonto(e.target.value)} required aria-label="Monto" />
          <select className="input" value={moneda} onChange={(e) => setMoneda(e.target.value as Moneda)} aria-label="Moneda">
            <option value="PEN">Soles (PEN)</option>
            <option value="USD">Dólares (USD)</option>
          </select>
          <input className="input" type="date" value={vence} onChange={(e) => setVence(e.target.value)} aria-label="Fecha de vencimiento" />
          <input className="input" style={{ gridColumn: "span 2" }} placeholder="Nota para el cliente (opcional)" value={nota}
            onChange={(e) => setNota(e.target.value)} maxLength={500} aria-label="Nota para el cliente" />
          <button className="button button-primary" type="submit" disabled={guardando} style={{ alignSelf: "end" }}>
            Agregar hito
          </button>
        </form>
      )}
    </article>
  );
}
