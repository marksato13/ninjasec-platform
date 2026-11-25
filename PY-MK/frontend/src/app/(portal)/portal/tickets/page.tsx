"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createSupportTicket,
  getSupportTicket,
  getSupportTickets,
  SupportTicketDetail,
  SupportTicketItem,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { getStatusBadgeClass } from "@/lib/role-utils";
import { getSeverityLabel, getTicketStatusLabel } from "@/lib/labels";
import { Modal } from "@/components/ui/modal";
import { QK } from "@/lib/query-keys";
import { detalleEvento, eventoTicket, fechaHora, PRIORIDADES } from "@/components/portal/etiquetas";

export default function PortalTicketsPage() {
  const [tab, setTab] = useState<"open" | "closed">("open");
  const [detail, setDetail] = useState<SupportTicketDetail | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [formTitle, setFormTitle] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formPriority, setFormPriority] = useState("medium");
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  const { data: tickets = [], isLoading, error } = useQuery<SupportTicketItem[]>({
    queryKey: QK.tickets({ ticket_status: tab === "open" ? "open" : "closed" }),
    queryFn: () => getSupportTickets({ ticket_status: tab === "open" ? "open" : "closed" }),
  });

  async function handleCreate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!formTitle.trim()) return;
    setSaving(true);
    try {
      await createSupportTicket({
        client_id: 0,  // overridden by backend from client profile
        title: formTitle.trim(),
        description: formDescription.trim() || null,
        priority: formPriority,
      });
      notifySuccess("Ticket creado");
      queryClient.invalidateQueries({ queryKey: QK.tickets({ ticket_status: "open" }) });
      setCreateOpen(false);
      setFormTitle("");
      setFormDescription("");
      setFormPriority("medium");
      setTab("open");
    } catch (err) {
      notifyError("No se pudo crear el ticket", err instanceof Error ? err.message : "");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <h2>Tickets</h2>
        </div>
        <button className="button button-primary" type="button" onClick={() => setCreateOpen(true)}>
          Nuevo ticket
        </button>
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
                <span>
                  <button
                    className="button button-ghost"
                    type="button"
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

      <Modal isOpen={createOpen} title="Nuevo ticket" onClose={() => setCreateOpen(false)}>
        <form className="entity-form" onSubmit={handleCreate}>
          <input
            placeholder="Título del ticket"
            value={formTitle}
            onChange={(e) => setFormTitle(e.target.value)}
            required
          />
          <textarea
            placeholder="Descripción del problema (opcional)"
            value={formDescription}
            onChange={(e) => setFormDescription(e.target.value)}
            rows={4}
          />
          <select aria-label="Prioridad" value={formPriority} onChange={(e) => setFormPriority(e.target.value)}>
            {PRIORIDADES.map((p) => (
              <option key={p.value} value={p.value}>Prioridad {p.label.toLowerCase()}</option>
            ))}
          </select>
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={saving}>
              {saving ? "Enviando..." : "Crear ticket"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => setCreateOpen(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={!!detail}
        title={detail ? `Ticket #${detail.id}` : "Detalle del ticket"}
        onClose={() => setDetail(null)}
      >
        {detail ? (
          <div className="page-stack">
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
