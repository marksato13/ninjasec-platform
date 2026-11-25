"use client";

/**
 * Vista propia de cada línea en el inicio del panel (plan 34).
 *
 * - Ninja Dev: proyectos de desarrollo por estado, próximas entregas (fecha de
 *   fin real del proyecto) y tickets abiertos de esos clientes.
 * - Ninja Sec: revisiones abiertas con sus hallazgos críticos y riesgos altos.
 *
 * Solo datos reales. Si una fuente falla se dice; si no hay nada, se dice qué
 * falta. Nunca un número de relleno.
 */

import Link from "next/link";

import type { ProjectItem, RiskItem, SecurityReviewItem, SupportTicketItem } from "@/lib/api";

import styles from "./vista-linea.module.css";

const ESTADOS_PROYECTO: { clave: string; nombre: string }[] = [
  { clave: "planning", nombre: "Planificación" },
  { clave: "active", nombre: "En curso" },
  { clave: "paused", nombre: "En pausa" },
  { clave: "completed", nombre: "Entregados" },
];

const DIA = 86_400_000;

function fechaCorta(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("es-PE", { day: "numeric", month: "short" });
}

function diasHasta(iso: string, hoy: number): number {
  return Math.round((new Date(`${iso}T00:00:00`).getTime() - hoy) / DIA);
}

type Fuente<T> = { data?: T; isLoading: boolean; isError: boolean };

function Estado({ fuente, vacio }: { fuente: Fuente<unknown>; vacio: string }) {
  if (fuente.isLoading) return <p className={styles.nota}>Cargando…</p>;
  if (fuente.isError) return <p className={styles.nota}>No se pudo cargar.</p>;
  return <p className={styles.nota}>{vacio}</p>;
}

export function VistaDev({
  proyectos,
  tickets,
  clientesDeProyectos,
}: {
  proyectos: Fuente<ProjectItem[]>;
  tickets: Fuente<SupportTicketItem[]>;
  clientesDeProyectos: Set<number>;
}) {
  const lista = proyectos.data ?? [];
  const hoy = new Date().setHours(0, 0, 0, 0);
  const conteo = ESTADOS_PROYECTO.map((e) => ({ ...e, n: lista.filter((p) => p.status === e.clave).length }));
  const maximo = Math.max(1, ...conteo.map((c) => c.n));

  const entregas = lista
    .filter((p) => p.end_date && p.status !== "completed" && p.status !== "cancelled")
    .map((p) => ({ p, dias: diasHasta(p.end_date as string, hoy) }))
    .filter((x) => x.dias <= 30)
    .sort((a, b) => a.dias - b.dias)
    .slice(0, 6);

  const abiertos = (tickets.data ?? []).filter(
    (t) => ["open", "in_progress", "pending"].includes(t.status) && clientesDeProyectos.has(t.client_id),
  );

  return (
    <section className={styles.vista} aria-labelledby="vista-dev" data-linea="dev">
      <h2 id="vista-dev" className={styles.titulo}>Ninja Dev</h2>
      <div className={styles.rejilla}>
        <div className={styles.bloque}>
          <h3>Proyectos por estado</h3>
          {lista.length === 0 ? (
            <Estado fuente={proyectos} vacio="Aún no hay proyectos de desarrollo." />
          ) : (
            <ul className={styles.barras}>
              {conteo.map((c) => (
                <li key={c.clave}>
                  <span className={styles.barraNombre}>{c.nombre}</span>
                  <span className={styles.barraPista} aria-hidden="true">
                    <span className={styles.barraValor} style={{ inlineSize: `${(c.n / maximo) * 100}%` }} />
                  </span>
                  <span className={styles.barraNumero}>{c.n}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className={styles.bloque}>
          <h3>Próximas entregas</h3>
          {entregas.length === 0 ? (
            <Estado
              fuente={proyectos}
              vacio={lista.length ? "Ningún proyecto vence en los próximos 30 días." : "Sin proyectos con fecha de entrega."}
            />
          ) : (
            <ul className={styles.lista}>
              {entregas.map(({ p, dias }) => (
                <li key={p.id}>
                  <Link href={`/dashboard/projects/${p.id}`}>{p.name}</Link>
                  <span className={dias < 0 ? styles.vencido : styles.cuando}>
                    {dias < 0 ? `Vencido hace ${-dias} d` : dias === 0 ? "Hoy" : `${fechaCorta(p.end_date as string)} · en ${dias} d`}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className={styles.bloque}>
          <h3>Tickets abiertos de sus clientes</h3>
          {tickets.isLoading || tickets.isError ? (
            <Estado fuente={tickets} vacio="" />
          ) : (
            <p className={styles.cifra}>
              <Link href="/dashboard/support-tickets">{abiertos.length}</Link>
              <span>{abiertos.length === 1 ? "ticket abierto" : "tickets abiertos"}</span>
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

export function VistaSec({
  revisiones,
  riesgos,
}: {
  revisiones: Fuente<SecurityReviewItem[]>;
  riesgos: Fuente<RiskItem[]>;
}) {
  const abiertas = (revisiones.data ?? []).filter((r) => r.status === "scheduled" || r.status === "in_progress");
  const criticos = abiertas.reduce((s, r) => s + (r.critical_findings_count ?? 0), 0);
  // Misma escala que la página de Riesgos: 12 o más es alto; 20 o más, crítico.
  const altos = (riesgos.data ?? [])
    .filter((r) => r.status !== "closed" && (r.residual_score ?? r.inherent_score) >= 12)
    .sort((a, b) => (b.residual_score ?? b.inherent_score) - (a.residual_score ?? a.inherent_score));

  return (
    <section className={styles.vista} aria-labelledby="vista-sec" data-linea="sec">
      <h2 id="vista-sec" className={styles.titulo}>Ninja Sec</h2>
      <div className={styles.rejilla}>
        <div className={styles.bloque}>
          <h3>Revisiones abiertas</h3>
          {revisiones.isLoading || revisiones.isError ? (
            <Estado fuente={revisiones} vacio="" />
          ) : (
            <p className={styles.cifra}>
              <Link href="/dashboard/security-reviews">{abiertas.length}</Link>
              <span>
                {abiertas.length === 0
                  ? "Ninguna programada ni en curso"
                  : criticos
                    ? `${criticos} ${criticos === 1 ? "hallazgo crítico" : "hallazgos críticos"}`
                    : "Sin hallazgos críticos"}
              </span>
            </p>
          )}
        </div>

        <div className={styles.bloque}>
          <h3>Riesgos altos</h3>
          {altos.length === 0 ? (
            <Estado fuente={riesgos} vacio="Ningún riesgo abierto con nivel alto." />
          ) : (
            <ul className={styles.lista}>
              {altos.slice(0, 5).map((r) => {
                const nivel = r.residual_score ?? r.inherent_score;
                return (
                  <li key={r.id}>
                    <Link href="/dashboard/risks">{r.title}</Link>
                    <span className={nivel >= 20 ? styles.vencido : styles.cuando}>
                      {nivel >= 20 ? "Crítico" : "Alto"} · {nivel}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
