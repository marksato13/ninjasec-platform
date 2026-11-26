"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, CheckCircle2, ClipboardCheck, MessageSquareWarning, Pencil, Plus, Trash2 } from "lucide-react";

import {
  createAcceptanceCase,
  decideAcceptanceCase,
  deleteAcceptanceCase,
  getAcceptanceCases,
  updateAcceptanceCase,
  type CasoAceptacion,
  type CasoAceptacionInput,
  type EstadoCaso,
  type VistaAceptacion,
} from "@/lib/api";
import { askReason, confirmApprove, confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";

/**
 * 35-P-05: pruebas de aceptación (UAT).
 *
 * El equipo escribe los casos (qué hacer y qué debería pasar); el cliente los
 * prueba y los aprueba u observa. Con todos aprobados, el proyecto está listo
 * para el acta de conformidad. Qué botones salen lo decide la API
 * (`can_manage`, `can_decide`), no el rol que creemos tener.
 */

const ESTADO: Record<EstadoCaso, { texto: string; clase: string }> = {
  pendiente: { texto: "Pendiente", clase: "badge-pending" },
  aprobado: { texto: "Aprobado", clase: "badge-approved" },
  observado: { texto: "Observado", clase: "badge-rejected" },
};

const fmtFecha = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" }) : "";

const VACIO: CasoAceptacionInput = { title: "", steps: "", expected: "" };

const tarjeta: React.CSSProperties = {
  display: "grid",
  gap: 10,
  padding: 14,
  border: "1px solid var(--line)",
  borderRadius: 12,
  background: "var(--panel-strong)",
  minWidth: 0,
};

const bloqueTexto: React.CSSProperties = { margin: 0, whiteSpace: "pre-wrap", overflowWrap: "anywhere" };

function Resumen({ vista }: { vista: VistaAceptacion }) {
  const { summary } = vista;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
      <span className="muted-small" style={{ fontVariantNumeric: "tabular-nums" }}>
        {summary.aprobado} de {summary.total} aprobados
      </span>
      {summary.pendiente > 0 ? <span className="badge badge-pending">{summary.pendiente} pendientes</span> : null}
      {summary.observado > 0 ? <span className="badge badge-rejected">{summary.observado} observados</span> : null}
    </div>
  );
}

function Progreso({ vista }: { vista: VistaAceptacion }) {
  const { total, aprobado } = vista.summary;
  const pct = total ? Math.round((aprobado / total) * 100) : 0;
  return (
    <div
      role="progressbar"
      aria-valuenow={pct}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Casos aprobados"
      style={{ height: 6, borderRadius: 999, background: "var(--line)", overflow: "hidden" }}
    >
      <div
        style={{
          height: "100%",
          width: `${pct}%`,
          background: "var(--success)",
          transition: "width 300ms var(--ease-out)",
        }}
      />
    </div>
  );
}

function AvisoActa({ vista, modo }: { vista: VistaAceptacion; modo: "equipo" | "cliente" }) {
  if (!vista.summary.ready_for_signoff) return null;
  return (
    <div
      role="status"
      style={{
        ...tarjeta,
        borderColor: "var(--success)",
        display: "flex",
        gap: 10,
        alignItems: "flex-start",
      }}
    >
      <ClipboardCheck size={18} style={{ color: "var(--success)", flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
      <div style={{ display: "grid", gap: 2 }}>
        <strong>Listo para el acta de conformidad</strong>
        <span className="muted-small">
          {modo === "equipo"
            ? "Todos los casos están aprobados por el cliente. Ya puedes proponer el acta."
            : "Aprobaste todos los casos. El equipo te enviará el acta de conformidad para cerrar."}
        </span>
      </div>
    </div>
  );
}

function CuerpoCaso({ caso, indice }: { caso: CasoAceptacion; indice: number }) {
  const e = ESTADO[caso.status];
  return (
    <>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap" }}>
        <strong style={{ minWidth: 0, overflowWrap: "anywhere" }}>
          <span className="muted-small" style={{ fontVariantNumeric: "tabular-nums", marginRight: 6 }}>{indice + 1}.</span>
          {caso.title}
        </strong>
        <span className={`badge ${e.clase}`}>
          {e.texto}
          {caso.decided_at && caso.status !== "pendiente" ? ` · ${fmtFecha(caso.decided_at)}` : ""}
        </span>
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <span className="card-label">Pasos</span>
        <p className="doc-summary" style={bloqueTexto}>{caso.steps}</p>
      </div>
      <div style={{ display: "grid", gap: 4 }}>
        <span className="card-label">Resultado esperado</span>
        <p className="doc-summary" style={bloqueTexto}>{caso.expected}</p>
      </div>
      {caso.status === "observado" && caso.client_note ? (
        <div style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
          <MessageSquareWarning size={14} style={{ color: "var(--danger)", flexShrink: 0, marginTop: 3 }} aria-hidden="true" />
          <p className="doc-summary" style={bloqueTexto}>«{caso.client_note}»</p>
        </div>
      ) : null}
    </>
  );
}

export function PruebasAceptacion({ projectId, modo }: { projectId: number; modo: "equipo" | "cliente" }) {
  const queryClient = useQueryClient();
  const esAdmin = ["admin", "super_admin"].includes(getStoredUser()?.role ?? "");
  const [editando, setEditando] = useState<CasoAceptacion | null>(null);
  const [formAbierto, setFormAbierto] = useState(false);
  const [form, setForm] = useState<CasoAceptacionInput>(VACIO);

  const { data: vista, isLoading, error } = useQuery<VistaAceptacion>({
    queryKey: QK.acceptance(projectId),
    queryFn: () => getAcceptanceCases(projectId),
    enabled: Number.isFinite(projectId) && projectId > 0,
  });

  const guardarVista = (v: VistaAceptacion) => {
    queryClient.setQueryData(QK.acceptance(projectId), v);
    queryClient.invalidateQueries({ queryKey: QK.acceptance(projectId) });
  };
  const fallo = (titulo: string) => (err: unknown) => notifyError(titulo, err instanceof Error ? err.message : undefined);

  const guardar = useMutation({
    mutationFn: () => (editando ? updateAcceptanceCase(editando.id, form) : createAcceptanceCase(projectId, form)),
    onSuccess: (v) => {
      notifySuccess(editando ? "Caso actualizado" : "Caso añadido");
      guardarVista(v);
      setFormAbierto(false);
      setEditando(null);
      setForm(VACIO);
    },
    onError: fallo("No se pudo guardar el caso"),
  });

  const mover = useMutation({
    mutationFn: async ({ a, b }: { a: CasoAceptacion; b: CasoAceptacion }) => {
      // Intercambia posiciones; si coincidían, separa la del que se mueve.
      const posA = a.position === b.position ? Math.max(0, b.position + (a.position <= b.position ? 1 : -1)) : b.position;
      await updateAcceptanceCase(b.id, { position: a.position });
      return updateAcceptanceCase(a.id, { position: posA });
    },
    onSuccess: guardarVista,
    onError: fallo("No se pudo reordenar"),
  });

  const quitar = useMutation({
    mutationFn: (id: number) => deleteAcceptanceCase(id),
    onSuccess: (v) => {
      notifySuccess("Caso quitado");
      guardarVista(v);
    },
    onError: fallo("No se pudo quitar el caso"),
  });

  const decidir = useMutation({
    mutationFn: (v: { id: number; decision: "aprobado" | "observado"; note: string | null }) =>
      decideAcceptanceCase(v.id, { decision: v.decision, note: v.note }),
    onSuccess: (v, vars) => {
      notifySuccess(vars.decision === "aprobado" ? "Caso aprobado" : "Observación enviada al equipo");
      guardarVista(v);
    },
    onError: fallo("No se pudo registrar tu decisión"),
  });

  function abrirNuevo() {
    setEditando(null);
    setForm(VACIO);
    setFormAbierto(true);
  }

  function abrirEdicion(c: CasoAceptacion) {
    setEditando(c);
    setForm({ title: c.title, steps: c.steps, expected: c.expected });
    setFormAbierto(true);
  }

  async function aprobar(c: CasoAceptacion) {
    const ok = await confirmApprove({
      title: "¿Funciona como se esperaba?",
      text: `«${c.title}» quedará aprobado y formará parte del acta de conformidad. Después no se puede cambiar.`,
      confirmText: "Aprobar caso",
    });
    if (ok) decidir.mutate({ id: c.id, decision: "aprobado", note: null });
  }

  async function observar(c: CasoAceptacion) {
    const note = await askReason({
      title: "¿Qué no funcionó?",
      text: "El equipo verá tu observación, lo corregirá y te pedirá que lo pruebes otra vez.",
      placeholder: "Por ejemplo: al guardar sale un error y no aparece en la lista",
      confirmText: "Enviar observación",
    });
    if (note !== null) decidir.mutate({ id: c.id, decision: "observado", note });
  }

  async function confirmarQuitar(c: CasoAceptacion) {
    const ok = await confirmDelete({ title: `¿Quitar «${c.title}»?`, text: "El caso desaparece de las pruebas de aceptación." });
    if (ok) quitar.mutate(c.id);
  }

  if (isLoading) return <div className="empty-state">Cargando pruebas de aceptación…</div>;
  if (error) {
    // El cliente sin casos o un colaborador ajeno al proyecto: sin ruido en su página.
    if (modo === "cliente") return null;
    return <p className="form-error">{error instanceof Error ? error.message : "No se pudieron cargar las pruebas"}</p>;
  }
  if (!vista) return null;
  // En el portal, un proyecto sin casos no muestra la sección.
  if (modo === "cliente" && vista.cases.length === 0) return null;

  const ocupado = mover.isPending || decidir.isPending || quitar.isPending;
  const valido = form.title.trim().length >= 3 && form.steps.trim().length >= 3 && form.expected.trim().length >= 3;

  return (
    <article className="panel" style={{ display: "grid", gap: 14 }}>
      <div className="panel-head" style={{ display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "grid", gap: 4 }}>
          <p className="eyebrow m-0">Pruebas de aceptación</p>
          <h3 style={{ margin: 0 }}>{modo === "cliente" ? "Prueba lo entregado" : "Casos de prueba del cliente"}</h3>
          {vista.cases.length > 0 ? <Resumen vista={vista} /> : null}
        </div>
        {vista.can_manage ? (
          <button className="button button-primary" type="button" onClick={abrirNuevo}>
            <Plus size={14} aria-hidden="true" /> Añadir caso
          </button>
        ) : null}
      </div>

      {vista.cases.length > 0 ? <Progreso vista={vista} /> : null}
      <AvisoActa vista={vista} modo={modo} />

      {modo === "cliente" && vista.can_decide && !vista.summary.ready_for_signoff ? (
        <p className="muted-small" style={{ margin: 0 }}>
          Sigue los pasos de cada caso y dinos si el resultado es el esperado.
        </p>
      ) : null}

      {vista.cases.length === 0 ? (
        <div className="empty-state">
          Aún no hay casos. Escribe qué debe probar el cliente y qué debería ver; cuando los apruebe todos, el proyecto queda listo para el acta.
        </div>
      ) : (
        <div className="stack-list" style={{ display: "grid", gap: 10 }}>
          {vista.cases.map((c, i) => (
            <div key={c.id} style={tarjeta}>
              <CuerpoCaso caso={c} indice={i} />

              {vista.can_manage ? (
                <div className="panel-actions" style={{ flexWrap: "wrap" }}>
                  <button
                    className="button button-ghost button-sm"
                    type="button"
                    aria-label={`Subir «${c.title}»`}
                    disabled={i === 0 || ocupado}
                    onClick={() => mover.mutate({ a: c, b: vista.cases[i - 1] })}
                  >
                    <ArrowUp size={14} aria-hidden="true" />
                  </button>
                  <button
                    className="button button-ghost button-sm"
                    type="button"
                    aria-label={`Bajar «${c.title}»`}
                    disabled={i === vista.cases.length - 1 || ocupado}
                    onClick={() => mover.mutate({ a: c, b: vista.cases[i + 1] })}
                  >
                    <ArrowDown size={14} aria-hidden="true" />
                  </button>
                  {c.status !== "aprobado" ? (
                    <button className="button button-secondary button-sm" type="button" onClick={() => abrirEdicion(c)}>
                      <Pencil size={14} aria-hidden="true" /> {c.status === "observado" ? "Corregir" : "Editar"}
                    </button>
                  ) : (
                    <span className="muted-small">Aprobado: es evidencia del acta.</span>
                  )}
                  {esAdmin && c.status !== "aprobado" ? (
                    <button className="button button-ghost button-sm" type="button" disabled={ocupado} onClick={() => confirmarQuitar(c)}>
                      <Trash2 size={14} aria-hidden="true" /> Quitar
                    </button>
                  ) : null}
                </div>
              ) : null}

              {vista.can_decide && c.status !== "aprobado" ? (
                <div className="panel-actions" style={{ flexWrap: "wrap" }}>
                  <button className="button button-success" type="button" disabled={ocupado} onClick={() => aprobar(c)}>
                    <CheckCircle2 size={14} aria-hidden="true" /> Funciona
                  </button>
                  <button className="button button-secondary" type="button" disabled={ocupado} onClick={() => observar(c)}>
                    Observar
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {vista.can_manage ? (
        <Modal
          isOpen={formAbierto}
          title={editando ? "Editar caso de prueba" : "Nuevo caso de prueba"}
          onClose={() => { setFormAbierto(false); setEditando(null); }}
        >
          <form
            className="entity-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (valido) guardar.mutate();
            }}
          >
            <input
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
              placeholder="Qué se prueba (por ejemplo: registrar una venta)"
              maxLength={200}
              required
            />
            <textarea
              value={form.steps}
              onChange={(e) => setForm((f) => ({ ...f, steps: e.target.value }))}
              placeholder={"Pasos, uno por línea:\n1. Entra a Ventas\n2. Pulsa Nueva venta…"}
              rows={4}
              maxLength={4000}
              required
            />
            <textarea
              value={form.expected}
              onChange={(e) => setForm((f) => ({ ...f, expected: e.target.value }))}
              placeholder="Qué debería ver el cliente si todo va bien"
              rows={3}
              maxLength={2000}
              required
            />
            {editando?.status === "observado" ? (
              <span className="muted-small">Al corregirlo vuelve a pendiente y el cliente lo prueba otra vez.</span>
            ) : null}
            <div className="panel-actions">
              <button className="button button-primary" type="submit" disabled={!valido || guardar.isPending}>
                {guardar.isPending ? "Guardando…" : editando ? "Guardar cambios" : "Añadir caso"}
              </button>
              <button className="button button-ghost" type="button" onClick={() => { setFormAbierto(false); setEditando(null); }}>
                Cancelar
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </article>
  );
}
