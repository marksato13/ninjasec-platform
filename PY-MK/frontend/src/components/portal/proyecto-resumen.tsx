"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { getSeguimiento, type ProjectItem, type VistaSeguimiento } from "@/lib/api";
import { getProjectStatusLabel } from "@/lib/labels";
import { QK } from "@/lib/query-keys";

import { fecha, hace } from "./etiquetas";
import s from "./portal.module.css";

/**
 * Un proyecto contado al cliente: en que fase va, cuanto lleva, que paso por ultimo y
 * que viene. Lee el mismo seguimiento que la pagina de detalle, asi que lo que dice aqui
 * es exactamente lo que el equipo publico. Si el seguimiento no carga, muestra lo que ya
 * sabe del listado en vez de inventar avance.
 */
export function ProyectoResumen({ proyecto }: { proyecto: ProjectItem }) {
  const q = useQuery<VistaSeguimiento>({
    queryKey: QK.tracking(proyecto.id),
    queryFn: () => getSeguimiento(proyecto.id),
    staleTime: 60_000,
  });

  if (q.isLoading) return <div className={s.esqueleto} aria-hidden="true" />;

  const v = q.data;
  const href = `/portal/projects/${proyecto.id}`;

  if (!v) {
    return (
      <Link className={s.proyecto} href={href}>
        <div className={s.proyectoCabeza}>
          <strong>{proyecto.name}</strong>
          <span className={s.linea}>{getProjectStatusLabel(proyecto.status)}</span>
        </div>
        <p style={{ margin: 0, color: "var(--muted)", fontSize: "0.86rem" }}>
          El seguimiento de este proyecto no está disponible ahora. Ábrelo para ver el detalle.
        </p>
      </Link>
    );
  }

  const actual = v.phases.find((f) => f.state === "current");
  const avanceFase = actual && actual.tasks_total > 0 ? Math.round((actual.tasks_done / actual.tasks_total) * 100) : 0;
  const ultimo = v.updates[0];
  const siguiente = v.next_up[0];

  return (
    <Link className={s.proyecto} href={href} aria-label={`${v.name}: ver seguimiento`}>
      <div className={s.proyectoCabeza}>
        <div style={{ display: "grid", gap: 2, minWidth: 0 }}>
          <strong>{v.name}</strong>
          <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>
            {actual ? `Fase: ${actual.label}` : getProjectStatusLabel(v.status)}
            {v.tasks_total > 0 ? ` — ${v.tasks_done} de ${v.tasks_total} tareas (${v.progress_percent}%)` : ""}
          </span>
        </div>
        {v.paused ? <span className={s.pausado}>En pausa</span> : <span className={s.linea}>{v.line === "dev" ? "Ninja Dev" : "Ninja Sec"}</span>}
      </div>

      <ol className={s.fases} aria-label="Fases del proyecto">
        {v.phases.map((f) => (
          <li
            key={f.key}
            className={`${s.fase} ${f.state === "done" ? s.faseHecha : ""} ${f.state === "current" ? s.faseActual : ""}`}
            style={f.state === "current" ? ({ "--avance": `${Math.max(avanceFase, 8)}%` } as React.CSSProperties) : undefined}
          >
            <span className={s.tramo} aria-hidden="true" />
            <span>
              {f.label}
              <span className={s.soloLector}>
                {f.state === "done" ? " (terminada)" : f.state === "current" ? " (en curso)" : " (pendiente)"}
              </span>
            </span>
          </li>
        ))}
      </ol>

      <dl className={s.datos}>
        <div>
          <dt>Último avance</dt>
          <dd>{ultimo ? `${ultimo.title} — ${hace(ultimo.created_at)}` : "Todavía no hay avances publicados."}</dd>
        </div>
        {siguiente ? (
          <div>
            <dt>Lo que sigue</dt>
            <dd>{siguiente}</dd>
          </div>
        ) : null}
        {v.end_date ? (
          <div>
            <dt>Entrega prevista</dt>
            <dd>{fecha(v.end_date)}</dd>
          </div>
        ) : null}
      </dl>
    </Link>
  );
}
