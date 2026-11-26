"use client";

import Link from "next/link";
import { useQueries, useQuery } from "@tanstack/react-query";
import { AppWindow, CalendarClock, ClipboardCheck, GitPullRequestArrow } from "lucide-react";

import {
  getAcceptanceCases,
  getClientSystems,
  getDeployments,
  getProjects,
  getSupportTickets,
  type ProjectItem,
  type SupportTicketItem,
} from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { ENTORNO, ESTADO_SISTEMA, RESULTADO, fechaCorta, textoVence } from "@/components/ninja-dev/etiquetas";
import s from "@/components/ninja-dev/ninja-dev.module.css";

const ABIERTO = new Set(["open", "in_progress", "pending"]);
// Tope de proyectos que se consultan para UAT: una llamada por proyecto.
const MAX_PROYECTOS_UAT = 25;

/** 35-P-08: solo datos reales de sistemas, despliegues, cambios y UAT. */
export default function PanelNinjaDevPage() {
  const sistemasQ = useQuery({ queryKey: QK.clientSystems(undefined), queryFn: () => getClientSystems() });
  const desplieguesQ = useQuery({ queryKey: QK.deployments({}), queryFn: () => getDeployments({}) });
  const ticketsQ = useQuery<SupportTicketItem[]>({ queryKey: QK.tickets({}), queryFn: () => getSupportTickets({}) });
  const proyectosQ = useQuery<ProjectItem[]>({ queryKey: QK.projects(), queryFn: getProjects });

  const proyectos = (proyectosQ.data ?? []).slice(0, MAX_PROYECTOS_UAT);
  const uat = useQueries({
    queries: proyectos.map((p) => ({
      queryKey: QK.acceptance(p.id),
      queryFn: () => getAcceptanceCases(p.id),
      retry: false,
    })),
  });

  const sistemas = sistemasQ.data?.systems ?? [];
  const enProduccion = sistemas.filter((x) => x.status === "en_produccion" || x.status === "en_mantenimiento");
  const porVencer = sistemas.filter((x) => x.warranty_expiring || x.environments.some((e) => e.expiring_soon));

  const despliegues = desplieguesQ.data?.deployments ?? [];
  const ultimos = despliegues.slice(0, 6);
  const conProblema = despliegues.filter((d) => d.result !== "ok").slice(0, 6);

  const cambios = (ticketsQ.data ?? []).filter((t) => t.kind === "cambio" && ABIERTO.has(t.status));
  const porEstimar = cambios.filter((t) => t.estimate_hours == null);
  const esperandoCliente = cambios.filter((t) => t.estimate_hours != null && !t.client_decision);

  const observados = uat
    .map((q, i) => ({ proyecto: proyectos[i], vista: q.data }))
    .filter((x) => x.vista && x.vista.summary.observado > 0);
  const listosParaActa = uat
    .map((q, i) => ({ proyecto: proyectos[i], vista: q.data }))
    .filter((x) => x.vista?.summary.ready_for_signoff);

  const nombreProyecto = (id: number) => proyectosQ.data?.find((p) => p.id === id)?.name ?? `Proyecto #${id}`;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ninja Dev</p>
          <h2>Panel Ninja Dev</h2>
          <p className="muted-small" style={{ margin: "4px 0 0" }}>
            Lo que necesita atención hoy en los sistemas que construimos y mantenemos.
          </p>
        </div>
      </div>

      <div className="metrics-grid">
        <Kpi icon={<AppWindow size={16} />} titulo="Sistemas en producción" valor={enProduccion.length}
          nota={`${sistemas.length} registrados`} cargando={sistemasQ.isLoading} />
        <Kpi icon={<CalendarClock size={16} />} titulo="Vencen en 30 días" valor={porVencer.length}
          nota="garantía, dominio o certificado" cargando={sistemasQ.isLoading} alerta={porVencer.length > 0} />
        <Kpi icon={<GitPullRequestArrow size={16} />} titulo="Cambios por mover" valor={porEstimar.length + esperandoCliente.length}
          nota={`${porEstimar.length} por estimar · ${esperandoCliente.length} esperan al cliente`} cargando={ticketsQ.isLoading} />
        <Kpi icon={<ClipboardCheck size={16} />} titulo="UAT con observaciones" valor={observados.length}
          nota={`${listosParaActa.length} listos para el acta`} cargando={proyectosQ.isLoading} />
      </div>

      <div className={s.panelGrid}>
        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Vencimientos</p><h3>Por vencer en 30 días</h3></div>
            <Link href="/dashboard/sistemas" className="muted-small">Ver sistemas</Link>
          </div>
          {porVencer.length === 0 ? (
            <p className={s.vacio}>Nada vence en los próximos 30 días.</p>
          ) : porVencer.map((x) => {
            const motivos: string[] = [];
            if (x.warranty_expiring) motivos.push(`garantía ${textoVence(x.warranty_until)}`);
            x.environments.filter((e) => e.expiring_soon).forEach((e) => {
              const fecha = [e.domain_expires_at, e.certificate_expires_at].filter(Boolean).sort()[0];
              motivos.push(`${ENTORNO[e.kind].label.toLowerCase()} ${textoVence(fecha)}`);
            });
            return (
              <Link key={x.id} href={`/dashboard/sistemas/${x.id}`} className={s.item}>
                <span>
                  <div className={s.nombre}>{x.name}</div>
                  <div className="muted-small">{x.client_name ?? `Cliente #${x.client_id}`}</div>
                </span>
                <span className={s.aviso}>{motivos.join(" · ")}</span>
              </Link>
            );
          })}
        </article>

        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Despliegues</p><h3>Fallidos o revertidos</h3></div>
            <Link href="/dashboard/despliegues" className="muted-small">Ver todos</Link>
          </div>
          {conProblema.length === 0 ? (
            <p className={s.vacio}>Ningún despliegue fallido ni revertido.</p>
          ) : conProblema.map((d) => (
            <Link key={d.id} href={`/dashboard/sistemas/${d.system_id}`} className={s.item}>
              <span>
                <div className={s.nombre}>{d.system_name} · {d.version}</div>
                <div className="muted-small">{ENTORNO[d.environment_kind].label} · {fechaCorta(d.deployed_at)}</div>
              </span>
              <span className={`badge ${RESULTADO[d.result].cls}`}>{RESULTADO[d.result].label}</span>
            </Link>
          ))}
        </article>

        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Solicitudes de cambio</p><h3>Esperando a alguien</h3></div>
            <Link href="/dashboard/support-tickets" className="muted-small">Ver tickets</Link>
          </div>
          {cambios.length === 0 ? (
            <p className={s.vacio}>No hay solicitudes de cambio abiertas.</p>
          ) : [...porEstimar, ...esperandoCliente].slice(0, 8).map((t) => (
            <Link key={t.id} href="/dashboard/support-tickets" className={s.item}>
              <span>
                <div className={s.nombre}>{t.title}</div>
                <div className="muted-small">Abierto {fechaCorta(t.opened_at)}</div>
              </span>
              {t.estimate_hours == null
                ? <span className="badge badge-pending">Por estimar</span>
                : <span className="badge badge-info">Espera al cliente · {t.estimate_hours} h</span>}
            </Link>
          ))}
        </article>

        <article className="panel">
          <div className="panel-head">
            <div><p className="eyebrow">Pruebas de aceptación</p><h3>Casos observados por el cliente</h3></div>
          </div>
          {observados.length === 0 && listosParaActa.length === 0 ? (
            <p className={s.vacio}>Ningún proyecto con casos observados.</p>
          ) : (
            <>
              {observados.map(({ proyecto, vista }) => (
                <Link key={proyecto.id} href={`/dashboard/projects/${proyecto.id}`} className={s.item}>
                  <span className={s.nombre}>{nombreProyecto(proyecto.id)}</span>
                  <span className="badge badge-rejected">{vista!.summary.observado} observados de {vista!.summary.total}</span>
                </Link>
              ))}
              {listosParaActa.map(({ proyecto }) => (
                <Link key={`acta-${proyecto.id}`} href={`/dashboard/projects/${proyecto.id}`} className={s.item}>
                  <span className={s.nombre}>{nombreProyecto(proyecto.id)}</span>
                  <span className="badge badge-active">Todo aprobado: proponer el acta</span>
                </Link>
              ))}
            </>
          )}
          {(proyectosQ.data?.length ?? 0) > MAX_PROYECTOS_UAT && (
            <p className="muted-small" style={{ margin: "8px 0 0" }}>Se revisan los {MAX_PROYECTOS_UAT} primeros proyectos.</p>
          )}
        </article>
      </div>

      <article className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Producción</p><h3>Últimos despliegues</h3></div>
        </div>
        {ultimos.length === 0 ? (
          <p className={s.vacio}>Aún no hay despliegues registrados.</p>
        ) : ultimos.map((d) => (
          <Link key={d.id} href={`/dashboard/sistemas/${d.system_id}`} className={s.item}>
            <span>
              <div className={s.nombre}>{d.system_name} · {d.version}</div>
              <div className="muted-small">{d.summary}</div>
            </span>
            <span className={s.etiquetas}>
              <span className={`badge ${ENTORNO[d.environment_kind].cls}`}>{ENTORNO[d.environment_kind].label}</span>
              <span className="muted-small">{fechaCorta(d.deployed_at)}</span>
            </span>
          </Link>
        ))}
        {enProduccion.length > 0 && (
          <p className="muted-small" style={{ margin: "10px 0 0" }}>
            En producción: {enProduccion.map((x) => `${x.name} (${ESTADO_SISTEMA[x.status].label.toLowerCase()})`).join(" · ")}
          </p>
        )}
      </article>
    </section>
  );
}

function Kpi({ icon, titulo, valor, nota, cargando, alerta }: {
  icon: React.ReactNode; titulo: string; valor: number; nota: string; cargando?: boolean; alerta?: boolean;
}) {
  return (
    <article className="metric-card panel">
      <div className="row-center">
        <span style={{ color: alerta ? "var(--warning)" : "var(--primary)", opacity: 0.8, display: "inline-flex" }}>{icon}</span>
        <span className="eyebrow m-0">{titulo}</span>
      </div>
      <strong style={{ fontSize: "2rem" }}>{cargando ? "…" : valor}</strong>
      <span className="muted-small">{nota}</span>
    </article>
  );
}
