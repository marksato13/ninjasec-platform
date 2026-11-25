"use client";

/**
 * Selector de modo del panel: Todo · Ninja Sec · Ninja Dev (plan 34).
 *
 * Grupo de radios con aspecto de control segmentado: se navega con flechas como
 * cualquier radiogroup nativo y el lector de pantalla anuncia el modo activo.
 * Solo para super_admin y admin; el resto ve todo.
 */

import { Code2, LayoutGrid, ShieldCheck } from "lucide-react";
import { useId } from "react";

import { type Modo, NOMBRE_MODO, setModo, useModo } from "@/lib/modo";

import styles from "./selector-modo.module.css";

const OPCIONES: { modo: Modo; Icono: typeof LayoutGrid }[] = [
  { modo: "todo", Icono: LayoutGrid },
  { modo: "sec", Icono: ShieldCheck },
  { modo: "dev", Icono: Code2 },
];

export function SelectorModo() {
  const modo = useModo();
  const nombre = useId();

  return (
    <fieldset className={styles.grupo} data-modo={modo}>
      <legend className={styles.oculto}>Modo del panel</legend>
      {OPCIONES.map(({ modo: m, Icono }) => (
        <label key={m} className={styles.opcion} data-activo={modo === m} data-linea={m}>
          <input
            className={styles.oculto}
            type="radio"
            name={nombre}
            value={m}
            checked={modo === m}
            onChange={() => setModo(m)}
          />
          <Icono size={14} strokeWidth={2} aria-hidden="true" />
          <span className={styles.texto}>{NOMBRE_MODO[m]}</span>
        </label>
      ))}
    </fieldset>
  );
}
