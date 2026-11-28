"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, Undo2 } from "lucide-react";

import {
  changeWorkWindowStatus,
  decideWorkWindow,
  getProjects,
  getWorkWindows,
  ProjectItem,
  requestWorkWindow,
  WorkWindowImpact,
  WorkWindowItem,
  WorkWindowStatus,
} from "@/lib/api";
import { confirmAction, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";

// ── Etiquetas ─────────────────────────────────────────────────────────────────
export const WW_STATUS: Record<WorkWindowStatus, { label: string; cls: string }> = {
  requested:   { label: "Esperando al cliente", cls: "badge-pending" },
  approved:    { label: "Aprobada",             cls: "badge-approved" },
  rejected:    { label: "Rechazada",            cls: "badge-rejected" },
  in_progress: { label: "En ejecución",         cls: "badge-info" },
  completed:   { label: "Completada",           cls: "badge-active" },
  rolled_back: { label: "Vuelta atrás",         cls: "badge-expired" },
  cancelled:   { label: "Cancelada",            cls: "badge-archived" },
};

export const WW_IMPACT: Record<WorkWindowImpact, { label: string; cls: string }> = {
  low:    { label: "Impacto bajo",  cls: "badge-active" },
  medium: { label: "Impacto medio", cls: "badge-pending" },
  high:   { label: "Impacto alto",  cls: "badge-rejected" },
};

const ANTICIPACION_HORAS = 72;

function fecha(iso?: string | null) {
  if (!iso) return "—";
  // El backend guarda UTC sin zona: se interpreta como UTC y se muestra en hora local.
  const d = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  return d.toLocaleString("es-PE", { dateStyle: "medium", timeStyle: "short" });
}

/** datetime-local ("2026-12-01T22:00") en hora local -> ISO con zona. */
function localAIso(valor: string): string {
  return new Date(valor).toISOString();
}

function horasHasta(valor: string): number {
  return (new Date(valor).getTime() - Date.now()) / 3_600_000;
}

const FORM_VACIO = {
  project_id: "",
  title: "",
  change_description: "",
  systems_affected: "",
  impact: "medium" as WorkWindowImpact,
  rollback_plan: "",
  is_emergency: false,
  starts_at: "",
  ends_at: "",
};

type Props = {
  /** "staff": admin y colaborador piden y ejecutan. "client": el cliente aprueba o rechaza. */
  mode: "staff" | "client";
  /** Limita la vista a un proyecto (detalle de proyecto). */
  projectId?: number;
};

export function WorkWindowsBoard({ mode, projectId }: Props) {
  const user = getStoredUser();
  const isAdmin = user?.role === "admin" || user?.role === "super_admin";
  const queryClient = useQueryClient();

  const [filterStatus, setFilterStatus] = useState<WorkWindowStatus | "">("");
  const [filterProject, setFilterProject] = useState<string>("");
  const [selected, setSelected] = useState<WorkWindowItem | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ ...FORM_VACIO, project_id: projectId ? String(projectId) : "" });
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState("");
  const [comment, setComment] = useState("");

  const filtros = useMemo(
    () => ({
      project_id: projectId ?? (filterProject ? Number(filterProject) : undefined),
      window_status: filterStatus || undefined,
    }),
    [projectId, filterProject, filterStatus],
  );

  const { data: windows = [], isLoading } = useQuery<WorkWindowItem[]>({
    queryKey: QK.workWindows(filtros),
    queryFn: () => getWorkWindows(filtros),
  });

  const { data: projects = [] } = useQuery<ProjectItem[]>({
    queryKey: QK.projects(),
    queryFn: () => getProjects(),
  });

  const projectName = useMemo(() => {
    const m: Record<number, string> = {};
    projects.forEach((p) => { m[p.id] = p.name; });
    return m;
  }, [projects]);

  const pendientes = windows.filter((w) => w.status === "requested").length;

  function refrescar(actualizada: WorkWindowItem) {
    queryClient.invalidateQueries({ queryKey: QK.workWindowsAll() });
    setSelected(actualizada);
  }

  async function handleCreate() {
    if (!form.project_id || !form.title || !form.change_description || !form.rollback_plan || !form.starts_at || !form.ends_at) {
      notifyError("Faltan datos", "Proyecto, título, cambio, plan de vuelta atrás, inicio y fin son obligatorios.");
      return;
    }
    if (new Date(form.ends_at) <= new Date(form.starts_at)) {
      notifyError("Fechas inválidas", "El fin tiene que ser posterior al inicio.");
      return;
    }
    if (!form.is_emergency && horasHasta(form.starts_at) < ANTICIPACION_HORAS) {
      notifyError("Muy pronto", `Una ventana se pide con al menos ${ANTICIPACION_HORAS} h de anticipación.`);
      return;
    }
    setSaving(true);
    try {
      await requestWorkWindow({
        project_id: Number(form.project_id),
        title: form.title,
        change_description: form.change_description,
        systems_affected: form.systems_affected || null,
        impact: form.impact,
        rollback_plan: form.rollback_plan,
        is_emergency: isAdmin ? form.is_emergency : false,
        starts_at: localAIso(form.starts_at),
        ends_at: localAIso(form.ends_at),
      });
      queryClient.invalidateQueries({ queryKey: QK.workWindowsAll() });
      notifySuccess("Ventana pedida", "El cliente la verá en su portal para aprobarla o rechazarla.");
      setCreateOpen(false);
      setForm({ ...FORM_VACIO, project_id: projectId ? String(projectId) : "" });
    } catch (err) {
      notifyError("No se pudo pedir la ventana", err instanceof Error ? err.message : undefined);
    } finally {
      setSaving(false);
    }
  }

  async function handleStatus(w: WorkWindowItem, status: "in_progress" | "completed" | "rolled_back" | "cancelled") {
    if (status === "rolled_back" && !note.trim()) {
      notifyError("Falta la nota", "Explica qué pasó y cómo quedó el sistema antes de registrar la vuelta atrás.");
      return;
    }
    if (status === "cancelled") {
      const ok = await confirmAction({ title: "¿Cancelar la ventana?", text: "El cliente verá que se canceló." });
      if (!ok) return;
    }
    try {
      const updated = await changeWorkWindowStatus(w.id, { status, note: note.trim() || null });
      setNote("");
      refrescar(updated);
      notifySuccess(WW_STATUS[updated.status].label);
    } catch (err) {
      notifyError("No se pudo actualizar", err instanceof Error ? err.message : undefined);
    }
  }

  async function handleDecision(w: WorkWindowItem, approve: boolean) {
    if (!approve && !comment.trim()) {
      notifyError("Falta el motivo", "Para rechazar, cuéntanos por qué o qué fecha te conviene.");
      return;
    }
    if (approve) {
      const ok = await confirmAction({
        title: "¿Autorizas esta ventana?",
        text: `Autorizas a Ninja Tech a trabajar en ${w.systems_affected || "los sistemas indicados"} entre ${fecha(w.starts_at)} y ${fecha(w.ends_at)}.`,
      });
      if (!ok) return;
    }
    try {
      const updated = await decideWorkWindow(w.id, { approve, comment: comment.trim() || null });
      setComment("");
      refrescar(updated);
      notifySuccess(approve ? "Ventana autorizada" : "Ventana rechazada");
    } catch (err) {
      notifyError("No se pudo registrar tu decisión", err instanceof Error ? err.message : undefined);
    }
  }

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">{mode === "client" ? "Autorizaciones" : "Gestión de cambios"}</p>
          <h3>Ventanas de trabajo</h3>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          {pendientes > 0 && (
            <span className="badge badge-pending">
              {pendientes} {mode === "client" ? "por autorizar" : "esperando al cliente"}
            </span>
          )}
          {!projectId && (
            <select value={filterProject} onChange={(e) => setFilterProject(e.target.value)} style={{ fontSize: "0.82rem" }}>
              <option value="">Todos los proyectos</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          )}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as WorkWindowStatus | "")}
            style={{ fontSize: "0.82rem" }}
          >
            <option value="">Todos los estados</option>
            {(Object.keys(WW_STATUS) as WorkWindowStatus[]).map((s) => (
              <option key={s} value={s}>{WW_STATUS[s].label}</option>
            ))}
          </select>
          {mode === "staff" && (
            <button className="button button-primary" type="button" onClick={() => setCreateOpen(true)} style={{ gap: 6 }}>
              <CalendarClock size={14} /> Pedir ventana
            </button>
          )}
        </div>
      </div>

      {mode === "client" && (
        <p className="muted-small" style={{ marginTop: 0 }}>
          Antes de tocar algo que puede cortar tu servicio, te pedimos permiso aquí. Revisa qué se hará, cuándo y cómo
          se vuelve atrás si algo falla. Nada se ejecuta sin tu autorización.
        </p>
      )}

      {isLoading ? (
        <div className="empty-state">Cargando…</div>
      ) : windows.length === 0 ? (
        <div className="empty-state">
          {mode === "client" ? "No hay ventanas de trabajo en tus proyectos." : "No hay ventanas de trabajo registradas."}
        </div>
      ) : (
        <div className="table-like">
          <div className="table-row table-head" style={{ gridTemplateColumns: "1.4fr 1fr 1.2fr auto auto" }}>
            <span>Cambio</span>
            <span>Proyecto</span>
            <span>Cuándo</span>
            <span>Impacto</span>
            <span>Estado</span>
          </div>
          {windows.map((w) => (
            <button
              type="button"
              key={w.id}
              className="table-row"
              onClick={() => { setSelected(w); setNote(""); setComment(""); }}
              style={{ gridTemplateColumns: "1.4fr 1fr 1.2fr auto auto", alignItems: "center", textAlign: "left", cursor: "pointer", background: "transparent", border: "none", width: "100%" }}
            >
              <span>
                <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>
                  {w.is_emergency && <AlertTriangle size={12} style={{ color: "var(--danger)", marginRight: 4 }} />}
                  {w.title}
                </div>
                <div className="muted-small">{w.systems_affected || "—"}</div>
              </span>
              <span style={{ fontSize: "0.82rem" }}>{projectName[w.project_id] ?? `#${w.project_id}`}</span>
              <span style={{ fontSize: "0.78rem" }}>{fecha(w.starts_at)} → {fecha(w.ends_at)}</span>
              <span><span className={`badge ${WW_IMPACT[w.impact]?.cls ?? "badge-draft"}`}>{WW_IMPACT[w.impact]?.label ?? w.impact}</span></span>
              <span><span className={`badge ${WW_STATUS[w.status]?.cls ?? "badge-draft"}`}>{WW_STATUS[w.status]?.label ?? w.status}</span></span>
            </button>
          ))}
        </div>
      )}

      {/* ── Detalle ── */}
      <Modal isOpen={!!selected} title={selected?.title ?? "Ventana de trabajo"} onClose={() => setSelected(null)}>
        {selected && (
          <div className="entity-form">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span className={`badge ${WW_STATUS[selected.status]?.cls}`}>{WW_STATUS[selected.status]?.label}</span>
              <span className={`badge ${WW_IMPACT[selected.impact]?.cls}`}>{WW_IMPACT[selected.impact]?.label}</span>
              {selected.is_emergency && <span className="badge badge-rejected">Emergencia</span>}
            </div>
            <dl style={{ display: "grid", gridTemplateColumns: "160px 1fr", gap: "6px 12px", fontSize: "0.85rem", margin: 0 }}>
              <dt className="muted-small">Proyecto</dt><dd style={{ margin: 0 }}>{projectName[selected.project_id] ?? `#${selected.project_id}`}</dd>
              <dt className="muted-small">Inicio</dt><dd style={{ margin: 0 }}>{fecha(selected.starts_at)}</dd>
              <dt className="muted-small">Fin (hora límite)</dt><dd style={{ margin: 0 }}>{fecha(selected.ends_at)}</dd>
              <dt className="muted-small">Sistemas afectados</dt><dd style={{ margin: 0 }}>{selected.systems_affected || "—"}</dd>
              <dt className="muted-small">Qué se hará</dt><dd style={{ margin: 0, whiteSpace: "pre-wrap" }}>{selected.change_description}</dd>
              <dt className="muted-small">Plan de vuelta atrás</dt><dd style={{ margin: 0, whiteSpace: "pre-wrap" }}>{selected.rollback_plan}</dd>
              {selected.client_decision_at && (
                <>
                  <dt className="muted-small">Decisión del cliente</dt>
                  <dd style={{ margin: 0 }}>{fecha(selected.client_decision_at)}{selected.client_comment ? ` — ${selected.client_comment}` : ""}</dd>
                </>
              )}
              {selected.execution_note && (
                <><dt className="muted-small">Nota de ejecución</dt><dd style={{ margin: 0, whiteSpace: "pre-wrap" }}>{selected.execution_note}</dd></>
              )}
            </dl>

            {/* Cliente: aprobar o rechazar */}
            {mode === "client" && selected.status === "requested" && (
              <>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Comentario (obligatorio si rechazas: motivo o fecha alternativa)"
                  rows={3}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="button button-primary" type="button" onClick={() => handleDecision(selected, true)} style={{ flex: 1 }}>
                    Autorizar
                  </button>
                  <button className="button button-danger" type="button" onClick={() => handleDecision(selected, false)} style={{ flex: 1 }}>
                    Rechazar
                  </button>
                </div>
              </>
            )}

            {/* Equipo: ejecutar y cerrar */}
            {mode === "staff" && (
              <>
                {selected.status === "in_progress" && (
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Nota de ejecución (obligatoria si vuelves atrás: qué falló y cómo quedó)"
                    rows={3}
                  />
                )}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {selected.status === "approved" && (
                    <button className="button button-primary" type="button" onClick={() => handleStatus(selected, "in_progress")}>
                      Iniciar
                    </button>
                  )}
                  {selected.status === "in_progress" && (
                    <>
                      <button className="button button-primary" type="button" onClick={() => handleStatus(selected, "completed")}>
                        Completar
                      </button>
                      <button className="button button-secondary" type="button" onClick={() => handleStatus(selected, "rolled_back")} style={{ gap: 6 }}>
                        <Undo2 size={13} /> Volver atrás
                      </button>
                    </>
                  )}
                  {(selected.status === "requested" || selected.status === "approved") && (
                    <button className="button button-ghost" type="button" onClick={() => handleStatus(selected, "cancelled")}>
                      Cancelar ventana
                    </button>
                  )}
                </div>
                {selected.status === "requested" && (
                  <p className="muted-small" style={{ margin: 0 }}>Esperando la autorización del cliente: hasta entonces no se puede iniciar.</p>
                )}
              </>
            )}
          </div>
        )}
      </Modal>

      {/* ── Pedir ventana ── */}
      <Modal isOpen={createOpen} title="Pedir ventana de trabajo" onClose={() => setCreateOpen(false)}>
        <div className="entity-form">
          <p className="muted-small" style={{ margin: 0 }}>
            Se pide con al menos {ANTICIPACION_HORAS} h de anticipación. El cliente la autoriza desde su portal; sin su
            autorización no se puede iniciar.
          </p>
          {!projectId && (
            <select value={form.project_id} onChange={(e) => setForm((f) => ({ ...f, project_id: e.target.value }))}>
              <option value="">Proyecto *</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          )}
          <input value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} placeholder="Título del cambio *" maxLength={160} />
          <textarea
            value={form.change_description}
            onChange={(e) => setForm((f) => ({ ...f, change_description: e.target.value }))}
            placeholder="Qué se va a hacer, paso a paso *"
            rows={3}
          />
          <input
            value={form.systems_affected}
            onChange={(e) => setForm((f) => ({ ...f, systems_affected: e.target.value }))}
            placeholder="Sistemas afectados (ej. FortiGate principal, VPN de sucursales)"
            maxLength={500}
          />
          <select value={form.impact} onChange={(e) => setForm((f) => ({ ...f, impact: e.target.value as WorkWindowImpact }))}>
            <option value="low">Impacto bajo: sin corte esperado</option>
            <option value="medium">Impacto medio: cortes breves posibles</option>
            <option value="high">Impacto alto: corte del servicio durante la ventana</option>
          </select>
          <textarea
            value={form.rollback_plan}
            onChange={(e) => setForm((f) => ({ ...f, rollback_plan: e.target.value }))}
            placeholder="Plan de vuelta atrás: cómo se deja todo como estaba si algo falla *"
            rows={3}
          />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <label className="muted-small">
              Inicio *
              <input type="datetime-local" value={form.starts_at} onChange={(e) => setForm((f) => ({ ...f, starts_at: e.target.value }))} />
            </label>
            <label className="muted-small">
              Fin (hora límite) *
              <input type="datetime-local" value={form.ends_at} onChange={(e) => setForm((f) => ({ ...f, ends_at: e.target.value }))} />
            </label>
          </div>
          {form.starts_at && !form.is_emergency && horasHasta(form.starts_at) < ANTICIPACION_HORAS && (
            <p className="muted-small" style={{ color: "var(--danger)", margin: 0 }}>
              Faltan menos de {ANTICIPACION_HORAS} h para el inicio: elige otra fecha{isAdmin ? " o márcala como emergencia" : ""}.
            </p>
          )}
          {isAdmin && (
            <label className="toggle-switch">
              <input type="checkbox" checked={form.is_emergency} onChange={(e) => setForm((f) => ({ ...f, is_emergency: e.target.checked }))} />
              <span className="toggle-track"><span className="toggle-thumb" /></span>
              <span style={{ fontSize: "0.85rem" }}>Emergencia (se salta las {ANTICIPACION_HORAS} h; el cliente igual la autoriza)</span>
            </label>
          )}
          <button className="button button-primary" type="button" disabled={saving} onClick={handleCreate}>
            {saving ? "Enviando…" : "Pedir ventana"}
          </button>
        </div>
      </Modal>
    </article>
  );
}
