import type { Linea, Modo } from "@/lib/modo";
import { NOMBRE_MODO } from "@/lib/modo";

import styles from "./chip-linea.module.css";

/** Etiqueta de línea de negocio. Sin línea no pinta nada: no es "otra", es "de las dos". */
export function ChipLinea({ linea }: { linea: Linea | null | undefined }) {
  if (!linea) return null;
  return (
    <span className={styles.chip} data-linea={linea}>
      <span className={styles.punto} aria-hidden="true" />
      {NOMBRE_MODO[linea]}
    </span>
  );
}

/** Aviso bajo el título de una lista cuando el modo oculta parte de ella. */
export function AvisoModo({ modo, visibles, total }: { modo: Modo; visibles: number; total: number }) {
  if (modo === "todo" || total === 0) return null;
  return (
    <p className={styles.aviso} role="status">
      Vista {NOMBRE_MODO[modo]}: {visibles} de {total}. Cambia a «Todo» en la cabecera para ver el resto.
    </p>
  );
}
