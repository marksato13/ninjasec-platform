"use client";

import Link from "next/link";

import styles from "./inicio.module.css";

export type Etapa = {
  clave: string;
  etiqueta: string;
  href: string;
  /** undefined = no se sabe (cargando o error). Nunca se rellena con un número. */
  valor?: number;
  detalle?: string;
  areas?: { sec: number; dev: number; otra: number };
  error?: boolean;
  cargando?: boolean;
};

/**
 * El elemento protagonista del inicio: el orden del servicio como una sola fila,
 * de la solicitud al soporte. Cada etapa enlaza a su sección.
 */
export function Embudo({ etapas }: { etapas: Etapa[] }) {
  return (
    <section className={styles.funnel} aria-labelledby="embudo-titulo">
      <h2 id="embudo-titulo" className={styles.funnelTitle}>
        La operación hoy
        <span className={styles.funnelHint}>de la solicitud al soporte</span>
      </h2>
      <ol className={styles.stages}>
        {etapas.map((e) => {
          const sinDato = e.valor === undefined;
          const valor = e.cargando ? "…" : sinDato ? "—" : e.valor;
          const detalle = e.error ? "No se pudo cargar" : e.cargando ? "Cargando" : e.detalle;
          return (
            <li key={e.clave} className={styles.stage}>
              <Link href={e.href} className={styles.stageLink} aria-label={`${e.etiqueta}: ${sinDato ? "sin dato" : e.valor}. Abrir sección`}>
                <span className={styles.stageLabel}>{e.etiqueta}</span>
                <span className={`${styles.stageValue} ${sinDato || e.valor === 0 ? styles.stageValueEmpty : ""}`}>{valor}</span>
                {e.areas && !e.error ? (
                  <span className={styles.areas}>
                    <span className={styles.areaChip}>
                      <span className={`${styles.areaDot} ${styles.areaDotSec}`} aria-hidden="true" />
                      Ninja Sec {e.areas.sec}
                    </span>
                    <span className={styles.areaChip}>
                      <span className={`${styles.areaDot} ${styles.areaDotDev}`} aria-hidden="true" />
                      Ninja Dev {e.areas.dev}
                    </span>
                    {e.areas.otra ? (
                      <span className={styles.areaChip}>
                        <span className={styles.areaDot} aria-hidden="true" />
                        Sin línea {e.areas.otra}
                      </span>
                    ) : null}
                  </span>
                ) : (
                  <span className={styles.stageDetail}>{detalle}</span>
                )}
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
