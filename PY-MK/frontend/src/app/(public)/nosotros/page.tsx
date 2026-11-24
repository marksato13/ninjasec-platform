import { PublicPageShell } from "@/components/public/public-page-shell";
import { capsulaActiva } from "@/lib/capsulas";

export default function NosotrosPage() {
  const conApi = capsulaActiva("telemetria");

  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Nosotros</p>
        <h1>Consultoría técnica con un equipo que aprende haciendo.</h1>
        <p>
          NinjaSec reúne dirección técnica con experiencia en redes y seguridad, y un equipo de
          estudiantes y profesionales de infraestructura, desarrollo y ciberseguridad que trabaja
          en casos reales con seguimiento.
        </p>
      </section>

      <section className="marketing-grid marketing-grid--two">
        <article className="panel">
          <h3>Misión</h3>
          <p>
            Ayudar a pequeñas y medianas empresas a ordenar, proteger y hacer crecer su tecnología,
            con servicios claros y entregables que se entienden.
          </p>
        </article>
        <article className="panel">
          <h3>Visión</h3>
          <p>
            Ser la consultora tecnológica de confianza de las PYMEs, conectando infraestructura,
            seguridad y desarrollo en un solo equipo.
          </p>
        </article>
        <article className="panel panel-wide">
          <h3>Enfoque</h3>
          <p>
            Primero entendemos qué tienes, y solo entonces proponemos qué hacer. Documentamos lo
            que construimos y decimos con claridad qué sabemos hacer y qué no.
            {conApi &&
              " Además desarrollamos una plataforma de reporting por API para dispositivos de red y seguridad."}
          </p>
        </article>
      </section>
    </PublicPageShell>
  );
}
