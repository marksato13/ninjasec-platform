"use client";

import { FormEvent, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { createServiceRequest, getServices } from "@/lib/api";
import { QK } from "@/lib/query-keys";

type ServiceOption = {
  id: number;
  title: string;
  category?: string | null;
};

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
  const { data: services = [], error: servicesError } = useQuery({
    queryKey: QK.services(),
    queryFn: getServices,
  });
  const mutation = useMutation({ mutationFn: createServiceRequest });
  const [serviceId, setServiceId] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [requestType, setRequestType] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState("");
  const statusMessage = status || (servicesError ? "No se pudo cargar el catálogo de servicios" : "");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");

    const payload = {
      service_id: Number(serviceId),
      requester_name: name,
      requester_email: email,
      request_type: requestType || "General",
      message,
    };

    try {
      await mutation.mutateAsync(payload);

      setStatus("Solicitud enviada correctamente.");
      setServiceId("");
      setName("");
      setEmail("");
      setRequestType("");
      setMessage("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ocurrió un error");
    }
  }

  return (
    <form className="public-form" onSubmit={handleSubmit}>
      <h3>Solicitar un servicio</h3>
      <select value={serviceId} onChange={(event) => setServiceId(event.target.value)} required>
        <option value="">Selecciona un servicio</option>
        {agrupar(services.filter((item) => item.id)).map((g) => (
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
      {statusMessage ? <p className="form-status">{statusMessage}</p> : null}
      <button className="button button-primary" type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Enviando..." : "Enviar solicitud"}
      </button>
    </form>
  );
}
