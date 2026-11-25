"use client";

import { useQuery } from "@tanstack/react-query";
import { BadgeCheck, ExternalLink } from "lucide-react";

import { getProjectTeamCertifications } from "@/lib/api";
import { QK } from "@/lib/query-keys";

import s from "./formacion.module.css";
import { areaLabel, fecha } from "./utils";

/**
 * Para el cliente: quien trabaja en su proyecto y que certificaciones vigentes
 * tiene, validadas por Ninja Tech. Sin archivos ni datos de contacto.
 */
export function EquipoCertificado({ projectId }: { projectId: number }) {
  const equipo = useQuery({
    queryKey: QK.projectTeamCerts(projectId),
    queryFn: () => getProjectTeamCertifications(projectId),
    enabled: Number.isFinite(projectId) && projectId > 0,
  });

  if (equipo.isLoading || equipo.error) return null;
  const miembros = equipo.data ?? [];
  if (miembros.length === 0) return null;

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <h3>Equipo asignado y certificaciones</h3>
          <p className="muted-small" style={{ margin: 0 }}>
            Certificaciones vigentes que Ninja Tech verificó. Cada una se puede comprobar en la web del emisor.
          </p>
        </div>
      </div>
      <div className={s.grid}>
        {miembros.map((m) => (
          <section key={m.user_id} className={s.ruta}>
            <div>
              <h4>{m.full_name}</h4>
              {m.role_in_project ? <p className="muted-small" style={{ margin: 0 }}>{m.role_in_project}</p> : null}
            </div>
            {m.certifications.length === 0 ? (
              <p className="muted-small" style={{ margin: 0 }}>Sin certificaciones registradas todavía.</p>
            ) : (
              <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 }}>
                {m.certifications.map((c) => (
                  <li key={`${c.name}-${c.issued_at}`} style={{ display: "grid", gap: 2 }}>
                    <span style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
                      <BadgeCheck size={15} aria-hidden="true" style={{ color: "var(--success)" }} />
                      <strong>{c.name}</strong>
                    </span>
                    <span className="muted-small">
                      {[c.issuer, areaLabel(c.area), c.issued_at ? `emitida ${fecha(c.issued_at)}` : null,
                        c.expires_at ? `vigente hasta ${fecha(c.expires_at)}` : null]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    {c.url ? (
                      <a className={s.area} href={c.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink size={13} aria-hidden="true" /> Verificar en el emisor
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </article>
  );
}
