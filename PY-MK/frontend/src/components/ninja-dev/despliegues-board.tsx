"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Rocket, Trash2 } from "lucide-react";

import {
  createDeployment,
  deleteDeployment,
  getClientSystems,
  getDeployments,
  updateDeployment,
  type Despliegue,
  type ResultadoDespliegue,
} from "@/lib/api";
import { confirmAction, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";
import { ENTORNO, RESULTADO, fechaCorta, mensajeError } from "./etiquetas";
import s from "./ninja-dev.module.css";

const VACIO = {
  system_id: "",
  environment_id: "",
  version: "",
  summary: "",
  deployed_at: "",
  result: "ok" as ResultadoDespliegue,
  backup_done: false,
  smoke_test_passed: false,
  rollback_plan_written: false,
  rollback_plan: "",
};

type Props = {
  /** Limita el registro a un sistema (ficha del sistema). */
  systemId?: number;
};

/** 35-P-02: cada vez que algo sale a un entorno, queda escrito. */
export function DesplieguesBoard({ systemId }: Props) {
  const queryClient = useQueryClient();
  const role = getStoredUser()?.role;
  const isAdmin = role === "admin" || role === "super_admin";

  const [filtroSistema, setFiltroSistema] = useState("");
  const [filtroResultado, setFiltroResultado] = useState<ResultadoDespliegue | "">("");
  const [altaOpen, setAltaOpen] = useState(false);
  const [form, setForm] = useState({ ...VACIO, system_id: systemId ? String(systemId) : "" });
  const [saving, setSaving] = useState(false);
  const [sel, setSel] = useState<Despliegue | null>(null);
  const [edit, setEdit] = useState<{ result: ResultadoDespliegue; summary: string } | null>(null);

  const sistema = systemId ?? (filtroSistema ? Number(filtroSistema) : undefined);
  const filtros = useMemo(() => ({ system_id: sistema }), [sistema]);

  const { data, isLoading, error } = useQuery({
    queryKey: QK.deployments(filtros),
    queryFn: () => getDeployments(filtros),
  });
  const { data: sistemasData } = useQuery({
    queryKey: QK.clientSystems(undefined),
    queryFn: () => getClientSystems(),
  });
  const sistemas = sistemasData?.systems ?? [];
  const elegido = sistemas.find((x) => x.id === Number(form.system_id));

  const despliegues = (data?.deployments ?? []).filter((d) => !filtroResultado || d.result === filtroResultado);
  const entornoElegido = elegido?.environments.find((e) => e.id === Number(form.environment_id));
  const okAProdSinChecklist =
    entornoElegido?.kind === "prod" && form.result === "ok" && !(form.backup_done && form.smoke_test_passed);

  function refrescar() {
    queryClient.invalidateQueries({ queryKey: ["deployments"] });
  }

  async function registrar() {
    if (!form.system_id || !form.environment_id || !form.version.trim() || !form.summary.trim()) {
      notifyError("Faltan datos", "Sistema, entorno, versión y resumen son obligatorios.");
      return;
    }
    if (okAProdSinChecklist) {
      notifyError("Falta el checklist", "Un despliegue a producción que salió bien necesita respaldo y prueba de humo.");
      return;
    }
    setSaving(true);
    try {
      await createDeployment({
        system_id: Number(form.system_id),
        environment_id: Number(form.environment_id),
        version: form.version.trim(),
        summary: form.summary.trim(),
        deployed_at: form.deployed_at ? new Date(form.deployed_at).toISOString() : null,
        result: form.result,
        backup_done: form.backup_done,
        smoke_test_passed: form.smoke_test_passed,
        rollback_plan_written: form.rollback_plan_written,
        rollback_plan: form.rollback_plan.trim() || null,
      });
      refrescar();
      notifySuccess(
        "Despliegue registrado",
        entornoElegido?.kind === "prod" && form.result === "ok"
          ? "El cliente verá «Versión publicada» en la bitácora de su proyecto."
          : undefined,
      );
      setAltaOpen(false);
      setForm({ ...VACIO, system_id: systemId ? String(systemId) : "" });
    } catch (err) {
      notifyError("No se pudo registrar", mensajeError(err));
    } finally {
      setSaving(false);
    }
  }

  async function guardarEdicion() {
    if (!sel || !edit) return;
    try {
      const d = await updateDeployment(sel.id, { result: edit.result, summary: edit.summary.trim() });
      refrescar();
      setSel(d);
      setEdit(null);
      notifySuccess("Despliegue corregido");
    } catch (err) {
      notifyError("No se pudo corregir", mensajeError(err));
    }
  }

  async function quitar(d: Despliegue) {
    const ok = await confirmAction({
      title: "¿Quitar este registro?",
      text: "Solo para un registro erróneo. Si ya publicó un avance en la bitácora, ese avance se queda.",
      confirmText: "Quitar",
    });
    if (!ok) return;
    try {
      await deleteDeployment(d.id);
      refrescar();
      setSel(null);
      notifySuccess("Registro quitado");
    } catch (err) {
      notifyError("No se pudo quitar", mensajeError(err));
    }
  }

  const check = (k: "backup_done" | "smoke_test_passed" | "rollback_plan_written", texto: string) => (
    <label className={s.check}>
      <input type="checkbox" checked={form[k]} onChange={(e) => setForm((f) => ({ ...f, [k]: e.target.checked }))} />
      {texto}
    </label>
  );

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Ninja Dev</p>
          <h3>Despliegues</h3>
        </div>
        <div className={s.barra}>
          {!systemId && (
            <select value={filtroSistema} onChange={(e) => setFiltroSistema(e.target.value)} aria-label="Filtrar por sistema">
              <option value="">Todos los sistemas</option>
              {sistemas.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>
          )}
          <select
            value={filtroResultado}
            onChange={(e) => setFiltroResultado(e.target.value as ResultadoDespliegue | "")}
            aria-label="Filtrar por resultado"
          >
            <option value="">Todos los resultados</option>
            {(Object.keys(RESULTADO) as ResultadoDespliegue[]).map((k) => (
              <option key={k} value={k}>{RESULTADO[k].label}</option>
            ))}
          </select>
          {data?.can_register && (
            <button className="button button-primary" type="button" onClick={() => setAltaOpen(true)} style={{ gap: 6 }}>
              <Rocket size={14} /> Registrar despliegue
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="empty-state">Cargando…</div>
      ) : error ? (
        <div className="empty-state">No se pudieron cargar los despliegues: {mensajeError(error)}</div>
      ) : despliegues.length === 0 ? (
        <div className="empty-state">No hay despliegues registrados{systemId ? " para este sistema" : ""}.</div>
      ) : (
        <div className={`table-like ${s.lista}`}>
          <div className={`table-row table-head ${s.fila} ${s.despliegues} ${s.sinClic} ${s.cabecera}`}>
            <span>Versión</span>
            <span>Entorno</span>
            <span>Qué cambió</span>
            <span>Cuándo</span>
            <span>Resultado</span>
          </div>
          {despliegues.map((d) => (
            <button
              key={d.id}
              type="button"
              className={`table-row ${s.fila} ${s.despliegues}`}
              onClick={() => { setSel(d); setEdit(null); }}
            >
              <span>
                <div className={s.nombre}>{d.version}</div>
                <div className="muted-small">{d.system_name}</div>
              </span>
              <span><span className={`badge ${ENTORNO[d.environment_kind].cls}`}>{ENTORNO[d.environment_kind].label}</span></span>
              <span className={s.celda}>{d.summary}</span>
              <span className={s.celda}>{fechaCorta(d.deployed_at)}</span>
              <span><span className={`badge ${RESULTADO[d.result].cls}`}>{RESULTADO[d.result].label}</span></span>
            </button>
          ))}
        </div>
      )}

      {/* ── Detalle ── */}
      <Modal isOpen={!!sel} title={sel ? `${sel.system_name} · ${sel.version}` : "Despliegue"} onClose={() => setSel(null)}>
        {sel && (
          <div className="entity-form">
            <div className={s.etiquetas}>
              <span className={`badge ${ENTORNO[sel.environment_kind].cls}`}>{ENTORNO[sel.environment_kind].label}</span>
              <span className={`badge ${RESULTADO[sel.result].cls}`}>{RESULTADO[sel.result].label}</span>
              {sel.published_update_id && <span className="badge badge-info">Publicado en la bitácora</span>}
            </div>
            <dl className={s.dl}>
              <dt className="muted-small">Cuándo</dt><dd>{fechaCorta(sel.deployed_at)}</dd>
              <dt className="muted-small">Quién</dt><dd>{sel.deployed_by_name ?? "—"}</dd>
              <dt className="muted-small">Qué cambió</dt><dd style={{ whiteSpace: "pre-wrap" }}>{sel.summary}</dd>
              <dt className="muted-small">Respaldo hecho</dt><dd>{sel.backup_done ? "Sí" : "No"}</dd>
              <dt className="muted-small">Prueba de humo</dt><dd>{sel.smoke_test_passed ? "Pasó" : "No"}</dd>
              <dt className="muted-small">Plan de vuelta atrás</dt>
              <dd style={{ whiteSpace: "pre-wrap" }}>{sel.rollback_plan || (sel.rollback_plan_written ? "Escrito (fuera de la plataforma)" : "—")}</dd>
            </dl>
            <p className="muted-small" style={{ margin: 0 }}>
              El checklist es interno: el cliente solo ve versión, fecha y resumen de lo que llegó a producción.
            </p>

            {edit ? (
              <>
                <select value={edit.result} onChange={(e) => setEdit({ ...edit, result: e.target.value as ResultadoDespliegue })}>
                  {(Object.keys(RESULTADO) as ResultadoDespliegue[]).map((k) => (
                    <option key={k} value={k}>{RESULTADO[k].label}</option>
                  ))}
                </select>
                <textarea value={edit.summary} onChange={(e) => setEdit({ ...edit, summary: e.target.value })} rows={3} />
                <div className={s.barra}>
                  <button className="button button-primary" type="button" onClick={guardarEdicion}>Guardar</button>
                  <button className="button button-ghost" type="button" onClick={() => setEdit(null)}>Cancelar</button>
                </div>
              </>
            ) : (
              <div className={s.barra}>
                {sel.can_edit && (
                  <button
                    className="button button-secondary"
                    type="button"
                    onClick={() => setEdit({ result: sel.result, summary: sel.summary })}
                  >
                    Corregir
                  </button>
                )}
                {isAdmin && (
                  <button className="button button-ghost" type="button" onClick={() => quitar(sel)} style={{ gap: 6 }}>
                    <Trash2 size={13} /> Quitar registro
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* ── Registrar ── */}
      <Modal isOpen={altaOpen} title="Registrar despliegue" onClose={() => setAltaOpen(false)}>
        <div className="entity-form">
          {!systemId && (
            <select
              value={form.system_id}
              onChange={(e) => setForm((f) => ({ ...f, system_id: e.target.value, environment_id: "" }))}
              aria-label="Sistema"
            >
              <option value="">Sistema *</option>
              {sistemas.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}
            </select>
          )}
          <select
            value={form.environment_id}
            onChange={(e) => setForm((f) => ({ ...f, environment_id: e.target.value }))}
            aria-label="Entorno"
            disabled={!elegido}
          >
            <option value="">{elegido && elegido.environments.length === 0 ? "El sistema no tiene entornos" : "Entorno *"}</option>
            {elegido?.environments.map((e) => (
              <option key={e.id} value={e.id}>{ENTORNO[e.kind].label}{e.url ? ` · ${e.url}` : ""}</option>
            ))}
          </select>
          <input
            value={form.version}
            onChange={(e) => setForm((f) => ({ ...f, version: e.target.value }))}
            placeholder="Versión: etiqueta o SHA corto *"
            maxLength={60}
          />
          <textarea
            value={form.summary}
            onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
            placeholder="Qué cambió, en palabras del cliente *"
            rows={3}
          />
          <div className={s.dosColumnas}>
            <label className="muted-small">
              Resultado
              <select value={form.result} onChange={(e) => setForm((f) => ({ ...f, result: e.target.value as ResultadoDespliegue }))}>
                {(Object.keys(RESULTADO) as ResultadoDespliegue[]).map((k) => (
                  <option key={k} value={k}>{RESULTADO[k].label}</option>
                ))}
              </select>
            </label>
            <label className="muted-small">
              Cuándo (vacío = ahora)
              <input
                type="datetime-local"
                value={form.deployed_at}
                onChange={(e) => setForm((f) => ({ ...f, deployed_at: e.target.value }))}
              />
            </label>
          </div>
          {check("backup_done", "Respaldo hecho antes de desplegar")}
          {check("smoke_test_passed", "La prueba de humo pasó")}
          {check("rollback_plan_written", "Plan de vuelta atrás escrito")}
          <textarea
            value={form.rollback_plan}
            onChange={(e) => setForm((f) => ({ ...f, rollback_plan: e.target.value }))}
            placeholder="Cómo se revierte (sin claves: solo dónde están)"
            rows={2}
          />
          {okAProdSinChecklist && (
            <p className={s.peligro} style={{ margin: 0 }}>
              A producción y «salió bien»: marca el respaldo y la prueba de humo.
            </p>
          )}
          <button className="button button-primary" type="button" disabled={saving} onClick={registrar}>
            {saving ? "Registrando…" : "Registrar despliegue"}
          </button>
        </div>
      </Modal>
    </article>
  );
}
