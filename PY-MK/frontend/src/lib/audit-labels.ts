// Etiquetas legibles para la auditoría. El backend registra dos formatos:
// un verbo suelto ("create") o "entidad.verbo" ("client.created").
// Si un código no está aquí se muestra tal cual: nunca se oculta lo que pasó.

const VERB_LABELS: Record<string, string> = {
  create: "Creación",
  created: "Creación",
  update: "Edición",
  updated: "Edición",
  delete: "Eliminación",
  deleted: "Eliminación",
  retired: "Baja",
  closed: "Cierre",
  resolved: "Resolución",
  validate: "Validación",
  validated: "Validación",
  approved: "Aprobación",
  rejected: "Rechazo",
  login: "Inicio de sesión",
  logout: "Cierre de sesión",
  export: "Exportación",
  exported: "Exportación",
  assigned: "Asignación",
  status_changed: "Cambio de estado",
};

const ENTITY_LABELS: Record<string, string> = {
  client: "Cliente",
  clients: "Clientes",
  user: "Usuario",
  users: "Usuarios",
  integration: "Integración",
  device: "Equipo",
  review: "Revisión de seguridad",
  review_finding: "Hallazgo de revisión",
  ticket: "Ticket",
  support_ticket: "Ticket de soporte",
  job_application: "Postulación",
  project: "Proyecto",
  project_phase: "Fase de proyecto",
  nav_visibility: "Visibilidad del menú",
  study_enrollment: "Inscripción en formación",
  study_progress: "Avance en formación",
  service: "Servicio",
  service_request: "Solicitud de servicio",
};

function humanize(code: string): string {
  const text = code.replace(/[._]/g, " ").trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : code;
}

export function getAuditEntityLabel(entity: string | null | undefined): string {
  if (!entity) return "—";
  return ENTITY_LABELS[entity] ?? entity;
}

export function getAuditActionLabel(action: string | null | undefined): string {
  if (!action) return "—";
  if (VERB_LABELS[action]) return VERB_LABELS[action];
  const dot = action.lastIndexOf(".");
  if (dot > 0) {
    const entity = action.slice(0, dot);
    const verb = VERB_LABELS[action.slice(dot + 1)];
    if (verb) return ENTITY_LABELS[entity] ? `${verb} · ${ENTITY_LABELS[entity]}` : verb;
  }
  return action.includes(".") || action.includes("_") ? humanize(action) : action;
}
