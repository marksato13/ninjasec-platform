// Marketing: de qué publicación llega cada contacto, y las redes de Ninja Tech.
//
// Cada pieza publicada lleva un enlace con marca, por ejemplo
// `/agenda-demo?origen=tiktok-03` (ninjasec-empresa, MARKETING/00-ESTRATEGIA.md).
// El formulario guarda esa marca en `lead.source`, para saber qué pieza trajo
// la reunión: es el único indicador que cuenta.

const ORIGEN_MAX = 40;

/** Limpia el valor de `?origen=`: minúsculas, letras, números y guiones. */
export function limpiarOrigen(valor: string | null | undefined): string | null {
  if (!valor) return null;
  const limpio = valor
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "")
    .slice(0, ORIGEN_MAX);
  return limpio || null;
}

/** Lee `?origen=` de la dirección actual (solo en el navegador). */
export function leerOrigen(): string | null {
  if (typeof window === "undefined") return null;
  return limpiarOrigen(new URLSearchParams(window.location.search).get("origen"));
}

/** `website` + origen → `website:tiktok-03`. Cabe en los 80 caracteres de `source`. */
export function etiquetaFuente(base: string, origen: string | null): string {
  return origen ? `${base}:${origen}` : base;
}

/**
 * Redes de Ninja Tech. Vacías hasta que existan las cuentas: el pie del sitio
 * solo muestra las que tienen dirección. Las URL llevan su propia marca de
 * origen al volver al sitio, no aquí.
 */
export const REDES: { nombre: string; url: string }[] = [
  { nombre: "LinkedIn", url: "" },
  { nombre: "Instagram", url: "" },
  { nombre: "Facebook", url: "" },
  { nombre: "TikTok", url: "" },
  { nombre: "YouTube", url: "" },
];
