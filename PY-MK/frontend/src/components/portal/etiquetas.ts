/**
 * Textos del portal del cliente. El backend guarda codigos (NEW, high, status_change);
 * el cliente lee palabras. Un codigo que no esta aqui se muestra tal cual, para que un
 * estado nuevo no desaparezca de la pantalla.
 */

const SOLICITUD: Record<string, string> = {
  NEW: "Recibida",
  REVIEW: "En evaluación",
  CLOSED: "Cerrada",
};

export function estadoSolicitud(status: string, projectId?: number | null): string {
  if (status === "CLOSED" && projectId) return "Convertida en proyecto";
  return SOLICITUD[status] ?? status;
}

export function claseSolicitud(status: string, projectId?: number | null): string {
  if (status === "CLOSED" && projectId) return "badge-active";
  if (status === "NEW") return "badge-pending";
  if (status === "REVIEW") return "badge-draft";
  return "badge-archived";
}

export const PRIORIDADES: { value: string; label: string }[] = [
  { value: "low", label: "Baja" },
  { value: "medium", label: "Media" },
  { value: "high", label: "Alta" },
  { value: "critical", label: "Crítica" },
];

const EVENTO: Record<string, string> = {
  status_change: "Cambio de estado",
  comment: "Comentario",
  note: "Nota",
  assignment: "Asignación",
  created: "Creación",
};

const ESTADO_TICKET: Record<string, string> = {
  open: "abierto",
  in_progress: "en curso",
  pending: "esperando tu respuesta",
  resolved: "resuelto",
  closed: "cerrado",
};

export function eventoTicket(tipo: string): string {
  return EVENTO[tipo] ?? tipo.replaceAll("_", " ");
}

export function detalleEvento(notes: string | null | undefined, desde?: string | null, hacia?: string | null): string {
  if (notes) return notes;
  if (desde || hacia) {
    const a = desde ? ESTADO_TICKET[desde] ?? desde : "—";
    const b = hacia ? ESTADO_TICKET[hacia] ?? hacia : "—";
    return `De ${a} a ${b}`;
  }
  return "—";
}

/** Fechas del backend: UTC sin zona. Se muestran en hora de Lima. */
export function fechaHora(iso: string | null | undefined): string {
  if (!iso) return "—";
  const fecha = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  if (Number.isNaN(fecha.getTime())) return iso;
  return fecha.toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/Lima",
  });
}

export function fecha(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 10);
  return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric", timeZone: "America/Lima" });
}

export function hace(iso: string | null | undefined): string {
  if (!iso) return "sin avances publicados";
  const t = new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`).getTime();
  const s = Math.max(0, Math.round((Date.now() - t) / 1000));
  if (s < 3600) return "hace menos de una hora";
  if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
  const d = Math.floor(s / 86400);
  return d === 1 ? "ayer" : `hace ${d} días`;
}
