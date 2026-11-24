"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  EstadoModulo,
  getAvanceEquipo,
  getDetalleEquipo,
  getMiInscripcion,
  getMisInscripciones,
  getPlanes,
  inscribirse,
  marcarAvance,
  validarModulo,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";

const ESTADO: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  completed: "Completado",
  validated: "Validado",
};

/** Barra de avance. Es un <progress> real, para que los lectores de pantalla la lean. */
function Barra({ valor }: { valor: number }) {
  return (
    <progress
      value={valor}
      max={100}
      aria-label={`${valor}% completado`}
      style={{ width: "100%", height: 10, accentColor: "var(--primary)" }}
    />
  );
}

export default function FormacionPage() {
  const user = getStoredUser();
  const esAdmin = user?.role === "admin" || user?.role === "super_admin";
  const qc = useQueryClient();
  const [abierta, setAbierta] = useState<number | null>(null);
  const [equipoAbierto, setEquipoAbierto] = useState<number | null>(null);

  const planes = useQuery({ queryKey: QK.studyPlans(), queryFn: getPlanes });
  const mias = useQuery({ queryKey: QK.studyMe(), queryFn: getMisInscripciones });
  const detalle = useQuery({
    queryKey: QK.studyMine(abierta ?? 0),
    queryFn: () => getMiInscripcion(abierta as number),
    enabled: abierta !== null,
  });
  const equipo = useQuery({ queryKey: QK.studyTeam(), queryFn: getAvanceEquipo, enabled: esAdmin });
  const detalleEquipo = useQuery({
    queryKey: ["study", "team", equipoAbierto ?? 0],
    queryFn: () => getDetalleEquipo(equipoAbierto as number),
    enabled: esAdmin && equipoAbierto !== null,
  });

  const refrescar = () => {
    qc.invalidateQueries({ queryKey: ["study"] });
  };
  const alFallar = (titulo: string) => (e: unknown) =>
    notifyError(titulo, e instanceof Error ? e.message : undefined);

  const unirme = useMutation({
    mutationFn: (planId: number) => inscribirse(planId),
    onSuccess: (i) => {
      refrescar();
      setAbierta(i.id);
      notifySuccess("Inscrito", "Marca tu avance módulo a módulo.");
    },
    onError: alFallar("No se pudo inscribir"),
  });

  const avanzar = useMutation({
    mutationFn: (v: { enrollmentId: number; moduleId: number; status: EstadoModulo; hours?: number | null }) =>
      marcarAvance(v.enrollmentId, v.moduleId, { status: v.status, hours_spent: v.hours ?? null }),
    onSuccess: refrescar,
    onError: alFallar("No se pudo guardar el avance"),
  });

  const validar = useMutation({
    mutationFn: (progressId: number) => validarModulo(progressId),
    onSuccess: () => {
      refrescar();
      notifySuccess("Módulo validado");
    },
    onError: alFallar("No se pudo validar"),
  });

  const idsInscritos = new Set((mias.data ?? []).map((i) => i.plan_id));

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Talento</p>
          <h2>Formación</h2>
        </div>
      </div>

      <article className="panel">
        <p className="muted-small" style={{ margin: 0 }}>
          Rutas de preparación hacia una certificación. El porcentaje se pondera por <strong>horas</strong>,
          no por número de módulos: uno de 20 h pesa más que uno de 2 h. Lo que marcas como
          «Completado» cuenta como avance; un administrador puede <strong>validarlo</strong> después.
        </p>
      </article>

      {/* ---- Mis planes ---- */}
      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Mis planes</p>
            <h3>Tu avance</h3>
          </div>
        </div>
        {mias.isLoading && <div className="empty-state">Cargando…</div>}
        {!mias.isLoading && (mias.data ?? []).length === 0 && (
          <div className="empty-state">Todavía no estás inscrito en ningún plan. Elige uno abajo.</div>
        )}
        <div style={{ display: "grid", gap: 14 }}>
          {(mias.data ?? []).map((i) => (
            <div key={i.id} className="panel" style={{ margin: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                <strong>{i.plan_name}</strong>
                <span className="muted-small">
                  {i.modules_done}/{i.modules_total} módulos · {i.hours_done}/{i.hours_total} h
                </span>
              </div>
              <Barra valor={i.percent} />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                <span className="muted-small">{i.percent}%</span>
                <button
                  type="button"
                  className="button button-ghost button-sm"
                  aria-expanded={abierta === i.id}
                  onClick={() => setAbierta(abierta === i.id ? null : i.id)}
                >
                  {abierta === i.id ? "Ocultar módulos" : "Ver módulos"}
                </button>
              </div>

              {abierta === i.id && (
                <div className="table-like" style={{ marginTop: 10 }}>
                  <div className="table-row table-head" style={{ gridTemplateColumns: "2.4fr 0.7fr 1.2fr" }}>
                    <span>Módulo</span>
                    <span>Horas</span>
                    <span>Estado</span>
                  </div>
                  {detalle.isLoading && <div className="empty-state">Cargando módulos…</div>}
                  {(detalle.data?.modules ?? []).map((m) => (
                    <div key={m.id} className="table-row" style={{ gridTemplateColumns: "2.4fr 0.7fr 1.2fr" }}>
                      <span>
                        <strong>{m.position}. {m.title}</strong>
                        {m.lab && <span className="muted-small" style={{ display: "block" }}>Laboratorio: {m.lab}</span>}
                      </span>
                      <span className="muted-small">{m.estimated_hours ?? "—"}</span>
                      <span>
                        {m.validated ? (
                          <span className="badge badge-active">Validado</span>
                        ) : (
                          <select
                            aria-label={`Estado del módulo ${m.title}`}
                            value={m.status}
                            disabled={avanzar.isPending}
                            onChange={(e) =>
                              avanzar.mutate({
                                enrollmentId: i.id,
                                moduleId: m.id,
                                status: e.target.value as EstadoModulo,
                              })
                            }
                          >
                            <option value="pending">{ESTADO.pending}</option>
                            <option value="in_progress">{ESTADO.in_progress}</option>
                            <option value="completed">{ESTADO.completed}</option>
                          </select>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </article>

      {/* ---- Planes disponibles ---- */}
      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Catálogo</p>
            <h3>Planes disponibles</h3>
          </div>
        </div>
        {planes.isLoading && <div className="empty-state">Cargando…</div>}
        {planes.error && <p className="form-error">No se pudieron cargar los planes.</p>}
        <div className="marketing-grid marketing-grid--two">
          {(planes.data ?? []).map((p) => (
            <div key={p.id} className="panel" style={{ margin: 0 }}>
              <strong>{p.name}</strong>
              <p className="muted-small" style={{ margin: "4px 0 8px" }}>
                {p.vendor ?? p.area}
                {p.exam_code ? ` · examen ${p.exam_code}` : ""} · {p.modules_count} módulos
                {p.estimated_hours ? ` · ${p.estimated_hours} h` : ""}
              </p>
              {p.description && <p style={{ margin: "0 0 10px" }}>{p.description}</p>}
              {idsInscritos.has(p.id) ? (
                <span className="badge badge-active">Inscrito</span>
              ) : (
                <button
                  type="button"
                  className="button button-primary button-sm"
                  disabled={unirme.isPending}
                  onClick={() => unirme.mutate(p.id)}
                >
                  Inscribirme
                </button>
              )}
            </div>
          ))}
        </div>
      </article>

      {/* ---- Equipo (solo admin) ---- */}
      {esAdmin && (
        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Equipo</p>
              <h3>Avance de los colaboradores</h3>
            </div>
          </div>
          {(equipo.data ?? []).length === 0 && !equipo.isLoading && (
            <div className="empty-state">Nadie se ha inscrito todavía.</div>
          )}
          <div className="table-like">
            {(equipo.data ?? []).map((f) => (
              <div key={f.enrollment_id}>
                <div className="table-row" style={{ gridTemplateColumns: "1.4fr 1.6fr 1fr 1fr auto", alignItems: "center" }}>
                  <strong>{f.user_name}</strong>
                  <span className="muted-small">{f.plan_name}</span>
                  <span><Barra valor={f.percent} /></span>
                  <span className="muted-small">
                    {f.pending_validation > 0 ? (
                      <span className="badge badge-pending">{f.pending_validation} por validar</span>
                    ) : (
                      `${f.percent}%`
                    )}
                  </span>
                  <button
                    type="button"
                    className="button button-ghost button-sm"
                    aria-expanded={equipoAbierto === f.enrollment_id}
                    onClick={() => setEquipoAbierto(equipoAbierto === f.enrollment_id ? null : f.enrollment_id)}
                  >
                    {equipoAbierto === f.enrollment_id ? "Cerrar" : "Revisar"}
                  </button>
                </div>
                {equipoAbierto === f.enrollment_id &&
                  (detalleEquipo.data?.modules ?? []).map((m) => (
                    <div key={m.id} className="table-row" style={{ gridTemplateColumns: "2fr 1fr auto", paddingLeft: 24 }}>
                      <span>{m.position}. {m.title}</span>
                      <span className="muted-small">{ESTADO[m.status] ?? m.status}</span>
                      {m.status === "completed" && m.progress_id !== null ? (
                        <button
                          type="button"
                          className="button button-success button-sm"
                          disabled={validar.isPending || f.user_id === user?.id}
                          title={f.user_id === user?.id ? "No puedes validar tu propio avance" : undefined}
                          onClick={() => validar.mutate(m.progress_id as number)}
                        >
                          Validar
                        </button>
                      ) : (
                        <span />
                      )}
                    </div>
                  ))}
              </div>
            ))}
          </div>
        </article>
      )}
    </section>
  );
}
