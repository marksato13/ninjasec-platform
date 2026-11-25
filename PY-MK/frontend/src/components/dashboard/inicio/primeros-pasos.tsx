"use client";

import Link from "next/link";
import { CheckCircle2, Circle } from "lucide-react";

import styles from "./inicio.module.css";

export type Paso = {
  clave: string;
  titulo: string;
  como: string;
  href: string;
  hecho: boolean;
};

/** Solo se muestra mientras falte algo; cada paso se comprueba contra datos reales. */
export function PrimerosPasos({ pasos }: { pasos: Paso[] }) {
  const hechos = pasos.filter((p) => p.hecho).length;
  return (
    <section className={styles.setup} aria-labelledby="pasos-titulo">
      <div className={styles.setupHead}>
        <h2 id="pasos-titulo" className={styles.cardTitle}>Primeros pasos para operar</h2>
        <span className={styles.setupProgress}>{hechos} de {pasos.length} listos</span>
      </div>
      <ul className={styles.steps}>
        {pasos.map((p) => (
          <li key={p.clave}>
            {p.hecho ? (
              <div className={`${styles.step} ${styles.stepDone}`}>
                <CheckCircle2 size={16} className={styles.stepCheck} aria-hidden="true" />
                <span className={styles.stepText}>
                  <span className={styles.stepTitle}>{p.titulo}</span>
                  <span className={styles.stepHow}>Listo</span>
                </span>
              </div>
            ) : (
              <Link href={p.href} className={styles.step}>
                <Circle size={16} className={styles.stepCheck} aria-hidden="true" />
                <span className={styles.stepText}>
                  <span className={styles.stepTitle}>{p.titulo}</span>
                  <span className={styles.stepHow}>{p.como}</span>
                </span>
              </Link>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
