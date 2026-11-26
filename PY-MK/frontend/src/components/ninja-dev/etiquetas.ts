import type { EstadoSistema, PlanSoporte, ResultadoDespliegue, TipoEntorno } from "@/lib/api";

/** Etiquetas compartidas por las pantallas de Ninja Dev (plan 35). */

export const ESTADO_SISTEMA: Record<EstadoSistema, { label: string; cls: string }> = {
  en_construccion:  { label: "En construcción",  cls: "badge-info" },
  en_produccion:    { label: "En producción",    cls: "badge-active" },
  en_mantenimiento: { label: "En mantenimiento", cls: "badge-pending" },
  retirado:         { label: "Retirado",         cls: "badge-archived" },
};

/** Sin precios: los planes se cotizan fuera del repositorio. */
export const PLAN_SOPORTE: Record<PlanSoporte, string> = {
  ninguno: "Sin plan",
  basico: "Básico",
  profesional: "Profesional",
  a_medida: "A medida",
};

export const ENTORNO: Record<TipoEntorno, { label: string; cls: string }> = {
  dev:     { label: "Desarrollo", cls: "badge-draft" },
  staging: { label: "Pruebas",    cls: "badge-info" },
  prod:    { label: "Producción", cls: "badge-active" },
};

export const RESULTADO: Record<ResultadoDespliegue, { label: string; cls: string }> = {
  ok:        { label: "Salió bien", cls: "badge-active" },
  fallido:   { label: "Falló",      cls: "badge-rejected" },
  revertido: { label: "Revertido",  cls: "badge-expired" },
};

/** Fecha corta. Las fechas sin hora (YYYY-MM-DD) no se corren un día por la zona. */
export function fechaCorta(iso?: string | null): string {
  if (!iso) return "—";
  const soloFecha = /^\d{4}-\d{2}-\d{2}$/.test(iso);
  const d = soloFecha
    ? new Date(`${iso}T12:00:00`)
    : new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  return soloFecha
    ? d.toLocaleDateString("es-PE", { dateStyle: "medium" })
    : d.toLocaleString("es-PE", { dateStyle: "medium", timeStyle: "short" });
}

/** Días que faltan para una fecha (negativo si ya pasó). */
export function diasHasta(iso?: string | null): number | null {
  if (!iso) return null;
  const d = new Date(/^\d{4}-\d{2}-\d{2}$/.test(iso) ? `${iso}T12:00:00` : iso);
  return Math.round((d.getTime() - Date.now()) / 86_400_000);
}

export function textoVence(iso?: string | null): string {
  const d = diasHasta(iso);
  if (d === null) return "—";
  if (d < 0) return `venció hace ${-d} d`;
  if (d === 0) return "vence hoy";
  return `vence en ${d} d`;
}

/** Mensaje del error tal como lo manda la API (viene en español). */
export function mensajeError(err: unknown): string | undefined {
  return err instanceof Error ? err.message : undefined;
}
