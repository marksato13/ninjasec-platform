import Image from "next/image";
import Link from "next/link";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { ServiceRequestForm } from "@/components/public/service-request-form";
import { capsulaActiva } from "@/lib/capsulas";

/**
 * Servicios que Ninja Tech ofrece HOY, en sus dos ramas activas: Ninja Sec y Ninja Dev.
 *
 * Sale del catalogo comercial, que separa lo que esta probado de lo que
 * todavia no se vende. Por eso no aparece aqui: conectarse a los equipos del
 * cliente por API, el informe SOC ni el hardening automatizado. Los
 * conectores son simulados, y eso lo descubre un cliente tecnico en la
 * primera demo.
 *
 * Los PRECIOS no se publican: estan en el repositorio privado y son una
 * propuesta sin validar.
 *
 * La nube (AWS) NO se ofrece desde aqui: es la futura rama Ninja Cloud. Sigue visible, marcada
 * «en preparacion» y sin boton, porque todavia no tiene el respaldo de evidencia que tienen los
 * de redes. El formulario tampoco la lista (ver service-request-form.tsx).
 */

type Servicio = { titulo: string; texto: string };
type Grupo = { titulo?: string; servicios: Servicio[] };
type Rama = {
  ancla: string;
  nombre: string;
  texto: string;
  avatar: string;
  pose: string;
  grupos: Grupo[];
};

const RAMAS: Rama[] = [
  {
    ancla: "ninja-sec",
    nombre: "Ninja Sec",
    texto:
      "Protegemos tus redes: revisamos dónde estás expuesto y corregimos primero lo que más importa.",
    avatar: "/brand/avatar-ninja-sec.webp",
    pose: "/brand/poses/sec-escudo-red.webp",
    grupos: [
      {
        titulo: "Ciberseguridad",
        servicios: [
          {
            titulo: "Auditoría ISO/IEC 27002",
            texto:
              "Evaluamos tu seguridad contra los controles del estándar, con hallazgos clasificados por riesgo y un plan de corrección priorizado. Es de solo lectura.",
          },
          {
            titulo: "Vulnerabilidades priorizadas",
            texto:
              "No te damos 400 fallos: te decimos cuáles son los que de verdad pueden explotarse, para que empieces por ahí.",
          },
        ],
      },
      {
        titulo: "Infraestructura segura",
        servicios: [
          {
            titulo: "Diagnóstico de infraestructura",
            texto:
              "Revisamos tu red y tus equipos sin modificar nada: qué tienes, dónde estás débil y qué corregir primero. Entregamos informe, diagrama y prioridades.",
          },
          {
            titulo: "Documentación técnica y diagramas",
            texto:
              "Topología actualizada, inventario de activos y procedimientos, para cuando llegue una auditoría o una licitación.",
          },
          {
            titulo: "Firewall y segmentación de red",
            texto:
              "Firewall perimetral, VLANs por zona, VPN y una vuelta atrás probada. Trabajamos con pfSense, Fortinet (FortiGate) y Cisco, y migramos desde MikroTik.",
          },
          {
            titulo: "Monitoreo y alertas",
            texto:
              "Vigilamos tus servidores y equipos y te avisamos por Telegram o correo antes de que llame un cliente. Con informe mensual.",
          },
        ],
      },
    ],
  },
  {
    ancla: "ninja-dev",
    nombre: "Ninja Dev",
    texto: "Construimos el software que tu negocio usa a diario, y probamos que funcione.",
    avatar: "/brand/avatar-ninja-dev.webp",
    pose: "/brand/poses/dev-sentado-laptop.webp",
    grupos: [
      {
        servicios: [
          {
            titulo: "Sistemas a medida",
            texto:
              "Aplicaciones web, sistemas internos y MVPs, con backend, base de datos y despliegue incluidos.",
          },
          {
            titulo: "APIs e integraciones",
            texto: "Conectamos tus sistemas entre sí para que los datos dejen de copiarse a mano.",
          },
          {
            titulo: "Automatización de procesos",
            texto: "Scripts y flujos que eliminan el trabajo repetitivo de tu equipo.",
          },
          {
            titulo: "Pruebas de software",
            texto:
              "Pruebas de extremo a extremo y un control de contrato de la API, las mismas con las que publicamos nuestra propia plataforma.",
          },
        ],
      },
    ],
  },
];

// Solo con la capsula de telemetria encendida: es la plataforma de reporting.
const PLATAFORMA: Grupo = {
  titulo: "Plataforma de reporting por API",
  servicios: [
    { titulo: "Integración API", texto: "Conectamos dispositivos, plataformas y sistemas para centralizar datos." },
    { titulo: "Reporting automatizado", texto: "Generamos reportes técnicos y ejecutivos listos para cliente o gerencia." },
    { titulo: "Dashboards operativos", texto: "Creamos paneles para operación, monitoreo y toma de decisiones." },
  ],
};

export default function ServiciosPage() {
  const conApi = capsulaActiva("telemetria");
  const ramas = conApi
    ? RAMAS.map((r) => (r.ancla === "ninja-dev" ? { ...r, grupos: [...r.grupos, PLATAFORMA] } : r))
    : RAMAS;

  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Servicios</p>
        <h1>Ciberseguridad y desarrollo de software para tu empresa.</h1>
        <p>
          Ninja Tech ayuda a pequeñas y medianas empresas a proteger sus redes y a construir software a medida,
          en dos áreas: <strong>Ninja Sec</strong> y <strong>Ninja Dev</strong>. Empezamos entendiendo qué tienes,
          y solo entonces proponemos qué hacer.
        </p>
      </section>

      {ramas.map((rama) => (
        <section className="page-stack" key={rama.ancla} id={rama.ancla}>
          <div className="rama-head">
            <Image src={rama.avatar} alt={`Logo de ${rama.nombre}`} width={72} height={72} className="rama-head__logo" />
            <div>
              <h2 style={{ margin: 0 }}>{rama.nombre}</h2>
              <p className="muted-small" style={{ margin: 0 }}>{rama.texto}</p>
            </div>
            <Image src={rama.pose} alt="" aria-hidden width={140} height={140} className="rama-head__pose" />
          </div>

          {rama.grupos.map((g) => (
            <div key={g.titulo ?? "todo"} style={{ display: "grid", gap: 14 }}>
              {g.titulo && <h3 className="rama-subarea">{g.titulo}</h3>}
              <div className="marketing-grid marketing-grid--two">
                {g.servicios.map((s) => (
                  <article className="panel" key={s.titulo}>
                    <h3>{s.titulo}</h3>
                    <p>{s.texto}</p>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </section>
      ))}

      <section className="page-stack" id="ninja-cloud">
        <article className="panel area-futura">
          <span className="badge badge-draft">En preparación</span>
          <h2 style={{ margin: "10px 0 6px" }}>Ninja Cloud: tu infraestructura en AWS</h2>
          <p style={{ margin: 0 }}>
            Diseño y despliegue en AWS, y conexión de tu oficina con la nube por VPN. Es una futura rama: todavía
            no tenemos trabajo propio que enseñar, así que <strong>no se contrata desde aquí</strong>.
          </p>
          <p className="muted-small" style={{ margin: "8px 0 0" }}>
            Cuando exista, aparecerá en <Link href="/proyectos#areas-en-preparacion">Proyectos</Link> con su
            diagrama y sus mediciones, y no antes.
          </p>
        </article>
      </section>

      <section className="content-hero">
        <p className="eyebrow">Solicitudes</p>
        <h2>Conversemos sobre tu necesidad.</h2>
        <p>
          Usa este formulario para solicitar un servicio de Ninja Sec o de Ninja Dev, o para iniciar una
          conversación técnica. Respondemos con un plan de trabajo y la mejor ruta para tu caso.
        </p>
        <Image
          src="/brand/poses/soporte-auricular.webp"
          alt=""
          aria-hidden
          width={120}
          height={120}
          className="rama-head__pose rama-head__pose--suelta"
        />
      </section>

      <ServiceRequestForm />
    </PublicPageShell>
  );
}
