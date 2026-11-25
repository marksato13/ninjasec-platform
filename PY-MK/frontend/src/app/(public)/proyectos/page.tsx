import Link from "next/link";

import { DiagramaProyecto } from "@/components/public/diagrama-proyecto";
import { PublicPageShell } from "@/components/public/public-page-shell";
import {
  EVIDENCIA_ETIQUETA,
  proyectosVisibles,
  type Linea,
  type ProyectoPublico,
} from "@/lib/portafolio";

export const metadata = {
  title: "Proyectos · Ninja Tech",
  description: "Lo que Ninja Tech ha construido en desarrollo e infraestructura, con su diagrama y el nivel de evidencia de cada trabajo.",
};

const LINEAS: { id: Linea; titulo: string; texto: string }[] = [
  { id: "dev", titulo: "Desarrollo", texto: "Software que construimos y que puedes ver funcionando." },
  { id: "infra", titulo: "Infraestructura y nube", texto: "Redes, seguridad y nube, con su diagrama y su nivel de evidencia." },
];

function Tarjeta({ p }: { p: ProyectoPublico }) {
  const ev = EVIDENCIA_ETIQUETA[p.evidencia];
  return (
    <article className="panel" id={p.id} style={{ display: "grid", gap: 14 }}>
      <header style={{ display: "grid", gap: 6 }}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <span
            className={`badge ${p.evidencia === "preparacion" ? "badge-draft" : "badge-active"}`}
            title={ev.ayuda}
          >
            {ev.texto}
          </span>
          {p.tecnologias.map((t) => (
            <span key={t} className="pill" style={{ fontSize: "0.72rem" }}>{t}</span>
          ))}
        </div>
        <h3 style={{ margin: 0 }}>{p.titulo}</h3>
        <p style={{ margin: 0 }}>{p.resumen}</p>
        <p className="muted-small" style={{ margin: 0 }}>{ev.ayuda}</p>
      </header>

      {p.diagrama && (
        <DiagramaProyecto
          titulo={p.diagrama.titulo}
          nodos={p.diagrama.nodos}
          aristas={p.diagrama.aristas}
          alto={p.id === "lab-alta-disponibilidad" ? 480 : 380}
        />
      )}

      <ul style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 6 }}>
        {p.detalle.map((d) => (
          <li key={d}>{d}</li>
        ))}
      </ul>

      {p.limites && (
        <p className="muted-small" style={{ margin: 0 }}>
          <strong>Lo que hay que saber:</strong> {p.limites}
        </p>
      )}
    </article>
  );
}

export default function ProyectosPage() {
  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Proyectos</p>
        <h1>Lo que hemos construido, y con qué nivel de evidencia.</h1>
        <p>
          Cada trabajo indica si es un producto en línea, un laboratorio propio o un caso de cliente.
          No mezclamos las tres cosas: te decimos qué es cada una.
        </p>
      </section>

      {LINEAS.map((linea) => {
        const items = proyectosVisibles(linea.id);
        if (items.length === 0) return null;
        return (
          <section className="page-stack" key={linea.id}>
            <div>
              <h2>{linea.titulo}</h2>
              <p className="muted-small" style={{ margin: 0 }}>{linea.texto}</p>
            </div>
            {items.map((p) => (
              <Tarjeta key={p.id} p={p} />
            ))}
          </section>
        );
      })}

      <section className="content-hero">
        <p className="eyebrow">¿Tienes un caso parecido?</p>
        <h2>Conversemos.</h2>
        <p>Cuéntanos qué necesitas y te decimos cómo lo abordaríamos, y qué sabemos hacer y qué no.</p>
        <div className="hero-actions">
          <Link className="button button-primary" href="/agenda-demo?origen=proyectos">Agenda una reunión</Link>
          <Link className="button button-secondary" href="/servicios">Ver servicios</Link>
        </div>
      </section>
    </PublicPageShell>
  );
}
