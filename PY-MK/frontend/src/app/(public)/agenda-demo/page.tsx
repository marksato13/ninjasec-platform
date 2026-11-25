import { LeadForm } from "@/components/public/lead-form";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { capsulaActiva } from "@/lib/capsulas";
import { metadatosDePagina } from "@/lib/sitio";

export const metadata = {
  ...metadatosDePagina(
    "/agenda-demo",
    "Agenda una reunión",
    "Agenda una primera conversación con Ninja Tech para revisar tu caso.",
  ),
};

export default function AgendaDemoPage() {
  const conApi = capsulaActiva("telemetria");

  // Sin la capsula de telemetria no hay plataforma que demostrar: la pagina
  // sigue existiendo (la ruta y el formulario son los mismos) pero sirve para
  // lo que hoy es el negocio, agendar una primera conversacion.
  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">{conApi ? "Agenda Demo" : "Agenda una reunión"}</p>
        <h1>{conApi ? "Solicita una demo de Ninja Tech." : "Agendemos una primera conversación."}</h1>
        <p>
          {conApi
            ? "Registra tu interés para evaluar cómo integrar reporting automatizado en tu entorno."
            : "Cuéntanos qué necesitas, ya sea infraestructura, nube, seguridad o desarrollo, y coordinamos una reunión para entender tu caso."}
        </p>
      </section>
      <LeadForm
        title={conApi ? "Agenda una demo" : "Agenda una reunión"}
        endpoint="leads/"
        submitLabel={conApi ? "Solicitar demo" : "Solicitar reunión"}
        payloadType="lead"
      />
    </PublicPageShell>
  );
}
