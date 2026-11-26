"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AvisoModo } from "@/components/dashboard/chip-linea";
import { getAreas, getProjects } from "@/lib/api";
import { clientesEnModo, mapaDeAreas } from "@/lib/lineas";
import { useModo } from "@/lib/modo";

import {
  createSupportTicket,
  createSupportTicketEvent,
  createTicketFromFinding,
  DashboardClient,
  DashboardUser,
  deleteSupportTicket,
  exportSupportTicketsXlsx,
  getClients,
  getClientSystems,
  getSecurityReview,
  getSecurityReviews,
  getSupportTicket,
  getSupportTickets,
  getSupportTicketStats,
  getUsers,
  importSupportTickets,
  SecurityReviewDetail,
  SecurityReviewItem,
  SupportTicketDetail,
  SupportTicketItem,
  SupportTicketStats,
  TicketKind,
  updateSupportTicket,
} from "@/lib/api";
import { AvisoGarantia, BadgeFase, BadgeTipo, CambioEquipo } from "@/components/tickets/solicitud-cambio";
import { AlertTriangle, CheckCircle2, Clock, Inbox, Ticket as TicketIcon, Trash2 } from "lucide-react";
import { EmptyState } from "@/components/ui/empty-state";

import { confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { getStatusBadgeClass } from "@/lib/role-utils";
import { getSeverityLabel, getTicketStatusLabel } from "@/lib/labels";
import { eventoTicket } from "@/components/portal/etiquetas";
import { Modal } from "@/components/ui/modal";
import { BulkActionBar } from "@/components/ui/bulk-action-bar";
import { useBulkSelection } from "@/lib/hooks/use-bulk-selection";
import { QK } from "@/lib/query-keys";

const statuses = ["open", "in_progress", "pending", "resolved", "closed"];

const SLA_HOURS: Record<string, number> = { critical: 4, high: 8, medium: 24, low: 72 };

function isOverdue(ticket: SupportTicketItem): boolean {
  if (ticket.status === "resolved" || ticket.status === "closed") return false;
  const sla = SLA_HOURS[ticket.priority];
  if (!sla || !ticket.opened_at) return false;
  const hoursOpen = (Date.now() - new Date(ticket.opened_at).getTime()) / 3600000;
  return hoursOpen > sla;
}

function hoursOpen(ticket: SupportTicketItem): string {
  if (!ticket.opened_at) return "";
  const h = Math.floor((Date.now() - new Date(ticket.opened_at).getTime()) / 3600000);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}

export default function SupportTicketsPage() {
  const currentUser  = getStoredUser();
  const isSuperAdmin = currentUser?.role === "super_admin";
  const isAdmin      = currentUser?.role === "admin" || isSuperAdmin;
  const queryClient = useQueryClient();
  const [activeStatus, setActiveStatus] = useState("open");
  const [filters, setFilters] = useState({ client_id: "", priority: "", date_from: "", date_to: "" });
  const [detail, setDetail] = useState<SupportTicketDetail | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ client_id: "", title: "", priority: "medium", category: "support", assigned_to: "", description: "", kind: "incidencia" as TicketKind, system_id: "" });
  // 35-P-03: incidencias (algo falla) y solicitudes de cambio (algo nuevo).
  const [kindFilter, setKindFilter] = useState<"" | TicketKind>("");
  const [fromFindingOpen, setFromFindingOpen] = useState(false);
  const [findingReviewId, setFindingReviewId] = useState<number | null>(null);
  const [findingId, setFindingId] = useState<number | null>(null);
  const [findingPriority, setFindingPriority] = useState("medium");
  const [findingSaving, setFindingSaving] = useState(false);

  const ticketFilters = {
    client_id: filters.client_id ? Number(filters.client_id) : undefined,
    ticket_status: activeStatus,
    priority: filters.priority || undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
  };

  const { data: ticketsTodos = [] } = useQuery<SupportTicketItem[]>({
    queryKey: QK.tickets(ticketFilters),
    queryFn: () => getSupportTickets(ticketFilters),
  });

  // Modo Ninja Sec / Ninja Dev (plan 34). Los tickets no tienen proyecto: siguen la
  // línea de los proyectos de su cliente; un cliente sin proyectos cuenta para las dos.
  const modo = useModo();
  const { data: proyectosModo } = useQuery({ queryKey: ["modo", "proyectos"], queryFn: getProjects, enabled: modo !== "todo" });
  const { data: areasModo } = useQuery({ queryKey: QK.areas(), queryFn: getAreas, enabled: modo !== "todo" });
  const clienteEnModo = clientesEnModo(proyectosModo, mapaDeAreas(areasModo), modo);
  // El listado no filtra por tipo en la API: se filtra aquí.
  const tickets = ticketsTodos.filter((t) => clienteEnModo(t.client_id) && (!kindFilter || (t.kind ?? "incidencia") === kindFilter));

  // Nombres de los sistemas para la etiqueta de cada fila, y los del cliente elegido al crear.
  const { data: todosLosSistemas } = useQuery({ queryKey: QK.clientSystems(), queryFn: () => getClientSystems() });
  const nombreSistema = (id?: number | null) => (id ? todosLosSistemas?.systems.find((s) => s.id === id)?.name ?? `Sistema #${id}` : null);
  const { data: sistemasDelForm } = useQuery({
    queryKey: QK.clientSystems(Number(form.client_id) || undefined),
    queryFn: () => getClientSystems(Number(form.client_id)),
    enabled: createOpen && !!form.client_id,
  });

  const bulk = useBulkSelection(tickets.map((t) => t.id));

  async function handleBulkDelete() {
    const confirmed = await confirmDelete({
      title: `¿Eliminar ${bulk.count} ticket${bulk.count === 1 ? "" : "s"}?`,
      text: "Esta acción eliminará los tickets seleccionados permanentemente y no se puede deshacer.",
    });
    if (!confirmed) return;
    const ids = [...bulk.selected];
    const results = await Promise.allSettled(ids.map((id) => deleteSupportTicket(id)));
    const failed = results.filter((r) => r.status === "rejected").length;
    bulk.clear();
    load();
    if (failed > 0) notifyError("Algunos tickets no se pudieron eliminar", `${failed} de ${ids.length} fallaron`);
    else notifySuccess("Tickets eliminados");
  }

  const { data: clients = [] } = useQuery<DashboardClient[]>({
    queryKey: QK.clients(),
    queryFn: () => getClients(),
  });

  const { data: users = [] } = useQuery<DashboardUser[]>({
    queryKey: QK.users(),
    queryFn: () => getUsers(),
  });

  const statsFilters = {
    client_id: filters.client_id ? Number(filters.client_id) : undefined,
    date_from: filters.date_from || undefined,
  };
  const { data: stats } = useQuery<SupportTicketStats>({
    queryKey: ["ticket-stats", statsFilters],
    queryFn: () => getSupportTicketStats(statsFilters),
  });

  // ── From-finding: data sources ────────────────────────────────────────────
  const { data: allReviews = [] } = useQuery<SecurityReviewItem[]>({
    queryKey: QK.reviews({}),
    queryFn: () => getSecurityReviews({}),
    enabled: fromFindingOpen,
  });
  const { data: reviewDetail = null } = useQuery<SecurityReviewDetail | null>({
    queryKey: ["security-review", findingReviewId, "detail"],
    queryFn: () => (findingReviewId ? getSecurityReview(findingReviewId) : Promise.resolve(null)),
    enabled: !!findingReviewId,
  });

  async function handleCreateFromFinding() {
    if (!findingId) return;
    setFindingSaving(true);
    try {
      await createTicketFromFinding(findingId, { priority: findingPriority });
      notifySuccess("Ticket creado desde hallazgo");
      queryClient.invalidateQueries({ queryKey: QK.tickets(ticketFilters) });
      queryClient.invalidateQueries({ queryKey: ["ticket-stats", statsFilters] });
      setFromFindingOpen(false);
      setFindingReviewId(null);
      setFindingId(null);
      setFindingPriority("medium");
    } catch (err) {
      notifyError("No se pudo crear", err instanceof Error ? err.message : undefined);
    } finally {
      setFindingSaving(false);
    }
  }

  function load() {
    queryClient.invalidateQueries({ queryKey: QK.tickets(ticketFilters) });
  }

  function clientName(clientId: number) {
    return clients.find((item) => item.id === clientId)?.company_name || `Cliente ${clientId}`;
  }

  function userName(userId?: number | null) {
    return users.find((item) => item.id === userId)?.full_name || "-";
  }

  return (
    <section className="page-stack">
      <div className="section-heading"><div><p className="eyebrow">Admin</p><h2>Bandeja de tickets</h2><AvisoModo modo={modo} visibles={tickets.length} total={ticketsTodos.length} /></div></div>

      {/* KPI strip (P-02 stats) */}
      {stats ? (
        <div className="metrics-grid">
          <article className="metric-card panel">
            <div className="row-center">
              <TicketIcon size={16} style={{ color: "var(--primary)", opacity: 0.7 }} />
              <span className="eyebrow m-0">Tickets totales</span>
            </div>
            <strong style={{ fontSize: "2rem" }}>{stats.total}</strong>
            <span className="muted-small">
              {stats.open_count} abiertos · {stats.closed_count} cerrados
            </span>
          </article>

          <article className="metric-card panel">
            <div className="row-center">
              <AlertTriangle size={16} style={{ color: "var(--warning)", opacity: 0.7 }} />
              <span className="eyebrow m-0">Abiertos</span>
            </div>
            <strong style={{ fontSize: "2rem", color: stats.open_count > 0 ? "var(--warning)" : "var(--success)" }}>
              {stats.open_count}
            </strong>
            <span className="muted-small">
              {stats.by_priority.critical ? `${stats.by_priority.critical} críticos · ` : ""}
              {stats.by_priority.high ? `${stats.by_priority.high} altos` : "sin prioridad alta"}
            </span>
          </article>

          <article className="metric-card panel">
            <div className="row-center">
              <CheckCircle2 size={16} style={{ color: "var(--success)", opacity: 0.7 }} />
              <span className="eyebrow m-0">Cerrados</span>
            </div>
            <strong style={{ fontSize: "2rem", color: "var(--success)" }}>{stats.closed_count}</strong>
            <span className="muted-small">
              {stats.total > 0 ? `${Math.round((stats.closed_count / stats.total) * 100)}% del total` : "—"}
            </span>
          </article>

          <article className="metric-card panel">
            <div className="row-center">
              <Clock size={16} style={{ color: "var(--primary)", opacity: 0.7 }} />
              <span className="eyebrow m-0">Tiempo medio</span>
            </div>
            <strong style={{ fontSize: "2rem" }}>
              {stats.avg_resolution_hours != null ? `${stats.avg_resolution_hours}h` : "—"}
            </strong>
            <span className="muted-small">Resolución promedio</span>
          </article>
        </div>
      ) : null}

      <article className="panel filters-panel">
        <div className="filters-grid">
          <select value={filters.client_id} onChange={(e) => setFilters((current) => ({ ...current, client_id: e.target.value }))}>{" "}<option value="">Todos los clientes</option>{clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}</select>
          <select value={filters.priority} onChange={(e) => setFilters((current) => ({ ...current, priority: e.target.value }))}><option value="">Todas las prioridades</option>{["low", "medium", "high", "critical"].map((item) => <option key={item} value={item}>{getSeverityLabel(item)}</option>)}</select>
          <select aria-label="Tipo" value={kindFilter} onChange={(e) => setKindFilter(e.target.value as "" | TicketKind)}><option value="">Incidencias y cambios</option><option value="incidencia">Solo incidencias</option><option value="cambio">Solo solicitudes de cambio</option></select>
          <button className="button button-secondary" type="button" onClick={() => load()}>Aplicar</button>
        </div>
        <div className="filters-dates">
          <label>Desde<input type="date" value={filters.date_from} onChange={(e) => setFilters((current) => ({ ...current, date_from: e.target.value }))} /></label>
          <label>Hasta<input type="date" value={filters.date_to} onChange={(e) => setFilters((current) => ({ ...current, date_to: e.target.value }))} /></label>
        </div>
        <div className="panel-actions">
          <button className="button button-primary" type="button" onClick={() => setCreateOpen(true)}>Crear ticket</button>
          <button className="button button-secondary" type="button" onClick={() => setFromFindingOpen(true)}>Desde hallazgo</button>
          {isAdmin && <button className="button button-ghost" type="button" onClick={() => exportSupportTicketsXlsx({ client_id: filters.client_id ? Number(filters.client_id) : undefined, ticket_status: activeStatus, priority: filters.priority || undefined, date_from: filters.date_from || undefined, date_to: filters.date_to || undefined }).catch((err) => notifyError("No se pudo exportar", err instanceof Error ? err.message : undefined))}>Exportar XLSX</button>}
          {isAdmin && <label className="button button-secondary">Importar XLSX<input hidden type="file" accept=".xlsx,.xls" onChange={async (e) => { if (!e.target.files?.[0]) return; try { const result = await importSupportTickets(e.target.files[0]); notifySuccess(`Importados: ${result.created}`); load(); } catch (err) { notifyError("No se pudo importar", err instanceof Error ? err.message : undefined); } }} /></label>}
        </div>
      </article>
      <div className="tab-list">
        {statuses.map((s) => {
          const count = tickets.filter((t) => t.status === s).length;
          const overdueCount = tickets.filter((t) => t.status === s && isOverdue(t)).length;
          return (
            <button key={s} className={`tab ${activeStatus === s ? "tab-active" : ""}`} type="button" onClick={() => setActiveStatus(s)}>
              {getTicketStatusLabel(s)}
              {count > 0 && <span className="pill" style={{ marginLeft: 6 }}>{count}</span>}
              {overdueCount > 0 && <span style={{ marginLeft: 4, color: "var(--danger)", fontSize: "0.7rem", fontWeight: 700 }}>⚠{overdueCount}</span>}
            </button>
          );
        })}
      </div>

      {isSuperAdmin && (
        <BulkActionBar
          count={bulk.count}
          itemLabel="ticket"
          onClear={bulk.clear}
          actions={[{ label: "Eliminar", variant: "danger", icon: <Trash2 size={14} />, onClick: handleBulkDelete }]}
        />
      )}
      <article className="panel">
        <div className="table-like">
          <div className="table-row table-head" style={{ gridTemplateColumns: "28px 60px 1fr 140px auto auto auto" }}>
            {isSuperAdmin ? (
              <input type="checkbox" checked={bulk.allSelected} onChange={bulk.toggleAll} aria-label="Seleccionar todos los tickets" />
            ) : <span />}
            <span>ID</span><span>Título</span><span>Cliente</span><span>Prioridad</span><span>SLA</span><span>Estado</span>
          </div>
          {tickets.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="Bandeja al día"
              description={`No hay tickets con estado “${activeStatus}”. Crea uno a mano o a partir de un hallazgo.`}
              action={{ label: "Crear ticket", onClick: () => setCreateOpen(true) }}
            />
          ) : (
            tickets.map((ticket) => {
              const overdue = isOverdue(ticket);
              return (
                <div className="table-row" key={ticket.id} style={{ gridTemplateColumns: "28px 60px 1fr 140px auto auto auto", borderLeft: overdue ? "3px solid var(--danger)" : "3px solid transparent" }}>
                  {isSuperAdmin ? (
                    <input type="checkbox" checked={bulk.isSelected(ticket.id)} onChange={() => bulk.toggle(ticket.id)} aria-label={`Seleccionar ticket ${ticket.id}`} />
                  ) : <span />}
                  <span className="muted-small">#{ticket.id}</span>
                  <span style={{ display: "grid", gap: 4, minWidth: 0 }}>
                    <button className="button button-ghost" type="button" style={{ textAlign: "left", fontSize: "0.88rem", justifySelf: "start" }} onClick={async () => setDetail(await getSupportTicket(ticket.id))}>
                      {ticket.title}
                    </button>
                    <span style={{ display: "flex", flexWrap: "wrap", gap: 4, paddingLeft: 12 }}>
                      <BadgeTipo kind={ticket.kind} />
                      {nombreSistema(ticket.system_id) ? <span className="badge badge-draft">{nombreSistema(ticket.system_id)}</span> : null}
                      {ticket.kind === "cambio" ? <BadgeFase ticket={ticket} /> : <AvisoGarantia ticket={ticket} />}
                    </span>
                  </span>
                  <span className="muted-small">{clientName(ticket.client_id)}</span>
                  <span><span className={`badge ${getStatusBadgeClass(ticket.priority)}`}>{getSeverityLabel(ticket.priority)}</span></span>
                  <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    {overdue ? (
                      <span className="badge badge-rejected" style={{ fontSize: "0.68rem" }}>Vencido {hoursOpen(ticket)}</span>
                    ) : (
                      <span className="muted-small">{hoursOpen(ticket)}</span>
                    )}
                  </span>
                  <span><span className={`badge ${getStatusBadgeClass(ticket.status)}`}>{getTicketStatusLabel(ticket.status)}</span></span>
                </div>
              );
            })
          )}
        </div>
      </article>

      <Modal isOpen={createOpen} title="Crear ticket" onClose={() => setCreateOpen(false)}>
        <div className="entity-form">
          <select value={form.client_id} onChange={(e) => setForm((current) => ({ ...current, client_id: e.target.value, system_id: "" }))}><option value="">Cliente</option>{clients.map((client) => <option key={client.id} value={client.id}>{client.company_name}</option>)}</select>
          <select aria-label="Tipo" value={form.kind} onChange={(e) => setForm((current) => ({ ...current, kind: e.target.value as TicketKind }))}>
            <option value="incidencia">Incidencia: algo falla</option>
            <option value="cambio">Solicitud de cambio: algo nuevo sobre un sistema</option>
          </select>
          {form.client_id ? (
            <select aria-label="Sistema" value={form.system_id} onChange={(e) => setForm((current) => ({ ...current, system_id: e.target.value }))}>
              <option value="">{(sistemasDelForm?.systems.length ?? 0) > 0 ? (form.kind === "cambio" ? "Sistema sobre el que se pide el cambio" : "Sistema afectado (opcional)") : "El cliente no tiene sistemas registrados"}</option>
              {(sistemasDelForm?.systems ?? []).filter((s) => s.status !== "retirado").map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          ) : null}
          <input value={form.title} onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))} placeholder="Titulo" />
          <textarea value={form.description} onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))} placeholder="Descripcion" rows={4} />
          <select value={form.priority} onChange={(e) => setForm((current) => ({ ...current, priority: e.target.value }))}>{["low","medium","high","critical"].map((item) => <option key={item} value={item}>{getSeverityLabel(item)}</option>)}</select>
          <select value={form.category} onChange={(e) => setForm((current) => ({ ...current, category: e.target.value }))}><option value="support">Soporte</option><option value="incident">Incidente</option><option value="request">Solicitud</option><option value="maintenance">Mantenimiento</option></select>
          {isAdmin && <select value={form.assigned_to} onChange={(e) => setForm((current) => ({ ...current, assigned_to: e.target.value }))}><option value="">Asignado a</option>{users.map((user) => <option key={user.id} value={user.id}>{user.full_name}</option>)}</select>}
          <button className="button button-primary" type="button" disabled={!form.client_id || !form.title || (form.kind === "cambio" && !form.system_id)} onClick={async () => { if (!form.client_id || !form.title) return; if (form.kind === "cambio" && !form.system_id) return; try { await createSupportTicket({ client_id: Number(form.client_id), title: form.title, description: form.description || null, category: form.category, priority: form.priority, assigned_to: form.assigned_to ? Number(form.assigned_to) : null, kind: form.kind, system_id: form.system_id ? Number(form.system_id) : null }); notifySuccess(form.kind === "cambio" ? "Solicitud de cambio creada" : "Ticket creado"); setCreateOpen(false); setForm((current) => ({ ...current, title: "", description: "", system_id: "" })); queryClient.invalidateQueries({ queryKey: ["tickets"] }); } catch (err) { notifyError("No se pudo crear", err instanceof Error ? err.message : undefined); } }}>Guardar</button>
        </div>
      </Modal>

      {/* P-03: crear ticket desde hallazgo */}
      <Modal isOpen={fromFindingOpen} title="Crear ticket desde hallazgo" onClose={() => { setFromFindingOpen(false); setFindingReviewId(null); setFindingId(null); }}>
        <div className="entity-form">
          <label style={{ display: "grid", gap: 6, fontSize: "0.78rem", color: "var(--muted)" }}>
            Revisión de seguridad
            <select
              value={findingReviewId ?? ""}
              onChange={(e) => { setFindingReviewId(e.target.value ? Number(e.target.value) : null); setFindingId(null); }}
            >
              <option value="">— Selecciona una revisión —</option>
              {allReviews.filter((r) => (r.findings_count ?? 0) > 0).map((r) => (
                <option key={r.id} value={r.id}>
                  #{r.id} · {clientName(r.client_id)} · {r.findings_count} hallazgo{(r.findings_count ?? 0) !== 1 ? "s" : ""}
                </option>
              ))}
            </select>
          </label>
          {findingReviewId && reviewDetail ? (
            <label style={{ display: "grid", gap: 6, fontSize: "0.78rem", color: "var(--muted)" }}>
              Hallazgo
              <select
                value={findingId ?? ""}
                onChange={(e) => setFindingId(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">— Selecciona un hallazgo —</option>
                {(reviewDetail.findings || []).map((f) => (
                  <option key={f.id} value={f.id}>
                    [{getSeverityLabel(f.severity)}] {f.title.slice(0, 70)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {findingId ? (
            <label style={{ display: "grid", gap: 6, fontSize: "0.78rem", color: "var(--muted)" }}>
              Prioridad del ticket
              <select value={findingPriority} onChange={(e) => setFindingPriority(e.target.value)}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
          ) : null}
          <div className="panel-actions">
            <button
              className="button button-primary"
              type="button"
              disabled={!findingId || findingSaving}
              onClick={handleCreateFromFinding}
            >
              {findingSaving ? "Creando…" : "Crear ticket"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => { setFromFindingOpen(false); setFindingReviewId(null); setFindingId(null); }}>
              Cancelar
            </button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!detail} title={detail ? `Ticket #${detail.id}` : "Detalle"} onClose={() => setDetail(null)}>
        {detail ? <div className="page-stack"><div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}><BadgeTipo kind={detail.kind} />{nombreSistema(detail.system_id) ? <span className="badge badge-draft">{nombreSistema(detail.system_id)}</span> : null}<AvisoGarantia ticket={detail} /></div>{detail.description ? <p className="doc-summary" style={{ margin: 0 }}>{detail.description}</p> : null}{detail.kind === "cambio" ? <CambioEquipo key={detail.id} ticket={detail} esAdmin={isAdmin} onActualizado={(t) => setDetail({ ...detail, ...t })} /> : null}<div className="card-meta"><div><span className="card-label">Cliente</span><span>{clientName(detail.client_id)}</span></div><div><span className="card-label">Asignado</span><span>{userName(detail.assigned_to)}</span></div><div><span className="card-label">Apertura</span><span>{detail.opened_at}</span></div><div><span className="card-label">Resolucion</span><span>{detail.resolution || "-"}</span></div></div><div className="entity-form"><select value={detail.status} onChange={(e) => setDetail({ ...detail, status: e.target.value })}>{statuses.map((item) => <option key={item} value={item}>{getTicketStatusLabel(item)}</option>)}</select>{isAdmin && <select value={detail.assigned_to || ""} onChange={(e) => setDetail({ ...detail, assigned_to: e.target.value ? Number(e.target.value) : null })}><option value="">Sin asignar</option>{users.map((user) => <option key={user.id} value={user.id}>{user.full_name}</option>)}</select>}<textarea value={detail.resolution || ""} onChange={(e) => setDetail({ ...detail, resolution: e.target.value })} rows={3} placeholder="Resolucion" /><button className="button button-primary" type="button" onClick={async () => { try { const updated = await updateSupportTicket(detail.id, { status: detail.status, assigned_to: detail.assigned_to, resolution: detail.resolution }); setDetail({ ...detail, ...updated }); load(); } catch (err) { notifyError("No se pudo actualizar", err instanceof Error ? err.message : undefined); } }}>Guardar cambios</button><button className="button button-secondary" type="button" onClick={async () => { const event = await createSupportTicketEvent(detail.id, { event_type: "manual_note", notes: "Seguimiento manual" }); setDetail({ ...detail, events: [...detail.events, event] }); }}>Agregar evento</button>{isSuperAdmin && <button className="button button-danger button-sm" type="button" onClick={async () => { const confirmed = await confirmDelete({ title: `¿Eliminar Ticket #${detail.id}?`, text: "Esta acción no se puede deshacer." }); if (!confirmed) return; try { await deleteSupportTicket(detail.id); notifySuccess("Ticket eliminado"); setDetail(null); load(); } catch (err) { notifyError("No se pudo eliminar", err instanceof Error ? err.message : undefined); } }}>Eliminar ticket</button>}</div><div className="table-like"><div className="table-row table-head"><span>Evento</span><span>Detalle</span><span>Fecha</span></div>{detail.events.map((event) => <div className="table-row" key={event.id}><span>{eventoTicket(event.event_type)}</span><span>{event.notes || `${event.from_status || ""} ${event.to_status || ""}`}</span><span>{event.created_at}</span></div>)}</div></div> : null}
      </Modal>
    </section>
  );
}
