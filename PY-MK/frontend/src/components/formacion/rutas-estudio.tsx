"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Compass, ExternalLink } from "lucide-react";

import { getMisInscripciones, getPlanes, getUserCertifications, inscribirse } from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { EmptyState } from "@/components/ui/empty-state";

import s from "./formacion.module.css";
import { plataformaDe } from "./utils";

const normal = (t: string | null | undefined) => (t ?? "").trim().toLowerCase();

/**
 * Rutas de estudio como guia: que certificacion preparar, donde y cuanto tiempo.
 * El estudio se hace en la plataforma del fabricante; aqui solo se marca que te
 * estas preparando, y se da por obtenida cuando su certificacion queda validada.
 */
export function RutasEstudio({ userId }: { userId: number | undefined }) {
  const qc = useQueryClient();
  const planes = useQuery({ queryKey: QK.studyPlans(), queryFn: getPlanes });
  const mias = useQuery({ queryKey: QK.studyMe(), queryFn: getMisInscripciones });
  const certs = useQuery({ queryKey: QK.certifications(), queryFn: getUserCertifications });

  const preparando = new Set((mias.data ?? []).map((i) => i.plan_id));
  const obtenidas = new Set(
    (certs.data ?? [])
      .filter((c) => c.user_id === userId && c.effective_status === "approved")
      .map((c) => normal(c.name)),
  );

  const preparar = useMutation({
    mutationFn: (planId: number) => inscribirse(planId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["study"] });
      notifySuccess("Ruta marcada", "Cuando apruebes, registra la certificación y adjunta el certificado.");
    },
    onError: (e) => notifyError("No se pudo marcar la ruta", e instanceof Error ? e.message : undefined),
  });

  return (
    <div className="page-stack">
      <article className="panel">
        <p className={s.intro}>
          Las rutas recomendadas para cada área. El curso y el examen se hacen en la plataforma oficial del fabricante;
          aquí solo marcas que te estás preparando para que el equipo lo sepa.
        </p>
      </article>

      {planes.isLoading ? <div className="empty-state">Cargando rutas…</div> : null}
      {planes.error ? <p className="form-error">No se pudieron cargar las rutas.</p> : null}
      {!planes.isLoading && !planes.error && (planes.data ?? []).length === 0 ? (
        <EmptyState icon={Compass} title="No hay rutas de estudio" description="Un administrador puede cargarlas desde los planes de estudio." />
      ) : null}

      <div className={s.grid}>
        {(planes.data ?? []).map((p) => {
          const plataforma = plataformaDe(p.vendor, p.name, p.target_certification);
          const obtenida = p.target_certification ? obtenidas.has(normal(p.target_certification)) : false;
          const enCurso = preparando.has(p.id);
          return (
            <section key={p.id} className={s.ruta}>
              <div className={s.credHead}>
                <h4>{p.name}</h4>
                {obtenida ? (
                  <span className={`${s.estado} ${s.ok}`}>Certificado obtenido</span>
                ) : enCurso ? (
                  <span className={`${s.estado} ${s.pendiente}`}>En preparación</span>
                ) : null}
              </div>
              <p className="muted-small" style={{ margin: 0 }}>
                {[p.vendor ?? p.area, p.exam_code ? `examen ${p.exam_code}` : null, p.estimated_hours ? `unas ${p.estimated_hours} h` : null]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
              {p.description ? <p style={{ margin: 0 }}>{p.description}</p> : null}
              <div className={s.actions}>
                {plataforma ? (
                  <a className="button button-secondary button-sm" href={plataforma.url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink size={14} aria-hidden="true" /> {plataforma.nombre}
                  </a>
                ) : null}
                {!enCurso && !obtenida ? (
                  <button
                    type="button"
                    className="button button-ghost button-sm"
                    disabled={preparar.isPending}
                    onClick={() => preparar.mutate(p.id)}
                  >
                    Me estoy preparando
                  </button>
                ) : null}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
