/**
 * Diccionarios de etiquetas en español para enums de backend que se
 * mostraban en crudo (en inglés) en 2+ páginas del dashboard/portal.
 * Valores confirmados contra app/db/models/enums.py -- no adivinados.
 *
 * No reemplaza `lib/role-utils.ts` (roles, accesos, badges) ni las
 * funciones ya agregadas ahí para catálogos de Aprobaciones
 * (getApprovalStatusLabel/getDocScopeLabel/getDocVisibilityLabel) --
 * este archivo es para los enums que aparecen fuera de esa página.
 */

// FindingSeverity + TicketPriority + DeviceCriticality comparten el mismo
// vocabulario (critical/high/medium/low[/info]) y la misma traducción
// natural -- un solo diccionario cubre los tres.
const SEVERITY_LABEL: Record<string, string> = {
  critical: "Critica",
  high: "Alta",
  medium: "Media",
  low: "Baja",
  info: "Info",
  unknown: "Desconocida",
};

export function getSeverityLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return SEVERITY_LABEL[normalized] ?? value;
}

// TicketStatus (app/db/models/enums.py)
const TICKET_STATUS_LABEL: Record<string, string> = {
  open: "Abierto",
  in_progress: "En progreso",
  pending: "Pendiente",
  resolved: "Resuelto",
  closed: "Cerrado",
};

export function getTicketStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return TICKET_STATUS_LABEL[normalized] ?? value;
}

// ReviewStatus (app/db/models/enums.py)
const REVIEW_STATUS_LABEL: Record<string, string> = {
  scheduled: "Programada",
  in_progress: "En progreso",
  closed: "Cerrada",
};

export function getReviewStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return REVIEW_STATUS_LABEL[normalized] ?? value;
}

// Device.status es texto libre (no un StrEnum), pero devices/page.tsx ya
// fija el vocabulario real via STATUS_OPTIONS.
const DEVICE_STATUS_LABEL: Record<string, string> = {
  active: "Activo",
  maintenance: "En mantenimiento",
  pending_review: "Pendiente de revision",
  offline: "Fuera de linea",
  decommissioned: "Dado de baja",
  unknown: "Desconocido",
};

export function getDeviceStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return DEVICE_STATUS_LABEL[normalized] ?? value;
}

// FindingStatus (app/db/models/enums.py)
const FINDING_STATUS_LABEL: Record<string, string> = {
  open: "Abierto",
  in_progress: "En progreso",
  resolved: "Resuelto",
  accepted: "Aceptado",
};

export function getFindingStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return FINDING_STATUS_LABEL[normalized] ?? value;
}

// RecommendationStatus (app/db/models/enums.py)
const RECOMMENDATION_STATUS_LABEL: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En progreso",
  completed: "Completada",
  cancelled: "Cancelada",
};

export function getRecommendationStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return RECOMMENDATION_STATUS_LABEL[normalized] ?? value;
}

// ProjectStatus (app/db/models/enums.py)
const PROJECT_STATUS_LABEL: Record<string, string> = {
  planning: "Planificacion",
  active: "Activo",
  paused: "Pausado",
  completed: "Completado",
};

export function getProjectStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return PROJECT_STATUS_LABEL[normalized] ?? value;
}

// DocStatus (app/db/models/enums.py) -- estado del documento en si, no
// confundir con DocVisibility (getDocVisibilityLabel en role-utils.ts).
const DOC_STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  active: "Activo",
  archived: "Archivado",
};

export function getDocStatusLabel(value: string): string {
  const normalized = value?.toLowerCase?.() ?? "";
  return DOC_STATUS_LABEL[normalized] ?? value;
}
