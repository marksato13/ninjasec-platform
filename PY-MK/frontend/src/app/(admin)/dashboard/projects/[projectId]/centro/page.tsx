"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { HitosDePago } from "@/components/tracking/hitos-de-pago";
import { SeguimientoVista } from "@/components/tracking/seguimiento-vista";

/** Lo que ve el especialista: lo mismo que el cliente, más el centro de mando para alimentarlo. */
export default function CentroDelProyectoPage() {
  const params = useParams();
  const id = Number(params?.projectId);

  if (!Number.isFinite(id)) return <div className="state-panel">Proyecto no válido.</div>;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Proyecto</p>
          <h2>Centro de mando</h2>
        </div>
        <div className="panel-actions">
          <Link className="button button-ghost" href={`/dashboard/projects/${id}`}>Detalle del proyecto</Link>
          <Link className="button button-ghost" href="/dashboard/projects">Volver</Link>
        </div>
      </div>
      <SeguimientoVista proyectoId={id} modo="equipo" />
      <HitosDePago projectId={id} />
    </section>
  );
}
