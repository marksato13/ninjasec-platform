"use client";

/**
 * Modo del panel: Todo, Ninja Sec o Ninja Dev (plan 34).
 *
 * Es una PREFERENCIA DE VISTA, no un permiso: filtra lo que el frontend muestra y
 * nunca cambia lo que el backend deja hacer. Se guarda en el navegador; si el
 * almacenamiento está bloqueado, el modo vive solo en memoria y la pantalla
 * funciona igual.
 *
 * Sin proveedor de React: un almacén mínimo con `useSyncExternalStore`, así
 * cualquier componente lo lee con `useModo()` sin envolver el layout.
 */

import { useSyncExternalStore } from "react";

export type Modo = "todo" | "sec" | "dev";
export type Linea = "sec" | "dev";

const CLAVE = "ninjatech_modo";
const MODOS: readonly Modo[] = ["todo", "sec", "dev"];

let actual: Modo = "todo";
let leido = false;
const oyentes = new Set<() => void>();

function leerGuardado(): Modo {
  try {
    const v = window.localStorage.getItem(CLAVE);
    return MODOS.includes(v as Modo) ? (v as Modo) : "todo";
  } catch {
    return "todo";
  }
}

function aplicarAlDocumento(modo: Modo) {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.mode = modo;
}

function asegurarLeido() {
  if (leido || typeof window === "undefined") return;
  leido = true;
  actual = leerGuardado();
  aplicarAlDocumento(actual);
}

export function setModo(modo: Modo) {
  asegurarLeido();
  if (modo === actual) return;
  actual = modo;
  try {
    window.localStorage.setItem(CLAVE, modo);
  } catch {
    /* almacenamiento bloqueado: el modo dura lo que dure la pestaña */
  }
  aplicarAlDocumento(modo);
  oyentes.forEach((f) => f());
}

function suscribir(f: () => void) {
  oyentes.add(f);
  return () => oyentes.delete(f);
}

function instantanea(): Modo {
  asegurarLeido();
  return actual;
}

/** En el servidor siempre "todo": el primer render coincide y luego se ajusta. */
export function useModo(): Modo {
  return useSyncExternalStore(suscribir, instantanea, () => "todo");
}

/** ¿Algo de esta línea se muestra en este modo? Sin línea (null) = de las dos. */
export function visibleEnModo(linea: Linea | null | undefined, modo: Modo): boolean {
  return modo === "todo" || !linea || linea === modo;
}

export const NOMBRE_MODO: Record<Modo, string> = {
  todo: "Todo",
  sec: "Ninja Sec",
  dev: "Ninja Dev",
};
