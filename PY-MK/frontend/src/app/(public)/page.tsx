import Image from "next/image";
import Link from "next/link";
import { ArrowRight, FilePieChart, Gauge, Plug, ShieldCheck } from "lucide-react";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { Mascot } from "@/components/ui/mascot";
import { capsulaActiva } from "@/lib/capsulas";

/**
 * La portada tiene DOS versiones, segun la capsula de telemetria.
 *
 * Con la capsula apagada (hoy) los conectores son simulados, asi que la
 * portada no puede prometer "reporting por API", ni presumir cifras de
 * clientes y dispositivos que no existen. Habla de lo que Ninja Tech hace de
 * verdad, en sus dos areas activas: Ninja Sec (ciberseguridad) y Ninja Dev (software).
 *
 * Al encender la capsula vuelve sola el mensaje de plataforma. Los numeros
 * de ejemplo (17 clientes, 73 dispositivos...) se retiraron en los dos casos:
 * eran de la demo, estaban escritos a mano y la demo ya no existe.
 */

const PASOS_PLATAFORMA = [
  { icon: Plug, title: "Conecta", text: "Integra pfSense, FortiGate y otras plataformas de red y seguridad por API." },
  { icon: Gauge, title: "Consolida", text: "Ninja Tech normaliza y centraliza los datos técnicos de todos tus dispositivos." },
  { icon: ShieldCheck, title: "Visualiza", text: "Dashboards operativos y ejecutivos, actualizados en tiempo casi real." },
  { icon: FilePieChart, title: "Reporta", text: "Reportes técnicos y ejecutivos listos para entregar, sin trabajo manual." },
];

const PASOS_CONSULTORIA = [
  { icon: ShieldCheck, title: "Revisa", text: "Evaluamos tu red, tus equipos y tus controles de seguridad." },
  { icon: Gauge, title: "Prioriza", text: "Ordenamos los hallazgos por riesgo y por impacto en tu negocio." },
  { icon: Plug, title: "Implementa", text: "Aplicamos las correcciones con un equipo técnico." },
  { icon: FilePieChart, title: "Informa", text: "Te entregamos informes claros, técnicos y ejecutivos." },
];

export default function HomePage() {
  const conApi = capsulaActiva("telemetria");
  const pasos = conApi ? PASOS_PLATAFORMA : PASOS_CONSULTORIA;

  return (
    <PublicPageShell>
      <section className="landing-hero-wrap">
        <div className="login-grid-bg" aria-hidden />
        <div className="login-orb login-orb--blue" aria-hidden />
        <div className="login-orb login-orb--cyan" aria-hidden />

        <div className="hero-marketing landing-reveal">
          <div>
            <span className="pill">{conApi ? "Ninja Tech Platform" : "Ninja Tech"}</span>
            {conApi ? (
              <>
                <h1>Reporting inteligente por API para infraestructura, seguridad y operaciones TI.</h1>
                <p>
                  Ninja Tech transforma datos técnicos de dispositivos y plataformas como pfSense y FortiGate
                  en dashboards, reportes ejecutivos y servicios tecnológicos listos para empresas y MSPs.
                </p>
              </>
            ) : (
              <>
                <h1>Ciberseguridad y desarrollo de software para pymes</h1>
                <p>
                  En Ninja Tech ayudamos a pequeñas y medianas empresas a proteger sus redes y
                  construir software a medida. Trabajamos en dos áreas: Ninja Sec y Ninja Dev.
                </p>
              </>
            )}
            <div className="hero-actions">
              <Link className="button button-primary" href="/agenda-demo">
                {conApi ? "Agenda una demo" : "Agenda una reunión"}
              </Link>
              {conApi ? (
                <Link className="button button-secondary" href="/solucion">Ver solucion</Link>
              ) : (
                <Link className="button button-secondary" href="/proyectos">Ver proyectos</Link>
              )}
            </div>
          </div>

          <div className="hero-visual-card hero-mascot-card">
            {conApi ? (
              <Mascot variant="working" size="lg" priority />
            ) : (
              <Image
                className="hero-pose"
                src="/brand/poses/tech-escudo-ventana.webp"
                alt="Kuro, la mascota de Ninja Tech, con un escudo y una ventana de código"
                width={520}
                height={520}
                priority
              />
            )}
            <div className="hero-mascot-badge">
              <span className="dot" />
              {conApi ? "Kuro está vigilando tu red" : "Kuro cuida tu red y tu código"}
            </div>
          </div>
        </div>
      </section>

      {/* Las dos areas activas, justo bajo la portada y en el mismo orden en movil y escritorio. */}
      <section className="branch-cards landing-reveal landing-reveal--delay-1" aria-label="Áreas de Ninja Tech">
        <article className="panel branch-card branch-card--sec" id="ninja-sec">
          <div className="branch-card__head">
            <Image className="branch-card__logo" src="/brand/avatar-ninja-sec.webp" alt="Logo de Ninja Sec" width={72} height={72} />
            <div>
              <p className="eyebrow">Ciberseguridad e infraestructura segura</p>
              <h2>Ninja Sec</h2>
            </div>
          </div>
          <p>Protegemos redes, detectamos comportamientos anómalos y ayudamos a responder a incidentes.</p>
          <Image
            className="branch-card__anim"
            src="/brand/anim/seguridad.webp"
            alt="Kuro sosteniendo un escudo de seguridad"
            width={150}
            height={150}
            unoptimized
          />
          <div className="hero-actions">
            <Link className="button button-secondary" href="/servicios">Ver servicios</Link>
            <Link className="button button-ghost" href="/proyectos">Ver proyectos</Link>
          </div>
        </article>

        <article className="panel branch-card branch-card--dev" id="ninja-dev">
          <div className="branch-card__head">
            <Image className="branch-card__logo" src="/brand/avatar-ninja-dev.webp" alt="Logo de Ninja Dev" width={72} height={72} />
            <div>
              <p className="eyebrow">Desarrollo de software</p>
              <h2>Ninja Dev</h2>
            </div>
          </div>
          <p>
            Desarrollamos aplicaciones web, sistemas internos y APIs. Integramos tus herramientas y probamos
            los flujos que tu negocio usa a diario.
          </p>
          <Image
            className="branch-card__anim"
            src="/brand/anim/desarrollo.webp"
            alt="Kuro programando en su laptop"
            width={150}
            height={150}
            unoptimized
          />
          <div className="hero-actions">
            <Link className="button button-secondary" href="/servicios">Ver servicios</Link>
            <Link className="button button-ghost" href="/proyectos">Ver proyectos</Link>
          </div>
        </article>
      </section>

      <section className="page-stack landing-reveal landing-reveal--delay-1">
        <p className="eyebrow" style={{ textAlign: "center" }}>
          {conApi ? "Cómo funciona" : "Cómo trabajamos"}
        </p>
        <div className="landing-steps">
          {pasos.map((step, index) => (
            <article className="panel landing-step" key={step.title}>
              <step.icon size={20} aria-hidden style={{ color: "var(--primary, #3B82F6)" }} />
              <h4>{step.title}</h4>
              <p>{step.text}</p>
              {index < pasos.length - 1 && (
                <ArrowRight className="landing-step-arrow" size={22} aria-hidden />
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="marketing-grid marketing-grid--three landing-reveal landing-reveal--delay-2">
        {conApi ? (
          <>
            <article className="panel">
              <p className="eyebrow">Valor</p>
              <h3>Menos trabajo manual</h3>
              <p>Automatizamos extracción, consolidación y entrega de reportes técnicos y ejecutivos.</p>
            </article>
            <article className="panel">
              <p className="eyebrow">Innovacion</p>
              <h3>Integración por API</h3>
              <p>Conectamos plataformas de red y seguridad para unificar visibilidad y operación.</p>
            </article>
            <article className="panel">
              <p className="eyebrow">Servicios</p>
              <h3>Producto + implementación</h3>
              <p>Ofrecemos software, dashboards, automatización y acompañamiento técnico.</p>
            </article>
          </>
        ) : (
          <>
            <article className="panel">
              <p className="eyebrow">Valor</p>
              <h3>Menos riesgo</h3>
              <p>Revisamos la seguridad de tu infraestructura y te decimos qué corregir primero.</p>
            </article>
            <article className="panel">
              <p className="eyebrow">Equipo</p>
              <h3>Talento en formación</h3>
              <p>Estudiantes y profesionales de infraestructura, desarrollo y ciberseguridad trabajando en casos reales.</p>
            </article>
            <article className="panel">
              <p className="eyebrow">Servicios</p>
              <h3>Consultoría + implementación</h3>
              <p>Diagnósticos, revisiones de seguridad y acompañamiento técnico.</p>
            </article>
          </>
        )}
      </section>

      {/* Lo que se puede ver, no solo lo que se promete. Cada enlace lleva a un diagrama. */}
      <section className="page-stack">
        <div>
          <h2>Qué construimos</h2>
          <p className="muted-small" style={{ margin: 0 }}>
            Trabajos reales, cada uno con su diagrama y el nivel de evidencia: producto en línea, laboratorio propio o caso de cliente.
          </p>
        </div>
        <div className="marketing-grid marketing-grid--two">
          <article className="panel">
            <p className="eyebrow">Ninja Dev</p>
            <h3>Software que ya está funcionando</h3>
            <p>
              La plataforma con la que gestionamos clientes, proyectos y equipo, y el despliegue
              continuo que la publica solo y vuelve atrás si algo falla.
            </p>
            <Link className="button button-secondary" href="/proyectos#plataforma-ninjasec">Ver la plataforma</Link>
          </article>
          <article className="panel">
            <p className="eyebrow">Ninja Sec · Infraestructura segura</p>
            <h3>Redes que no paran</h3>
            <p>
              Una red segmentada con firewalls en alta disponibilidad y doble proveedor de internet,
              medida en nuestro laboratorio.
            </p>
            <Link className="button button-secondary" href="/proyectos#lab-alta-disponibilidad">Ver el diagrama</Link>
          </article>
        </div>
      </section>

      <section className="marketing-grid marketing-grid--two">
        <article className="panel">
          <p className="eyebrow">Portafolio</p>
          <h3>Capacidad real de ejecucion</h3>
          <p>
            {conApi
              ? "Ninja Tech demuestra integraciones API, modelado de datos, UX operacional y reporting automatizado aplicado a infraestructura y ciberseguridad."
              : "Revisiones de seguridad, gestión de infraestructura y desarrollo de software aplicados a las necesidades de pequeñas y medianas empresas."}
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">Comercial</p>
          <h3>{conApi ? "Proyecto, consultoria o MVP" : "Proyecto o consultoria"}</h3>
          <p>
            {conApi
              ? "Si necesitas un sistema a medida, dashboards o automatizacion de reportes, podemos definir alcance, tiempos y entregables desde este mismo producto."
              : "Si necesitas una revisión de seguridad, soporte de infraestructura o un sistema a medida, definimos contigo el alcance, los tiempos y los entregables."}
          </p>
          <div className="hero-actions">
            <Link className="button button-secondary" href="/contacto">Hablemos</Link>
            <Link className="button button-ghost" href="/servicios">Ver servicios</Link>
          </div>
        </article>
      </section>
    </PublicPageShell>
  );
}
