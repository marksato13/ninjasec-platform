/** Utilidades de texto del inicio del panel. Sin datos inventados: si no hay fecha, "—". */

export function haceCuanto(iso?: string | null): string {
  if (!iso) return "—";
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "—";
  const minutos = Math.floor((Date.now() - fecha.getTime()) / 60000);
  if (minutos < 1) return "ahora";
  if (minutos < 60) return `hace ${minutos} min`;
  if (minutos < 1440) return `hace ${Math.floor(minutos / 60)} h`;
  const dias = Math.floor(minutos / 1440);
  return dias === 1 ? "ayer" : `hace ${dias} días`;
}

const VERBOS: Record<string, string> = {
  create: "Creó",
  created: "Creó",
  update: "Editó",
  updated: "Editó",
  delete: "Eliminó",
  deleted: "Eliminó",
  closed: "Cerró",
  close: "Cerró",
  converted: "Convirtió",
  approved: "Aprobó",
  rejected: "Rechazó",
  retired: "Retiró",
  login: "Inició sesión",
  requested: "Pidió",
  completed: "Completó",
  verified: "Verificó",
  assigned: "Asignó",
};

const ENTIDADES: Record<string, string> = {
  client: "un cliente",
  clients: "un cliente",
  user: "un usuario",
  users: "un usuario",
  project: "un proyecto",
  projects: "un proyecto",
  project_task: "una tarea",
  project_tasks: "una tarea",
  lead: "un lead",
  leads: "un lead",
  service: "un servicio",
  services: "un servicio",
  service_request: "una solicitud de servicio",
  service_requests: "una solicitud de servicio",
  support_ticket: "un ticket",
  support_tickets: "un ticket",
  ticket: "un ticket",
  security_review: "una revisión de seguridad",
  security_reviews: "una revisión de seguridad",
  review_finding: "un hallazgo",
  device: "un equipo",
  devices: "un equipo",
  integration: "una consola",
  integrations: "una consola",
  study_enrollment: "una inscripción a formación",
  study_enrollments: "una inscripción a formación",
  work_window: "una ventana de trabajo",
  work_windows: "una ventana de trabajo",
  nav_visibility: "los menús por rol",
  area: "un área",
  areas: "un área",
  project_type: "un tipo de proyecto",
  doc_type: "un tipo de documento",
};

/**
 * "client.created" + entidad "clients" -> "Creó un cliente".
 * Si la acción no se reconoce, se muestra tal cual: mejor un texto técnico que uno inventado.
 */
export function describirAccion(accion: string, entidad?: string | null): string {
  const partes = accion.split(".");
  const verbo = partes[partes.length - 1] ?? accion;
  const sujeto = partes.length > 1 ? partes.slice(0, -1).join("_") : entidad ?? "";
  const v = VERBOS[verbo.toLowerCase()];
  const e = ENTIDADES[sujeto.toLowerCase()] ?? ENTIDADES[(entidad ?? "").toLowerCase()];
  if (v && e) return `${v} ${e}`;
  if (v && entidad) return `${v} ${entidad.replace(/_/g, " ")}`;
  return accion;
}

export function nombreDeUsuario(nombre?: string | null): string {
  const limpio = (nombre ?? "").trim();
  return limpio ? limpio.split(/\s+/)[0] : "";
}

export function saludoSegunHora(fecha = new Date()): string {
  const h = fecha.getHours();
  if (h < 12) return "Buenos días";
  if (h < 19) return "Buenas tardes";
  return "Buenas noches";
}

export function fechaLarga(fecha = new Date()): string {
  const texto = fecha.toLocaleDateString("es-PE", { weekday: "long", day: "numeric", month: "long" });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}
