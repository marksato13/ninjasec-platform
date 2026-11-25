"use client";

import Link from "next/link";
import { History } from "lucide-react";

import type { AuditItem } from "@/lib/api";

import { describirAccion, haceCuanto } from "./formato";
import styles from "./inicio.module.css";

export function Actividad({ eventos, cargando, error }: { eventos: AuditItem[]; cargando: boolean; error: boolean }) {
  return (
    <section className={styles.card} aria-labelledby="actividad-titulo">
      <div className={styles.cardHead}>
        <h2 id="actividad-titulo" className={styles.cardTitle}>Actividad reciente</h2>
        <Link href="/dashboard/audit" className={styles.cardMeta}>Ver auditoría</Link>
      </div>
      {error ? (
        <p className={styles.error} role="status">No se pudo cargar la auditoría.</p>
      ) : cargando ? (
        <p className={styles.empty}>Cargando actividad…</p>
      ) : eventos.length === 0 ? (
        <p className={styles.empty}>Todavía no hay actividad registrada. Cada alta, cambio o cierre quedará aquí.</p>
      ) : (
        <ul className={styles.list}>
          {eventos.map((ev) => (
            <li key={ev.id} className={styles.item}>
              <span className={styles.itemIcon}><History size={15} aria-hidden="true" /></span>
              <span className={styles.itemBody}>
                <span className={styles.itemTitle} style={{ display: "block" }}>
                  {describirAccion(ev.action, ev.entity_type)}
                  {ev.entity_id ? ` #${ev.entity_id}` : ""}
                </span>
              </span>
              <span className={styles.itemWhen}>{haceCuanto(ev.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
