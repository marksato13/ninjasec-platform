"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Package, ShieldCheck } from "lucide-react";

import { createServiceRequest, getMe, getServiceRequests, getServices, ServiceItem, ServiceRequestItem } from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { Modal } from "@/components/ui/modal";
import { claseSolicitud, estadoSolicitud, fecha } from "@/components/portal/etiquetas";

function serviceIcon(category?: string | null) {
  const cat = (category ?? "").toLowerCase();
  if (cat.includes("pentest") || cat.includes("audit")) return <ShieldCheck size={20} />;
  return <Package size={20} />;
}

export default function PortalServicesPage() {
  const [requestOpen, setRequestOpen] = useState(false);
  const [selectedService, setSelectedService] = useState<ServiceItem | null>(null);
  const [formMessage, setFormMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const queryClient = useQueryClient();

  const { data: services = [], isLoading, error } = useQuery<ServiceItem[]>({
    queryKey: ["portal-services"],
    queryFn: getServices,
  });

  const { data: myRequests = [] } = useQuery<ServiceRequestItem[]>({
    queryKey: ["portal-service-requests"],
    queryFn: getServiceRequests,
  });

  const serviceMap = new Map(services.map((s) => [s.id, s.title]));

  function openRequest(service: ServiceItem) {
    setSelectedService(service);
    setFormMessage("");
    setRequestOpen(true);
  }

  async function handleRequest(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedService) return;
    setSaving(true);
    try {
      const me = await getMe();
      await createServiceRequest({
        service_id: selectedService.id,
        requester_name: me.name || me.full_name || me.email,
        requester_email: me.email,
        message: formMessage.trim() || null,
      });
      notifySuccess("Solicitud enviada", "Te contactaremos a la brevedad.");
      await queryClient.invalidateQueries({ queryKey: ["portal-service-requests"] });
      setRequestOpen(false);
    } catch (err) {
      notifyError("No se pudo enviar la solicitud", err instanceof Error ? err.message : "");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <h2>Servicios</h2>
        </div>
        <span style={{ color: "var(--muted)", fontSize: "0.88rem" }}>
          {services.length} servicio{services.length !== 1 ? "s" : ""} disponible{services.length !== 1 ? "s" : ""}
        </span>
      </div>

      {myRequests.length > 0 && (
        <article className="panel">
          <div className="panel-head">
            <div><h3>Mis solicitudes</h3></div>
            <span style={{ color: "var(--muted)", fontSize: "0.8rem" }}>{myRequests.length} solicitud{myRequests.length !== 1 ? "es" : ""}</span>
          </div>
          <div className="table-like">
            <div className="table-row table-head">
              <span>Servicio</span>
              <span>Estado</span>
              <span>Fecha</span>
            </div>
            {myRequests.map((req) => (
              <div className="table-row" key={req.id}>
                <span>{serviceMap.get(req.service_id) || `Servicio #${req.service_id}`}</span>
                <span><span className={`badge ${claseSolicitud(req.status, req.project_id)}`}>{estadoSolicitud(req.status, req.project_id)}</span></span>
                <span style={{ color: "var(--muted)", fontSize: "0.78rem" }}>{fecha(req.created_at)}</span>
              </div>
            ))}
          </div>
        </article>
      )}

      {error ? (
        <div className="empty-state state-error">No se pudo cargar el catálogo de servicios.</div>
      ) : isLoading ? (
        <div className="empty-state">Cargando servicios...</div>
      ) : services.length === 0 ? (
        <div className="empty-state">No hay servicios disponibles en este momento.</div>
      ) : (
        <div className="card-grid">
          {services.map((service) => (
            <article
              key={service.id}
              className="card"
              style={{ borderLeft: "3px solid var(--security)" }}
            >
              <div className="card-header">
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{
                    display: "flex", alignItems: "center", justifyContent: "center",
                    width: 36, height: 36, borderRadius: 10,
                    background: "rgba(99,102,241,0.12)", color: "var(--security)",
                  }}>
                    {serviceIcon(service.category)}
                  </span>
                  <div>
                    <strong style={{ fontSize: "0.95rem" }}>{service.title}</strong>
                    {service.category && (
                      <p className="eyebrow" style={{ margin: 0, marginTop: 2 }}>{service.category}</p>
                    )}
                  </div>
                </div>
              </div>
              {service.summary && (
                <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: 0 }}>{service.summary}</p>
              )}
              {service.description && service.description !== service.summary && (
                <p style={{ fontSize: "0.82rem", margin: 0 }}>{service.description}</p>
              )}
              <div className="card-actions">
                <button
                  className="button button-primary"
                  type="button"
                  onClick={() => openRequest(service)}
                >
                  Solicitar servicio
                </button>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        isOpen={requestOpen && !!selectedService}
        title={`Solicitar: ${selectedService?.title ?? ""}`}
        onClose={() => setRequestOpen(false)}
      >
        <form className="entity-form" onSubmit={handleRequest}>
          <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: 0 }}>
            {selectedService?.summary || selectedService?.description || "Completa los datos para solicitar este servicio."}
          </p>
          <textarea
            placeholder="Describe tu necesidad o proyecto (opcional)"
            value={formMessage}
            onChange={(e) => setFormMessage(e.target.value)}
            rows={4}
          />
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={saving}>
              {saving ? "Enviando..." : "Enviar solicitud"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => setRequestOpen(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </Modal>
    </section>
  );
}
