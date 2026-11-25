"use client";

import { FormEvent, useEffect, useState } from "react";

type ServiceOption = {
  id: number;
  title: string;
  category?: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8021/api/v1";

/**
 * A que rama pertenece cada categoria del catalogo. Es solo la ETIQUETA que ve la persona: los
 * valores que se envian (el id del servicio) y las categorias de la base de datos no cambian.
 *
 * «nube» (AWS) no es una rama activa: es la futura Ninja Cloud, que no se contrata desde aqui.
 * Se omite del formulario, pero el servicio sigue existiendo en la base de datos.
 */
const RAMA_DE_CATEGORIA: Record<string, string> = {
  infraestructura: "Ninja Sec",
  seguridad: "Ninja Sec",
  desarrollo: "Ninja Dev",
};
const ORDEN_RAMAS = ["Ninja Sec", "Ninja Dev", "Otros"];

function agrupar(servicios: ServiceOption[]): { rama: string; items: ServiceOption[] }[] {
  const porRama = new Map<string, ServiceOption[]>();
  for (const s of servicios) {
    const cat = (s.category ?? "").toLowerCase();
    if (cat === "nube") continue;
    const rama = RAMA_DE_CATEGORIA[cat] ?? "Otros";
    porRama.set(rama, [...(porRama.get(rama) ?? []), s]);
  }
  return ORDEN_RAMAS.filter((r) => porRama.has(r)).map((r) => ({ rama: r, items: porRama.get(r)! }));
}

export function ServiceRequestForm() {
  const [services, setServices] = useState<ServiceOption[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [requestType, setRequestType] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadServices() {
      try {
        const response = await fetch(`${API_URL}/services/`);
        if (!response.ok) return;
        const data = (await response.json()) as ServiceOption[];
        setServices(data.filter((item) => item.id));
      } catch {
        // ignore
      }
    }

    loadServices();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setStatus("");

    const payload = {
      service_id: Number(serviceId),
      requester_name: name,
      requester_email: email,
      request_type: requestType || "General",
      message,
    };

    try {
      const response = await fetch(`${API_URL}/services/requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("No se pudo registrar la solicitud");
      }

      setStatus("Solicitud enviada correctamente.");
      setServiceId("");
      setName("");
      setEmail("");
      setRequestType("");
      setMessage("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ocurrio un error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="public-form" onSubmit={handleSubmit}>
      <h3>Solicitar un servicio</h3>
      <select value={serviceId} onChange={(event) => setServiceId(event.target.value)} required>
        <option value="">Selecciona un servicio</option>
        {agrupar(services).map((g) => (
          <optgroup key={g.rama} label={g.rama}>
            {g.items.map((service) => (
              <option key={service.id} value={service.id}>
                {service.title}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <input placeholder="Nombre" value={name} onChange={(event) => setName(event.target.value)} required />
      <input placeholder="Correo" value={email} onChange={(event) => setEmail(event.target.value)} required />
      <input placeholder="Tipo de solicitud" value={requestType} onChange={(event) => setRequestType(event.target.value)} />
      <textarea placeholder="Describe tu necesidad" value={message} onChange={(event) => setMessage(event.target.value)} rows={5} required />
      {status ? <p className="form-status">{status}</p> : null}
      <button className="button button-primary" type="submit" disabled={loading}>
        {loading ? "Enviando..." : "Enviar solicitud"}
      </button>
    </form>
  );
}
