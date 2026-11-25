"use client";

/**
 * Inicio del panel: la operación de Ninja Tech de un vistazo.
 *
 * Regla: solo datos reales del backend. Si un dato no carga se dice "No se pudo
 * cargar"; si no hay datos, se dice qué hacer. Nunca un número de relleno.
 * (Antes este panel mostraba alertas, tendencias y actividad inventadas cuando la
 * base estaba vacía, y un "score 100" calculado sin datos.)
 *
 * Orden de la pantalla = orden del servicio (ninjasec-empresa/OPERACIONES/flujos/
 * 01-ORDEN-DEL-SERVICIO.md): solicitudes y leads -> clientes -> proyectos por área
 * -> soporte. Las vistas de seguridad e infraestructura dependen de la cápsula de
 * telemetría y ya no viven aquí: las alertas solo se piden si la cápsula está activa.
 */

import { useQuery } from "@tanstack/react-query";

import {
  type AlertItem,
  type AreaItem,
  type AuditItem,
  type RiskItem,
  type SecurityReviewItem,
  type AuthUser,
  type CollaboratorProfile,
  type DashboardClient,
  type LeadItem,
  type ProjectItem,
  type ServiceItem,
  type ServiceRequestItem,
  type SupportTicketItem,
  getAlerts,
  getAreas,
  getAuditLogs,
  getClients,
  getCollaborators,
  getLeads,
  getMe,
  getProjects,
  getRisks,
  getSecurityReviews,
  getServiceRequests,
  getServices,
  getSupportTickets,
} from "@/lib/api";
import { capsulaActiva } from "@/lib/capsulas";
import { clientesEnModo, lineaDeProyecto, mapaDeAreas, proyectoEnModo } from "@/lib/lineas";
import { NOMBRE_MODO, useModo } from "@/lib/modo";
import { QK } from "@/lib/query-keys";

import { Actividad } from "./inicio/actividad";
import { Atencion, type Pendiente } from "./inicio/atencion";
import { Embudo, type Etapa } from "./inicio/embudo";
import { fechaLarga, nombreDeUsuario, saludoSegunHora } from "./inicio/formato";
import { PrimerosPasos, type Paso } from "./inicio/primeros-pasos";
import styles from "./inicio/inicio.module.css";
import { VistaDev, VistaSec } from "./inicio/vista-linea";

const TICKET_ABIERTO = new Set(["open", "in_progress", "pending"]);
const PROYECTO_VIVO = new Set(["planning", "active", "paused"]);
const LEAD_CERRADO = new Set(["WON", "LOST", "CONVERTED"]);
const TELEMETRIA = capsulaActiva("telemetria");

export function DashboardShell() {
  const yo = useQuery<AuthUser>({ queryKey: QK.me(), queryFn: getMe });
  const solicitudes = useQuery<ServiceRequestItem[]>({ queryKey: QK.serviceRequests(), queryFn: getServiceRequests });
  const leads = useQuery<LeadItem[]>({ queryKey: QK.leads(), queryFn: getLeads });
  const clientes = useQuery<DashboardClient[]>({ queryKey: QK.clients(), queryFn: () => getClients() });
  const proyectos = useQuery<ProjectItem[]>({ queryKey: QK.projects(), queryFn: getProjects });
  const areas = useQuery<AreaItem[]>({ queryKey: QK.areas(), queryFn: getAreas });
  const tickets = useQuery<SupportTicketItem[]>({ queryKey: QK.tickets(), queryFn: () => getSupportTickets() });
  const servicios = useQuery<ServiceItem[]>({ queryKey: QK.services(), queryFn: getServices });
  const colaboradores = useQuery<CollaboratorProfile[]>({ queryKey: QK.collaborators(), queryFn: getCollaborators });
  const auditoria = useQuery<AuditItem[]>({ queryKey: QK.auditLogs(8), queryFn: () => getAuditLogs(8) });
  const alertas = useQuery<AlertItem[]>({ queryKey: QK.alerts(undefined), queryFn: () => getAlerts(), enabled: TELEMETRIA });

  // Modo Ninja Sec / Ninja Dev (plan 34): filtra lo que se muestra, no lo que se puede hacer.
  // Lo comercial (solicitudes y leads) es común a las dos líneas y no se filtra.
  const modo = useModo();
  const revisiones = useQuery<SecurityReviewItem[]>({ queryKey: QK.reviews(undefined), queryFn: () => getSecurityReviews(), enabled: modo === "sec" });
  const riesgos = useQuery<RiskItem[]>({ queryKey: QK.risks(undefined), queryFn: () => getRisks(), enabled: modo === "sec" });

  const nombre = nombreDeUsuario(yo.data?.full_name ?? yo.data?.name);

  // ── El embudo ───────────────────────────────────────────────
  const nuevas = (solicitudes.data ?? []).filter((s) => s.status === "NEW").length;
  const leadsAbiertos = (leads.data ?? []).filter((l) => !LEAD_CERRADO.has(l.status));
  const leadsNuevos = leadsAbiertos.filter((l) => l.status === "NEW").length;
  const areaPorId = mapaDeAreas(areas.data);
  const proyectosDelModo = (proyectos.data ?? []).filter((p) => proyectoEnModo(p, areaPorId, modo));
  const vivos = proyectosDelModo.filter((p) => PROYECTO_VIVO.has(p.status));
  const porArea = { sec: 0, dev: 0, otra: 0 };
  for (const p of vivos) porArea[lineaDeProyecto(p, areaPorId) ?? "otra"] += 1;
  const clienteEnModo = clientesEnModo(proyectos.data, areaPorId, modo);
  const abiertos = (tickets.data ?? []).filter((t) => TICKET_ABIERTO.has(t.status) && clienteEnModo(t.client_id));
  const sinAsignar = abiertos.filter((t) => !t.assigned_to).length;
  const clientesActivos = (clientes.data ?? []).filter((c) => c.commercial_status !== "inactive" && clienteEnModo(c.id)).length;
  const clientesDeProyectos = new Set(proyectosDelModo.map((p) => p.client_id).filter((id): id is number => Boolean(id)));

  const etapas: Etapa[] = [
    {
      clave: "solicitudes",
      etiqueta: "Solicitudes",
      href: "/dashboard/services",
      valor: solicitudes.data?.length,
      detalle: nuevas ? `${nuevas} sin revisar` : "Ninguna por revisar",
      error: solicitudes.isError,
      cargando: solicitudes.isLoading,
    },
    {
      clave: "leads",
      etiqueta: "Leads abiertos",
      href: "/dashboard/leads",
      valor: leads.data ? leadsAbiertos.length : undefined,
      detalle: leadsNuevos ? `${leadsNuevos} sin contactar` : "Ninguno sin contactar",
      error: leads.isError,
      cargando: leads.isLoading,
    },
    {
      clave: "clientes",
      etiqueta: "Clientes",
      href: "/dashboard/clients",
      valor: clientes.data ? clientesActivos : undefined,
      detalle: clientes.data && clientes.data.length !== clientesActivos ? `${clientes.data.length} en total` : "Activos",
      error: clientes.isError,
      cargando: clientes.isLoading,
    },
    {
      clave: "proyectos",
      etiqueta: "Proyectos en curso",
      href: "/dashboard/projects",
      valor: proyectos.data ? vivos.length : undefined,
      areas: proyectos.data ? porArea : undefined,
      error: proyectos.isError,
      cargando: proyectos.isLoading,
    },
    {
      clave: "tickets",
      etiqueta: "Tickets abiertos",
      href: "/dashboard/support-tickets",
      valor: tickets.data ? abiertos.length : undefined,
      detalle: sinAsignar ? `${sinAsignar} sin asignar` : "Ninguno sin asignar",
      error: tickets.isError,
      cargando: tickets.isLoading,
    },
  ];

  // ── La bandeja de pendientes ────────────────────────────────
  const pendientes: Pendiente[] = [];
  for (const s of solicitudes.data ?? []) {
    if (s.status !== "NEW") continue;
    pendientes.push({
      clave: `sol-${s.id}`,
      tipo: "solicitud",
      titulo: `Revisar la solicitud de ${s.requester_name}`,
      sub: s.message || s.requester_email,
      cuando: s.created_at,
      href: "/dashboard/services",
    });
  }
  for (const l of leads.data ?? []) {
    if (l.status !== "NEW") continue;
    pendientes.push({
      clave: `lead-${l.id}`,
      tipo: "lead",
      titulo: `Contactar a ${l.contact_name}`,
      sub: l.company_name || l.email,
      cuando: l.created_at,
      href: "/dashboard/leads",
    });
  }
  for (const t of abiertos) {
    if (t.assigned_to) continue;
    pendientes.push({
      clave: `tk-${t.id}`,
      tipo: t.priority === "critical" || t.priority === "high" ? "urgente" : "ticket",
      titulo: `Asignar el ticket #${t.id}: ${t.title}`,
      sub: `Prioridad ${t.priority}`,
      cuando: t.opened_at ?? t.created_at,
      href: "/dashboard/support-tickets",
    });
  }
  for (const a of TELEMETRIA ? alertas.data ?? [] : []) {
    pendientes.push({
      clave: `al-${a.type}-${a.entity_type}-${a.entity_id}`,
      tipo: a.severity === "critical" || a.severity === "high" ? "urgente" : "alerta",
      titulo: a.message,
      sub: "Alerta de telemetría",
      cuando: a.created_at,
    });
  }
  pendientes.sort((x, y) => (y.cuando ?? "").localeCompare(x.cuando ?? ""));
  const fuentesConError = [solicitudes, leads, tickets].filter((q) => q.isError).length;

  // ── Primeros pasos: solo con todas las listas cargadas, para no afirmar nada sin datos ──
  const listasCargadas = [areas, servicios, clientes, proyectos, colaboradores].every((q) => q.data);
  const pasos: Paso[] = listasCargadas
    ? [
        { clave: "areas", titulo: "Áreas Ninja Sec y Ninja Dev", como: "Configuración › Áreas", href: "/dashboard/settings", hecho: (areas.data ?? []).some((a) => a.is_active) },
        { clave: "servicios", titulo: "Servicios publicados", como: "Servicios › Nuevo servicio", href: "/dashboard/services", hecho: (servicios.data ?? []).some((s) => s.active) },
        { clave: "colaborador", titulo: "Primer colaborador", como: "Colaboradores › Nuevo colaborador", href: "/dashboard/collaborators", hecho: (colaboradores.data ?? []).length > 0 },
        { clave: "cliente", titulo: "Primer cliente", como: "Clientes › Nuevo, o convierte un lead", href: "/dashboard/clients", hecho: (clientes.data ?? []).length > 0 },
        { clave: "proyecto", titulo: "Primer proyecto", como: "Proyectos › Nuevo proyecto", href: "/dashboard/projects", hecho: (proyectos.data ?? []).length > 0 },
      ]
    : [];
  const faltaAlgo = pasos.some((p) => !p.hecho);

  const hoy = new Date();

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <div>
          <h1 className={styles.greeting} suppressHydrationWarning>
            {saludoSegunHora(hoy)}
            {nombre ? `, ${nombre}` : ""}
          </h1>
          <p className={styles.date} suppressHydrationWarning>
            {fechaLarga(hoy)}
            {modo !== "todo" ? ` · Vista ${NOMBRE_MODO[modo]}` : ""}
          </p>
        </div>
      </header>

      {faltaAlgo ? <PrimerosPasos pasos={pasos} /> : null}

      <Embudo etapas={etapas} />

      {modo === "dev" ? (
        <VistaDev
          proyectos={{ data: proyectosDelModo, isLoading: proyectos.isLoading || areas.isLoading, isError: proyectos.isError }}
          tickets={tickets}
          clientesDeProyectos={clientesDeProyectos}
        />
      ) : null}
      {modo === "sec" ? <VistaSec revisiones={revisiones} riesgos={riesgos} /> : null}

      <div className={styles.columns}>
        <Atencion
          pendientes={pendientes}
          cargando={solicitudes.isLoading || leads.isLoading || tickets.isLoading}
          fuentesConError={fuentesConError}
        />
        <Actividad eventos={auditoria.data ?? []} cargando={auditoria.isLoading} error={auditoria.isError} />
      </div>
    </div>
  );
}
