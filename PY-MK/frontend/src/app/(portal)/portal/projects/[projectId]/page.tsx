"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { EquipoCertificado } from "@/components/formacion/equipo-certificado";
import { HitosDePago } from "@/components/tracking/hitos-de-pago";
import { SeguimientoVista } from "@/components/tracking/seguimiento-vista";
import { PruebasAceptacion } from "@/components/uat/pruebas-aceptacion";

/** Lo que ve el cliente: el recorrido de SU proyecto, quién trabaja y qué va pasando. */
export default function PortalProyectoPage() {
  const params = useParams();
  const id = Number(params?.projectId);

  if (!Number.isFinite(id)) return <div className="state-panel">Proyecto no válido.</div>;

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <h2>Seguimiento de tu proyecto</h2>
        </div>
        <Link className="button button-ghost" href="/portal/projects">Volver a mis proyectos</Link>
      </div>
      <SeguimientoVista proyectoId={id} modo="cliente" />
      <PruebasAceptacion projectId={id} modo="cliente" />
      <HitosDePago projectId={id} />
      <EquipoCertificado projectId={id} />
    </section>
  );
}
