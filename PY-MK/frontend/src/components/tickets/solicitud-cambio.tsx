"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock, GitPullRequestArrow, ShieldCheck, XCircle } from "lucide-react";

import {
  convertChange,
  decideChange,
  estimateChange,
  getProjects,
  getUsers,
  type DashboardUser,
  type ProjectItem,
  type SupportTicketItem,
  type TicketKind,
} from "@/lib/api";
import { askReason, confirmApprove, notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";

/**
 * 35-P-03: solicitudes de cambio.
 *
 * Una incidencia es algo que falla; un cambio es algo nuevo sobre un sistema
 * que el cliente ya tiene. El cambio sigue este recorrido:
 *   el cliente lo pide → el equipo lo estima → el cliente aprueba o rechaza
 *   → (si aprueba) un admin lo convierte en tarea de un proyecto.
 * Rechazar exige un motivo; reestimar tras un rechazo reabre la decisión.
 */

const fmtFecha = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" }) : "";

const fmtHoras = (h: number) => `${Number.isInteger(h) ? h : h.toFixed(1)} h`;

export function BadgeTipo({ kind }: { kind?: TicketKind | null }) {
  return kind === "cambio" ? (
    <span className="badge badge-info">Cambio</span>
  ) : (
    <span className="badge badge-draft">Incidencia</span>
  );
}

/** En qué punto del recorrido está un cambio. */
export function faseCambio(t: SupportTicketItem): { texto: string; clase: string } {
  if (t.converted_project_id) return { texto: "Convertido en tarea", clase: "badge-approved" };
  if (t.client_decision === "approved") return { texto: "Aprobado por el cliente", clase: "badge-approved" };
  if (t.client_decision === "rejected") return { texto: "Rechazado por el cliente", clase: "badge-rejected" };
  if (t.estimate_hours != null) return { texto: "Esperando al cliente", clase: "badge-pending" };
  return { texto: "Por estimar", clase: "badge-draft" };
}

export function BadgeFase({ ticket }: { ticket: SupportTicketItem }) {
  const f = faseCambio(ticket);
  return <span className={`badge ${f.clase}`}>{f.texto}</span>;
}

/** Incidencia sobre un sistema aún en garantía: hasta cuándo cubre. */
export function AvisoGarantia({ ticket }: { ticket: SupportTicketItem }) {
  if (ticket.kind !== "incidencia" || !ticket.warranty_until) return null;
  return (
    <span className="badge badge-approved" style={{ gap: 4 }}>
      <ShieldCheck size={12} aria-hidden="true" /> En garantía hasta {fmtFecha(ticket.warranty_until)}
    </span>
  );
}

const caja: React.CSSProperties = {
  display: "grid",
  gap: 10,
  padding: 14,
  border: "1px solid var(--line)",
  borderRadius: 12,
  background: "var(--panel-strong)",
};

// `.entity-form input` estira todos los inputs; un radio va a su tamaño.
const radio: React.CSSProperties = { width: "auto", minHeight: 0, padding: 0, margin: 0, accentColor: "var(--primary)" };

function Estimacion({ ticket }: { ticket: SupportTicketItem }) {
  if (ticket.estimate_hours == null) return null;
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <span className="card-label">Estimación</span>
      <strong style={{ fontSize: "1.4rem", fontVariantNumeric: "tabular-nums" }}>{fmtHoras(ticket.estimate_hours)}</strong>
      {ticket.estimate_note ? <p className="doc-summary" style={{ margin: 0 }}>{ticket.estimate_note}</p> : null}
      {ticket.estimated_at ? <span className="muted-small">Estimado el {fmtFecha(ticket.estimated_at)}</span> : null}
    </div>
  );
}

function DecisionDelCliente({ ticket }: { ticket: SupportTicketItem }) {
  if (!ticket.client_decision) return null;
  const aprobado = ticket.client_decision === "approved";
  return (
    <div style={{ display: "grid", gap: 4 }}>
      <span className="card-label">Decisión del cliente</span>
      <span className={`badge ${aprobado ? "badge-approved" : "badge-rejected"}`} style={{ gap: 4, justifySelf: "start" }}>
        {aprobado ? <CheckCircle2 size={12} aria-hidden="true" /> : <XCircle size={12} aria-hidden="true" />}
        {aprobado ? "Aprobó" : "Rechazó"}
        {ticket.client_decision_at ? ` · ${fmtFecha(ticket.client_decision_at)}` : ""}
      </span>
      {ticket.client_decision_note ? (
        <p className="doc-summary" style={{ margin: 0 }}>«{ticket.client_decision_note}»</p>
      ) : null}
    </div>
  );
}

// ─── Lado del equipo ─────────────────────────────────────────────────────

export function CambioEquipo({
  ticket,
  esAdmin,
  onActualizado,
}: {
  ticket: SupportTicketItem;
  esAdmin: boolean;
  onActualizado: (t: SupportTicketItem) => void;
}) {
  const queryClient = useQueryClient();
  const [horas, setHoras] = useState(ticket.estimate_hours != null ? String(ticket.estimate_hours) : "");
  const [nota, setNota] = useState(ticket.estimate_note ?? "");
  const [destino, setDestino] = useState<"existente" | "nuevo">("existente");
  const [proyectoId, setProyectoId] = useState("");
  const [proyectoNombre, setProyectoNombre] = useState("");
  const [responsable, setResponsable] = useState("");

  const aprobado = ticket.client_decision === "approved";
  const convertido = !!ticket.converted_project_id;
  const puedeEstimar = !aprobado && !convertido;
  const puedeConvertir = esAdmin && aprobado && !convertido;

  const { data: proyectos = [] } = useQuery<ProjectItem[]>({
    queryKey: QK.projects(),
    queryFn: getProjects,
    enabled: puedeConvertir,
  });
  const { data: usuarios = [] } = useQuery<DashboardUser[]>({
    queryKey: QK.users(),
    queryFn: () => getUsers(),
    enabled: puedeConvertir,
  });
  const proyectosDelCliente = proyectos.filter((p) => p.client_id === ticket.client_id);
  const equipo = usuarios.filter((u) => u.is_active && u.role_code !== "client");

  function alTerminar(t: SupportTicketItem) {
    onActualizado(t);
    queryClient.invalidateQueries({ queryKey: ["tickets"] });
  }

  const estimar = useMutation({
    mutationFn: () => estimateChange(ticket.id, { hours: Number(horas), note: nota.trim() || null }),
    onSuccess: (t) => {
      notifySuccess(ticket.client_decision === "rejected" ? "Estimación nueva enviada al cliente" : "Estimación enviada al cliente");
      alTerminar(t);
    },
    onError: (err) => notifyError("No se pudo estimar", err instanceof Error ? err.message : undefined),
  });

  const convertir = useMutation({
    mutationFn: () =>
      convertChange(ticket.id, {
        assigned_user_id: Number(responsable),
        project_id: destino === "existente" ? Number(proyectoId) : null,
        project_name: destino === "nuevo" ? proyectoNombre.trim() : null,
      }),
    onSuccess: (t) => {
      notifySuccess("Cambio convertido en tarea");
      alTerminar(t);
      queryClient.invalidateQueries({ queryKey: QK.projects() });
    },
    onError: (err) => notifyError("No se pudo convertir", err instanceof Error ? err.message : undefined),
  });

  const horasValidas = Number(horas) > 0 && Number(horas) <= 9999;
  const destinoValido = destino === "existente" ? !!proyectoId : proyectoNombre.trim().length >= 3;

  return (
    <div style={caja}>
      <div className="row-center" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <span className="eyebrow m-0">Solicitud de cambio</span>
        <BadgeFase ticket={ticket} />
      </div>

      <Estimacion ticket={ticket} />
      <DecisionDelCliente ticket={ticket} />

      {puedeEstimar ? (
        <form
          className="entity-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (horasValidas) estimar.mutate();
          }}
        >
          <label style={{ display: "grid", gap: 6, fontSize: "0.78rem", color: "var(--muted)" }}>
            {ticket.estimate_hours != null ? "Reestimar (horas)" : "Horas estimadas"}
            <input
              type="number"
              inputMode="decimal"
              min={0.5}
              max={9999}
              step={0.5}
              value={horas}
              onChange={(e) => setHoras(e.target.value)}
              placeholder="Por ejemplo: 12"
            />
          </label>
          <textarea
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            rows={3}
            maxLength={1000}
            placeholder="Qué incluye la estimación (opcional, lo ve el cliente)"
          />
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={!horasValidas || estimar.isPending}>
              {estimar.isPending ? "Enviando…" : ticket.estimate_hours != null ? "Enviar nueva estimación" : "Enviar estimación"}
            </button>
          </div>
          {ticket.client_decision === "rejected" ? (
            <span className="muted-small">Al reestimar, el cliente vuelve a decidir.</span>
          ) : null}
        </form>
      ) : null}

      {aprobado && !convertido && !esAdmin ? (
        <p className="muted-small" style={{ margin: 0 }}>Aprobado. Un administrador lo convertirá en tarea de un proyecto.</p>
      ) : null}

      {puedeConvertir ? (
        <form
          className="entity-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (destinoValido && responsable) convertir.mutate();
          }}
        >
          <span className="card-label">Convertir en tarea</span>
          <div className="row-center" style={{ flexWrap: "wrap", gap: 12, fontSize: "0.85rem" }}>
            <label className="row-center" style={{ gap: 6, whiteSpace: "nowrap" }}>
              <input type="radio" style={radio} name={`destino-${ticket.id}`} checked={destino === "existente"} onChange={() => setDestino("existente")} />
              Proyecto existente
            </label>
            <label className="row-center" style={{ gap: 6, whiteSpace: "nowrap" }}>
              <input type="radio" style={radio} name={`destino-${ticket.id}`} checked={destino === "nuevo"} onChange={() => setDestino("nuevo")} />
              Proyecto nuevo
            </label>
          </div>
          {destino === "existente" ? (
            <select aria-label="Proyecto" value={proyectoId} onChange={(e) => setProyectoId(e.target.value)}>
              <option value="">{proyectosDelCliente.length ? "Elige un proyecto del cliente" : "El cliente no tiene proyectos"}</option>
              {proyectosDelCliente.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          ) : (
            <input
              value={proyectoNombre}
              onChange={(e) => setProyectoNombre(e.target.value)}
              maxLength={160}
              placeholder="Nombre del proyecto nuevo (mínimo 3 caracteres)"
            />
          )}
          <select aria-label="Responsable" value={responsable} onChange={(e) => setResponsable(e.target.value)}>
            <option value="">Responsable de la tarea</option>
            {equipo.map((u) => (
              <option key={u.id} value={u.id}>{u.full_name}</option>
            ))}
          </select>
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={!destinoValido || !responsable || convertir.isPending}>
              <GitPullRequestArrow size={14} aria-hidden="true" /> {convertir.isPending ? "Convirtiendo…" : "Convertir en tarea"}
            </button>
          </div>
        </form>
      ) : null}

      {convertido ? (
        <Link className="button button-secondary" style={{ justifySelf: "start" }} href={`/dashboard/projects/${ticket.converted_project_id}`}>
          Ver el proyecto
        </Link>
      ) : null}
    </div>
  );
}

// ─── Lado del cliente ────────────────────────────────────────────────────

export function CambioCliente({
  ticket,
  onActualizado,
}: {
  ticket: SupportTicketItem;
  onActualizado: (t: SupportTicketItem) => void;
}) {
  const queryClient = useQueryClient();
  const decidir = useMutation({
    mutationFn: (v: { decision: "approved" | "rejected"; nota: string | null }) => decideChange(ticket.id, v.decision, v.nota),
    onSuccess: (t, v) => {
      notifySuccess(v.decision === "approved" ? "Estimación aprobada" : "Rechazo enviado al equipo");
      onActualizado(t);
      queryClient.invalidateQueries({ queryKey: ["tickets"] });
    },
    onError: (err) => notifyError("No se pudo registrar tu decisión", err instanceof Error ? err.message : undefined),
  });

  async function aprobar() {
    const ok = await confirmApprove({
      title: "¿Apruebas esta estimación?",
      text: `${fmtHoras(ticket.estimate_hours ?? 0)} para «${ticket.title}». El equipo lo planificará como trabajo de un proyecto.`,
      confirmText: "Aprobar",
    });
    if (ok) decidir.mutate({ decision: "approved", nota: null });
  }

  async function rechazar() {
    const nota = await askReason({
      title: "¿Por qué la rechazas?",
      text: "El equipo verá tu motivo y podrá enviarte una estimación nueva.",
      placeholder: "Por ejemplo: esperaba menos horas, o falta incluir el reporte en PDF",
      confirmText: "Rechazar estimación",
    });
    if (nota !== null) decidir.mutate({ decision: "rejected", nota });
  }

  const esperando = ticket.estimate_hours != null && !ticket.client_decision;

  return (
    <div style={caja}>
      <div className="row-center" style={{ justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
        <span className="eyebrow m-0">Tu solicitud de cambio</span>
        <BadgeFase ticket={ticket} />
      </div>

      {ticket.estimate_hours == null ? (
        <p className="muted-small" style={{ margin: 0, display: "flex", gap: 6, alignItems: "center" }}>
          <Clock size={14} aria-hidden="true" /> El equipo está estimando cuánto trabajo lleva. Te avisaremos aquí.
        </p>
      ) : (
        <Estimacion ticket={ticket} />
      )}

      <DecisionDelCliente ticket={ticket} />

      {esperando ? (
        <div className="panel-actions">
          <button className="button button-success" type="button" disabled={decidir.isPending} onClick={aprobar}>
            <CheckCircle2 size={14} aria-hidden="true" /> Aprobar
          </button>
          <button className="button button-secondary" type="button" disabled={decidir.isPending} onClick={rechazar}>
            Rechazar
          </button>
        </div>
      ) : null}

      {ticket.client_decision === "rejected" ? (
        <p className="muted-small" style={{ margin: 0 }}>El equipo revisará tu motivo y puede enviarte una estimación nueva.</p>
      ) : null}
      {ticket.client_decision === "approved" && !ticket.converted_project_id ? (
        <p className="muted-small" style={{ margin: 0 }}>Aprobado. El equipo lo está planificando.</p>
      ) : null}
      {ticket.converted_project_id ? (
        <Link className="button button-secondary" style={{ justifySelf: "start" }} href={`/portal/projects/${ticket.converted_project_id}`}>
          Ver el proyecto
        </Link>
      ) : null}
    </div>
  );
}
