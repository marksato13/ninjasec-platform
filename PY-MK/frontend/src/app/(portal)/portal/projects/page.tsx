"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { getProjects, ProjectItem } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { ProyectoResumen } from "@/components/portal/proyecto-resumen";
import s from "@/components/portal/portal.module.css";

const CERRADOS = new Set(["closed", "completed", "cancelled", "canceled"]);

export default function PortalProjectsPage() {
  const { data: items = [], isLoading, error } = useQuery<ProjectItem[]>({
    queryKey: QK.projects(),
    queryFn: () => getProjects(),
  });

  const enCurso = items.filter((p) => !CERRADOS.has(p.status.toLowerCase()));
  const cerrados = items.filter((p) => CERRADOS.has(p.status.toLowerCase()));

  return (
    <section className="page-stack">
      <header className={s.saludo}>
        <h2>Proyectos</h2>
        <p>Toca un proyecto para ver su recorrido completo, el equipo y los avances.</p>
      </header>

      {error ? (
        <p className="form-error">{error instanceof Error ? error.message : "No se pudieron cargar los proyectos."}</p>
      ) : null}

      {isLoading ? (
        <div className={s.bloque}>
          <div className={s.esqueleto} aria-hidden="true" />
          <div className={s.esqueleto} aria-hidden="true" />
        </div>
      ) : items.length === 0 && !error ? (
        <div className={s.vacio}>
          <strong>Todavía no tienes proyectos.</strong>
          <span>Cuando una solicitud de servicio se convierta en proyecto, aparecerá aquí con su avance.</span>
          <Link className="button button-primary button-sm" href="/portal/services">
            Ver servicios
          </Link>
        </div>
      ) : (
        <>
          {enCurso.length > 0 ? (
            <section className={s.bloque} aria-labelledby="en-curso">
              <div className={s.bloqueTitulo}>
                <h3 id="en-curso">En curso</h3>
              </div>
              {enCurso.map((p) => <ProyectoResumen key={p.id} proyecto={p} />)}
            </section>
          ) : null}
          {cerrados.length > 0 ? (
            <section className={s.bloque} aria-labelledby="terminados">
              <div className={s.bloqueTitulo}>
                <h3 id="terminados">Terminados</h3>
              </div>
              {cerrados.map((p) => <ProyectoResumen key={p.id} proyecto={p} />)}
            </section>
          ) : null}
        </>
      )}
    </section>
  );
}
