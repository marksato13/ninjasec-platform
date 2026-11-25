import Image from "next/image";
import Link from "next/link";

import { DiagramaProyecto } from "@/components/public/diagrama-proyecto";
import { PublicPageShell } from "@/components/public/public-page-shell";
import {
  AREAS_EN_PREPARACION,
  EVIDENCIA_ETIQUETA,
  proyectosVisibles,
  type Linea,
  type ProyectoPublico,
} from "@/lib/portafolio";

export const metadata = {
  title: "Proyectos · Ninja Tech",
  description:
    "Lo que Ninja Tech ha construido en ciberseguridad (Ninja Sec) y desarrollo de software (Ninja Dev), con su diagrama y el nivel de evidencia de cada trabajo.",
};

const RAMAS: {
  id: Extract<Linea, "sec" | "dev">;
  ancla: string;
  nombre: string;
  texto: string;
  avatar: string;
  pose: string;
}[] = [
  {
    id: "sec",
    ancla: "ninja-sec",
    nombre: "Ninja Sec",
    texto: "Ciberseguridad e infraestructura segura: redes que resisten, y análisis para detectar lo anómalo.",
    avatar: "/brand/avatar-ninja-sec.webp",
    pose: "/brand/poses/sec-escudo-red.webp",
  },
  {
    id: "dev",
    ancla: "ninja-dev",
    nombre: "Ninja Dev",
    texto: "Desarrollo de software: sistemas que construimos y que puedes ver funcionando.",
    avatar: "/brand/avatar-ninja-dev.webp",
    pose: "/brand/poses/dev-sentado-laptop.webp",
  },
];

/** Agrupa por subárea conservando el orden en que aparecen. Sin subárea, un solo grupo sin título. */
function porSubarea(items: ProyectoPublico[]) {
  const grupos: { titulo: string | null; items: ProyectoPublico[] }[] = [];
  for (const p of items) {
    const titulo = p.subarea ?? null;
    const g = grupos.find((x) => x.titulo === titulo);
    if (g) g.items.push(p);
    else grupos.push({ titulo, items: [p] });
  }
  return grupos;
}

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

      {p.enlaces && p.enlaces.length > 0 && (
        <div className="hero-actions">
          {p.enlaces.map((e) => (
            <a
              key={e.href}
              className="button button-secondary"
              href={e.href}
              target="_blank"
              rel="noopener noreferrer"
            >
              {e.texto} ↗
            </a>
          ))}
        </div>
      )}
    </article>
  );
}

export default function ProyectosPage() {
  const cloud = proyectosVisibles("cloud");

  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Proyectos</p>
        <h1>Lo que hemos construido, y con qué nivel de evidencia.</h1>
        <p>
          Cada trabajo está en una de nuestras dos ramas activas, Ninja Sec y Ninja Dev, e indica qué es:
          un producto en línea, un laboratorio propio, una investigación abierta o un caso de cliente.
          No mezclamos las cosas: te decimos qué es cada una.
        </p>
        <p className="muted-small" style={{ margin: 0 }}>
          <strong>Ojo con tres significados distintos.</strong> La <em>disponibilidad</em> de un servicio
          dice si lo puedes contratar hoy (está en <Link href="/servicios">Servicios</Link>). El{" "}
          <em>estado de un proyecto</em> dice qué respaldo tiene lo que mostramos aquí. Una{" "}
          <em>futura rama</em> es un área que todavía no existe y no se contrata.
        </p>
      </section>

      {RAMAS.map((rama) => {
        const items = proyectosVisibles(rama.id);
        if (items.length === 0) return null;
        return (
          <section className="page-stack" key={rama.id} id={rama.ancla}>
            <div className="rama-head">
              <Image src={rama.avatar} alt={`Logo de ${rama.nombre}`} width={72} height={72} className="rama-head__logo" />
              <div>
                <h2 style={{ margin: 0 }}>{rama.nombre}</h2>
                <p className="muted-small" style={{ margin: 0 }}>{rama.texto}</p>
              </div>
              <Image src={rama.pose} alt="" aria-hidden width={140} height={140} className="rama-head__pose" />
            </div>

            {porSubarea(items).map((g) => (
              <div key={g.titulo ?? "todo"} style={{ display: "grid", gap: 16 }}>
                {g.titulo && <h3 className="rama-subarea">{g.titulo}</h3>}
                {g.items.map((p) => (
                  <Tarjeta key={p.id} p={p} />
                ))}
              </div>
            ))}
          </section>
        );
      })}

      <section className="page-stack" id="areas-en-preparacion">
        <div>
          <h2>Áreas en preparación</h2>
          <p className="muted-small" style={{ margin: 0 }}>
            Ramas que todavía no existen. No son servicios que puedas contratar hoy: te contamos hacia dónde vamos.
          </p>
        </div>
        <div className="marketing-grid marketing-grid--three">
          {AREAS_EN_PREPARACION.map((a) => (
            <article className="panel area-futura" key={a.id} id={a.id}>
              <span className="badge badge-draft">En preparación</span>
              <h3 style={{ margin: "10px 0 6px" }}>{a.nombre}</h3>
              <p style={{ margin: 0 }}>{a.texto}</p>
              {a.nota && <p className="muted-small" style={{ margin: "8px 0 0" }}>{a.nota}</p>}
              {a.linea === "cloud" && cloud.length > 0 && (
                <div className="area-futura__proyecto">
                  {cloud.map((p) => (
                    <div key={p.id} id={p.id}>
                      <p style={{ margin: "0 0 4px", fontWeight: 600 }}>{p.titulo}</p>
                      <p className="muted-small" style={{ margin: 0 }}>{p.resumen}</p>
                      <p className="muted-small" style={{ margin: "6px 0 0" }}>
                        {EVIDENCIA_ETIQUETA[p.evidencia].ayuda} Cuando exista, aparecerá con su diagrama y sus
                        mediciones, y no antes.
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      </section>

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
