import Link from "next/link";
import { ArrowRight, FilePieChart, Gauge, Plug, ShieldCheck } from "lucide-react";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { Mascot } from "@/components/ui/mascot";

const STATS = [
  { value: "17", label: "clientes monitoreados" },
  { value: "73", label: "dispositivos gestionados" },
  { value: "62", label: "hallazgos identificados" },
  { value: "28", label: "revisiones de seguridad" },
];

const STEPS = [
  { icon: Plug, title: "Conecta", text: "Integra pfSense, FortiGate y otras plataformas de red y seguridad por API." },
  { icon: Gauge, title: "Consolida", text: "NinjaSec normaliza y centraliza los datos técnicos de todos tus dispositivos." },
  { icon: ShieldCheck, title: "Visualiza", text: "Dashboards operativos y ejecutivos, actualizados en tiempo casi real." },
  { icon: FilePieChart, title: "Reporta", text: "Reportes técnicos y ejecutivos listos para entregar, sin trabajo manual." },
];

export default function HomePage() {
  return (
    <PublicPageShell>
      <section className="landing-hero-wrap">
        <div className="login-grid-bg" aria-hidden />
        <div className="login-orb login-orb--blue" aria-hidden />
        <div className="login-orb login-orb--cyan" aria-hidden />

        <div className="hero-marketing landing-reveal">
          <div>
            <span className="pill">NinjaSec Platform</span>
            <h1>Reporting inteligente por API para infraestructura, seguridad y operaciones TI.</h1>
            <p>
              NinjaSec transforma datos técnicos de dispositivos y plataformas como pfSense y FortiGate
              en dashboards, reportes ejecutivos y servicios tecnológicos listos para empresas y MSPs.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" href="/agenda-demo">Agenda una demo</Link>
              <Link className="button button-secondary" href="/solucion">Ver solucion</Link>
            </div>
            <div className="landing-stats">
              {STATS.map((stat) => (
                <div className="landing-stat" key={stat.label}>
                  <strong>{stat.value}</strong>
                  <span>{stat.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="hero-visual-card hero-mascot-card">
            <Mascot variant="working" size="lg" priority />
            <div className="hero-mascot-badge">
              <span className="dot" />
              Kuro está vigilando tu red
            </div>
          </div>
        </div>
      </section>

      <section className="page-stack landing-reveal landing-reveal--delay-1">
        <p className="eyebrow" style={{ textAlign: "center" }}>Cómo funciona</p>
        <div className="landing-steps">
          {STEPS.map((step, index) => (
            <article className="panel landing-step" key={step.title}>
              <step.icon size={20} aria-hidden style={{ color: "var(--primary, #3B82F6)" }} />
              <h4>{step.title}</h4>
              <p>{step.text}</p>
              {index < STEPS.length - 1 && (
                <ArrowRight className="landing-step-arrow" size={22} aria-hidden />
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="marketing-grid marketing-grid--three landing-reveal landing-reveal--delay-2">
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
      </section>

      <section className="marketing-grid marketing-grid--two">
        <article className="panel">
          <p className="eyebrow">Portafolio</p>
          <h3>Capacidad real de ejecucion</h3>
          <p>
            NinjaSec demuestra integraciones API, modelado de datos, UX operacional y reporting
            automatizado aplicado a infraestructura y ciberseguridad.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">Comercial</p>
          <h3>Proyecto, consultoria o MVP</h3>
          <p>
            Si necesitas un sistema a medida, dashboards o automatizacion de reportes, podemos
            definir alcance, tiempos y entregables desde este mismo producto.
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
