"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createSupportTicket,
  getClientSystems,
  getSupportTicket,
  getSupportTickets,
  SupportTicketDetail,
  SupportTicketItem,
  TicketKind,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { getStatusBadgeClass } from "@/lib/role-utils";
import { getSeverityLabel, getTicketStatusLabel } from "@/lib/labels";
import { Modal } from "@/components/ui/modal";
import { QK } from "@/lib/query-keys";
import { detalleEvento, eventoTicket, fechaHora, PRIORIDADES } from "@/components/portal/etiquetas";
import { AvisoGarantia, BadgeFase, BadgeTipo, CambioCliente } from "@/components/tickets/solicitud-cambio";

export default function PortalTicketsPage() {
  const [tab, setTab] = useState<"open" | "closed">("open");
  const [detail, setDetail] = useState<SupportTicketDetail | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [formKind, setFormKind] = useState<TicketKind>("incidencia");
  const [formSystem, setFormSystem] = useState("");
  const [formTitle, setFormTitle] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formPriority, setFormPriority] = useState("medium");
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  // La API filtra por UN estado; antes "Abiertos" pedía solo `open` y un ticket en
  // curso o pendiente (p. ej. un cambio ya convertido en tarea) no salía en ninguna pestaña.
  const { data: todos = [], isLoading, error } = useQuery<SupportTicketItem[]>({
    queryKey: QK.tickets({ portal: true }),
    queryFn: () => getSupportTickets(),
  });
  const tickets = todos.filter((t) => (tab === "closed") === ["resolved", "closed"].includes(t.status));

  // 35-P-03: el cliente solo ve SUS sistemas (el backend filtra por su perfil).
  const { data: misSistemas } = useQuery({ queryKey: QK.clientSystems(), queryFn: () => getClientSystems() });
  const sistemas = (misSistemas?.systems ?? []).filter((s) => s.status !== "retirado");
  const nombreSistema = (id?: number | null) => (id ? misSistemas?.systems.find((s) => s.id === id)?.name ?? null : null);

  function abrirCrear(kind: TicketKind) {
    setFormKind(kind);
    setFormSystem("");
    setCreateOpen(true);
  }

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!formTitle.trim()) return;
    if (formKind === "cambio" && !formSystem) return;
    setSaving(true);
    try {
      await createSupportTicket({
        client_id: 0,  // overridden by backend from client profile
        title: formTitle.trim(),
        description: formDescription.trim() || null,
        priority: formPriority,
        kind: formKind,
        system_id: formSystem ? Number(formSystem) : null,
      });
      notifySuccess(formKind === "cambio" ? "Solicitud de cambio enviada" : "Ticket creado", formKind === "cambio" ? "El equipo la estimará y verás aquí las horas para aprobarlas." : undefined);
      queryClient.invalidateQueries({ queryKey: QK.ticketsAll() });
      setCreateOpen(false);
      setFormTitle("");
      setFormDescription("");
      setFormPriority("medium");
      setFormSystem("");
      setTab("open");
    } catch (err) {
      notifyError("No se pudo crear el ticket", err instanceof Error ? err.message : "");
    } finally {
      setSaving(false);
    }
  }

  const esCambio = formKind === "cambio";

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <h2>Tickets</h2>
        </div>
        <div className="panel-actions" style={{ flexWrap: "wrap" }}>
          <button className="button button-secondary" type="button" onClick={() => abrirCrear("cambio")}>
            Pedir un cambio
          </button>
          <button className="button button-primary" type="button" onClick={() => abrirCrear("incidencia")}>
            Nuevo ticket
          </button>
        </div>
      </div>
      <div className="tab-list">
        <button
          className={`tab ${tab === "open" ? "tab-active" : ""}`}
          type="button"
          onClick={() => setTab("open")}
        >
          Abiertos
        </button>
        <button
          className={`tab ${tab === "closed" ? "tab-active" : ""}`}
          type="button"
          onClick={() => setTab("closed")}
        >
          Cerrados
        </button>
      </div>
      <article className="panel">
        {error ? <p className="form-error">{error instanceof Error ? error.message : "No se pudieron cargar tickets"}</p> : null}
        {isLoading ? (
          <div className="empty-state">Cargando tickets...</div>
        ) : tickets.length === 0 ? (
          <div className="empty-state">No hay tickets {tab === "open" ? "abiertos" : "cerrados"}.</div>
        ) : (
          <div className="table-like">
            <div className="table-row table-head table-row-wide">
              <span>ID</span>
              <span>Título</span>
              <span>Prioridad</span>
              <span>Estado</span>
            </div>
            {tickets.map((ticket) => (
              <div className="table-row table-row-wide" key={ticket.id}>
                <span>#{ticket.id}</span>
                <span style={{ display: "grid", gap: 4, minWidth: 0 }}>
                  <button
                    className="button button-ghost"
                    type="button"
                    style={{ justifySelf: "start", textAlign: "left" }}
                    onClick={async () => {
                      try {
                        setDetail(await getSupportTicket(ticket.id));
                      } catch (err) {
                        notifyError("No se pudo abrir el ticket", err instanceof Error ? err.message : "");
                      }
                    }}
                  >
                    {ticket.title}
                  </button>
                  <span style={{ display: "flex", flexWrap: "wrap", gap: 4, paddingLeft: 12 }}>
                    <BadgeTipo kind={ticket.kind} />
                    {nombreSistema(ticket.system_id) ? <span className="badge badge-draft">{nombreSistema(ticket.system_id)}</span> : null}
                    {ticket.kind === "cambio" ? <BadgeFase ticket={ticket} /> : <AvisoGarantia ticket={ticket} />}
                  </span>
                </span>
                <span>{getSeverityLabel(ticket.priority)}</span>
                <span>
                  <span className={`badge ${getStatusBadgeClass(ticket.status)}`}>
                    {getTicketStatusLabel(ticket.status)}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </article>

      <Modal isOpen={createOpen} title={esCambio ? "Pedir un cambio" : "Nuevo ticket"} onClose={() => setCreateOpen(false)}>
        <form className="entity-form" onSubmit={handleCreate}>
          <select aria-label="Tipo" value={formKind} onChange={(e) => setFormKind(e.target.value as TicketKind)}>
            <option value="incidencia">Algo falla (incidencia)</option>
            <option value="cambio">Quiero algo nuevo en un sistema (cambio)</option>
          </select>
          {esCambio && sistemas.length === 0 ? (
            <p className="muted-small" style={{ margin: 0 }}>
              Aún no tienes sistemas registrados con nosotros. Abre un ticket normal y lo vemos juntos.
            </p>
          ) : (
            <select
              aria-label="Sistema"
              value={formSystem}
              onChange={(e) => setFormSystem(e.target.value)}
              required={esCambio}
            >
              <option value="">{esCambio ? "¿Sobre qué sistema?" : "Sistema afectado (opcional)"}</option>
              {sistemas.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          )}
          <input
            placeholder={esCambio ? "Qué quieres que cambie" : "Título del ticket"}
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            required
          />
          <textarea
            placeholder={esCambio ? "Cuéntanos el detalle: qué necesitas y para qué" : "Descripción del problema (opcional)"}
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            rows={4}
          />
          <select aria-label="Prioridad" value={formPriority} onChange={(e) => setFormPriority(e.target.value)}>
            {PRIORIDADES.map((p) => (
              <option key={p.value} value={p.value}>Prioridad {p.label.toLowerCase()}</option>
            ))}
          </select>
          {esCambio ? (
            <p className="muted-small" style={{ margin: 0 }}>
              El equipo estimará las horas. Nada se hace hasta que tú lo apruebes.
            </p>
          ) : null}
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={saving || (esCambio && !formSystem)}>
              {saving ? "Enviando..." : esCambio ? "Enviar solicitud" : "Crear ticket"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => setCreateOpen(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={!!detail}
        title={detail ? `${detail.kind === "cambio" ? "Cambio" : "Ticket"} #${detail.id}` : "Detalle del ticket"}
        onClose={() => setDetail(null)}
      >
        {detail ? (
          <div className="page-stack">
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              <BadgeTipo kind={detail.kind} />
              {nombreSistema(detail.system_id) ? <span className="badge badge-draft">{nombreSistema(detail.system_id)}</span> : null}
              <AvisoGarantia ticket={detail} />
            </div>
            {detail.kind === "cambio" ? (
              <CambioCliente key={detail.id} ticket={detail} onActualizado={(t) => setDetail({ ...detail, ...t })} />
            ) : null}
            <div className="card-meta">
              <div>
                <span className="card-label">Descripción</span>
                <span>{detail.description || "-"}</span>
              </div>
              <div>
                <span className="card-label">Resolución</span>
                <span>{detail.resolution || "-"}</span>
              </div>
              <div>
                <span className="card-label">Apertura</span>
                <span>{fechaHora(detail.opened_at)}</span>
              </div>
            </div>
            <div className="table-like">
              <div className="table-row table-head">
                <span>Evento</span>
                <span>Detalle</span>
                <span>Fecha</span>
              </div>
              {detail.events.map((event) => (
                <div className="table-row" key={event.id}>
                  <span>{eventoTicket(event.event_type)}</span>
                  <span>{detalleEvento(event.notes, event.from_status, event.to_status)}</span>
                  <span>{fechaHora(event.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
