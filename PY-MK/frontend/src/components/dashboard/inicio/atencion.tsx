"use client";

import Link from "next/link";
import { AlertTriangle, Inbox, Ticket, UserPlus } from "lucide-react";

import { haceCuanto } from "./formato";
import styles from "./inicio.module.css";

export type Pendiente = {
  clave: string;
  tipo: "solicitud" | "lead" | "ticket" | "urgente" | "alerta";
  titulo: string;
  sub?: string | null;
  cuando?: string | null;
  href?: string;
};

const MAXIMO = 8;

function Icono({ tipo }: { tipo: Pendiente["tipo"] }) {
  if (tipo === "urgente") return <span className={`${styles.itemIcon} ${styles.itemIconDanger}`}><AlertTriangle size={15} aria-hidden="true" /></span>;
  if (tipo === "alerta") return <span className={`${styles.itemIcon} ${styles.itemIconWarn}`}><AlertTriangle size={15} aria-hidden="true" /></span>;
  if (tipo === "ticket") return <span className={`${styles.itemIcon} ${styles.itemIconWarn}`}><Ticket size={15} aria-hidden="true" /></span>;
  if (tipo === "lead") return <span className={styles.itemIcon}><UserPlus size={15} aria-hidden="true" /></span>;
  return <span className={styles.itemIcon}><Inbox size={15} aria-hidden="true" /></span>;
}

export function Atencion({
  pendientes,
  cargando,
  fuentesConError,
}: {
  pendientes: Pendiente[];
  cargando: boolean;
  fuentesConError: number;
}) {
  const visibles = pendientes.slice(0, MAXIMO);
  const resto = pendientes.length - visibles.length;

  return (
    <section className={styles.card} aria-labelledby="atencion-titulo">
      <div className={styles.cardHead}>
        <h2 id="atencion-titulo" className={styles.cardTitle}>Requiere tu atención</h2>
        {pendientes.length ? <span className={styles.cardMeta}>{pendientes.length} pendientes</span> : null}
      </div>

      {fuentesConError ? (
        <p className={styles.error} role="status">
          {fuentesConError === 1 ? "Una fuente no se pudo cargar" : `${fuentesConError} fuentes no se pudieron cargar`}; la lista puede estar incompleta.
        </p>
      ) : null}

      {cargando ? (
        <p className={styles.empty}>Cargando pendientes…</p>
      ) : visibles.length === 0 ? (
        <p className={styles.empty}>
          Nada pendiente. Aquí aparecen las solicitudes de servicio sin revisar, los leads sin contactar y los tickets sin asignar.
        </p>
      ) : (
        <ul className={styles.list}>
          {visibles.map((p) => {
            const contenido = (
              <>
                <Icono tipo={p.tipo} />
                <span className={styles.itemBody}>
                  <span className={styles.itemTitle} style={{ display: "block" }}>{p.titulo}</span>
                  {p.sub ? <span className={styles.itemSub} style={{ display: "block" }}>{p.sub}</span> : null}
                </span>
                <span className={styles.itemWhen}>{haceCuanto(p.cuando)}</span>
              </>
            );
            return (
              <li key={p.clave}>
                {p.href ? <Link href={p.href} className={styles.item}>{contenido}</Link> : <div className={styles.item}>{contenido}</div>}
              </li>
            );
          })}
        </ul>
      )}
      {resto > 0 ? <p className={styles.empty}>Y {resto} más en sus secciones.</p> : null}
    </section>
  );
}
