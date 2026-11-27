"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppWindow, ExternalLink } from "lucide-react";

import { getClientSystems, getDeployments } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { ENTORNO, ESTADO_SISTEMA, PLAN_SOPORTE, fechaCorta, mensajeError, textoVence } from "@/components/ninja-dev/etiquetas";
import s from "@/components/ninja-dev/ninja-dev.module.css";

/**
 * 35-P-01 · Mis sistemas. El backend ya le quita al cliente el repositorio,
 * dónde están las claves y los entornos ocultos; y de los despliegues solo le
 * manda los de producción que llegaron, sin el checklist interno.
 */
export default function MisSistemasPage() {
  const { data, isLoading, error } = useQuery({ queryKey: QK.clientSystems(undefined), queryFn: () => getClientSystems() });
  const { data: desp } = useQuery({ queryKey: QK.deployments({}), queryFn: () => getDeployments({}) });

  const sistemas = data?.systems ?? [];
  const versiones = desp?.deployments ?? [];

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Tus sistemas</p>
          <h2>Mis sistemas</h2>
          <p className="muted-small" style={{ margin: "4px 0 0" }}>
            Lo que construimos para ti: dónde está publicado, hasta cuándo tiene garantía y qué versiones salieron.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="empty-state">Cargando…</div>
      ) : error ? (
        <div className="empty-state">No se pudieron cargar tus sistemas: {mensajeError(error)}</div>
      ) : sistemas.length === 0 ? (
        <div className="empty-state">
          <AppWindow size={20} style={{ opacity: 0.6 }} />
          <p style={{ margin: "6px 0 0" }}>Aún no tienes sistemas registrados con nosotros.</p>
        </div>
      ) : sistemas.map((x) => {
        const suyas = versiones.filter((d) => d.system_id === x.id).slice(0, 5);
        return (
          <article key={x.id} className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">{x.stack || "Sistema"}</p>
                <h3>{x.name}</h3>
              </div>
              <div className={s.etiquetas}>
                <span className={`badge ${ESTADO_SISTEMA[x.status].cls}`}>{ESTADO_SISTEMA[x.status].label}</span>
                {x.warranty_expiring && <span className="badge badge-pending">Garantía por vencer</span>}
              </div>
            </div>
            {x.description && <p style={{ marginTop: 0 }}>{x.description}</p>}
            <dl className={s.dl}>
              <dt className="muted-small">Plan de soporte</dt><dd>{PLAN_SOPORTE[x.support_plan]}</dd>
              <dt className="muted-small">Garantía hasta</dt>
              <dd>
                {fechaCorta(x.warranty_until)}
                {x.warranty_until && x.status !== "retirado" && (
                  <span className={x.warranty_expiring ? s.aviso : "muted-small"}> · {textoVence(x.warranty_until)}</span>
                )}
              </dd>
            </dl>

            {x.environments.length > 0 && (
              <div className={s.entornos} style={{ marginTop: 14 }}>
                {x.environments.map((e) => (
                  <div key={e.id} className={s.entorno}>
                    <span className={`badge ${ENTORNO[e.kind].cls}`} style={{ justifySelf: "start" }}>{ENTORNO[e.kind].label}</span>
                    {e.url ? (
                      <a href={e.url} target="_blank" rel="noreferrer noopener" className={s.celda}
                        style={{ display: "inline-flex", gap: 4, alignItems: "center", overflowWrap: "anywhere" }}>
                        {e.url} <ExternalLink size={12} />
                      </a>
                    ) : <span className="muted-small">Sin dirección publicada</span>}
                    {e.domain_expires_at && (
                      <span className={e.expiring_soon ? s.aviso : "muted-small"}>Dominio: {textoVence(e.domain_expires_at)}</span>
                    )}
                    {e.certificate_expires_at && (
                      <span className={e.expiring_soon ? s.aviso : "muted-small"}>Certificado: {textoVence(e.certificate_expires_at)}</span>
                    )}
                  </div>
                ))}
              </div>
            )}

            <h4 style={{ margin: "18px 0 6px", fontSize: "0.9rem" }}>Versiones publicadas</h4>
            {suyas.length === 0 ? (
              <p className={s.vacio}>Todavía no hay versiones publicadas.</p>
            ) : suyas.map((d) => (
              <div key={d.id} className={s.item}>
                <span>
                  <div className={s.nombre}>{d.version}</div>
                  <div className="muted-small">{d.summary}</div>
                </span>
                <span className={s.etiquetas}>
                  {d.result === "revertido" && <span className="badge badge-expired">Revertida</span>}
                  <span className="muted-small">{fechaCorta(d.deployed_at)}</span>
                </span>
              </div>
            ))}

            <p className="muted-small" style={{ margin: "12px 0 0" }}>
              ¿Algo falla o necesitas un cambio? <Link href="/portal/tickets">Abre un ticket</Link> y elige este sistema.
            </p>
          </article>
        );
      })}
    </section>
  );
}
