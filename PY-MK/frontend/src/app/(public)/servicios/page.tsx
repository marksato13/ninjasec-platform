import { PublicPageShell } from "@/components/public/public-page-shell";
import { ServiceRequestForm } from "@/components/public/service-request-form";
import { capsulaActiva } from "@/lib/capsulas";

/**
 * Servicios que NinjaSec ofrece HOY.
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
 * La nube (AWS) se ofrece como servicio. No tiene todavia el respaldo de
 * evidencia que tienen los de redes, asi que se redacta como lo que podemos
 * hacer y no como lo que ya hemos entregado.
 */

type Servicio = { titulo: string; texto: string };
type Linea = { eyebrow: string; titulo: string; servicios: Servicio[] };

const LINEAS: Linea[] = [
  {
    eyebrow: "Infraestructura y redes",
    titulo: "Que tu red funcione, esté ordenada y segura",
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
          "Firewall perimetral, VLANs por zona, VPN y una vuelta atrás probada. Trabajamos con Fortinet (FortiGate) y Cisco, y migramos desde MikroTik.",
      },
      {
        titulo: "Monitoreo y alertas",
        texto:
          "Vigilamos tus servidores y equipos y te avisamos por Telegram o correo antes de que llame un cliente. Con informe mensual.",
      },
    ],
  },
  {
    eyebrow: "Nube",
    titulo: "Tu infraestructura en AWS",
    servicios: [
      {
        titulo: "Diseño y despliegue en AWS",
        texto:
          "Servidores, redes privadas, copias de seguridad y seguridad básica para tus aplicaciones en la nube, con la misma disciplina que una red física.",
      },
      {
        titulo: "Conectar tu red con la nube",
        texto:
          "Unimos tu oficina con AWS mediante VPN y definimos qué se ve desde dónde, para que la nube no sea una puerta abierta.",
      },
    ],
  },
  {
    eyebrow: "Ciberseguridad",
    titulo: "Saber dónde estás expuesto",
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
    eyebrow: "Desarrollo",
    titulo: "Software hecho a tu medida",
    servicios: [
      {
        titulo: "Sistemas a medida",
        texto:
          "Aplicaciones web, sistemas internos y MVPs, con backend, base de datos y despliegue incluidos.",
      },
      {
        titulo: "APIs e integraciones",
        texto:
          "Conectamos tus sistemas entre sí para que los datos dejen de copiarse a mano.",
      },
      {
        titulo: "Automatización de procesos",
        texto:
          "Scripts y flujos que eliminan el trabajo repetitivo de tu equipo.",
      },
    ],
  },
];

// Solo con la capsula de telemetria encendida: es la plataforma de reporting.
const PLATAFORMA: Linea = {
  eyebrow: "Plataforma",
  titulo: "Reporting por API",
  servicios: [
    { titulo: "Integración API", texto: "Conectamos dispositivos, plataformas y sistemas para centralizar datos." },
    { titulo: "Reporting automatizado", texto: "Generamos reportes técnicos y ejecutivos listos para cliente o gerencia." },
    { titulo: "Dashboards operativos", texto: "Creamos paneles para operación, monitoreo y toma de decisiones." },
  ],
};

export default function ServiciosPage() {
  const lineas = capsulaActiva("telemetria") ? [...LINEAS, PLATAFORMA] : LINEAS;

  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Servicios</p>
        <h1>Infraestructura, nube, seguridad y desarrollo para tu empresa.</h1>
        <p>
          Ninja Tech ayuda a pequeñas y medianas empresas a ordenar, proteger y hacer crecer su
          tecnología. Empezamos entendiendo qué tienes, y solo entonces proponemos qué hacer.
        </p>
      </section>

      {lineas.map((linea) => (
        <section className="page-stack" key={linea.eyebrow}>
          <div>
            <p className="eyebrow">{linea.eyebrow}</p>
            <h2>{linea.titulo}</h2>
          </div>
          <div className="marketing-grid marketing-grid--two">
            {linea.servicios.map((s) => (
              <article className="panel" key={s.titulo}>
                <h3>{s.titulo}</h3>
                <p>{s.texto}</p>
              </article>
            ))}
          </div>
        </section>
      ))}

      <section className="content-hero">
        <p className="eyebrow">Solicitudes</p>
        <h2>Conversemos sobre tu necesidad.</h2>
        <p>
          Usa este formulario para solicitar un servicio o iniciar una conversación técnica.
          Respondemos con un plan de trabajo y la mejor ruta para tu caso.
        </p>
      </section>

      <ServiceRequestForm />
    </PublicPageShell>
  );
}
