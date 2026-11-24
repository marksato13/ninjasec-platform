import { notFound } from "next/navigation";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { capsulaActiva } from "@/lib/capsulas";

export default function SolucionPage() {
  // Esta pagina describe conectores por API, y los conectores son simulados
  // mientras la capsula de telemetria este apagada. Ocultarla del menu no
  // basta: quien teclee /solucion llegaria igual. Por eso se cierra.
  if (!capsulaActiva("telemetria")) notFound();

  return (
    <PublicPageShell>
      <section className="content-hero">
        <p className="eyebrow">Solucion</p>
        <h1>Como funciona NinjaSec.</h1>
        <p>
          La plataforma conecta dispositivos y sistemas por API, procesa datos y genera dashboards
          y reportes que reducen trabajo manual y elevan la visibilidad operativa.
        </p>
      </section>

      <section className="marketing-grid marketing-grid--three">
        <article className="panel"><h3>1. Conectores</h3><p>Integraciones con pfSense, FortiGate y futuras plataformas.</p></article>
        <article className="panel"><h3>2. Normalización</h3><p>Transformamos datos dispersos en métricas consistentes.</p></article>
        <article className="panel"><h3>3. Reportes</h3><p>Entregamos resultados técnicos y ejecutivos listos para usar.</p></article>
      </section>
    </PublicPageShell>
  );
}
