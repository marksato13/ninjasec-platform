"use client";

import { Suspense } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { getPendingApprovalsCount } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";
import { MatrizEquipo } from "@/components/formacion/matriz-equipo";
import { MisCertificaciones } from "@/components/formacion/mis-certificaciones";
import { MisSkills } from "@/components/formacion/mis-skills";
import { RutasEstudio } from "@/components/formacion/rutas-estudio";
import { Validar } from "@/components/formacion/validar";

type Pestania = "certificaciones" | "skills" | "rutas" | "validar" | "equipo";

/**
 * Formacion: las credenciales del equipo, no un aula.
 *
 * Los cursos se toman en la plataforma de cada fabricante (Fortinet, Cisco, AWS...).
 * Aqui se registra el resultado, se adjunta el certificado, el super admin lo
 * valida y el cliente ve al personal certificado en sus proyectos.
 */
function Formacion() {
  const user = getStoredUser();
  const esAdmin = user?.role === "admin" || user?.role === "super_admin";
  const esSuper = user?.role === "super_admin";
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const pendientes = useQuery({
    queryKey: QK.pendingApprovals(),
    queryFn: getPendingApprovalsCount,
    enabled: esSuper,
  });

  const pestanias: { id: Pestania; label: string; visible: boolean }[] = [
    { id: "certificaciones", label: "Mis certificaciones", visible: true },
    { id: "skills", label: "Mis skills", visible: true },
    { id: "rutas", label: "Rutas de estudio", visible: true },
    {
      id: "validar",
      label: pendientes.data?.pending ? `Validar (${pendientes.data.pending})` : "Validar",
      visible: esAdmin,
    },
    { id: "equipo", label: "Equipo", visible: esAdmin },
  ];
  const visibles = pestanias.filter((p) => p.visible);
  const pedida = params.get("tab") as Pestania | null;
  const activa: Pestania = visibles.some((p) => p.id === pedida) ? (pedida as Pestania) : "certificaciones";

  const ir = (id: Pestania) => {
    const q = new URLSearchParams(params.toString());
    if (id === "certificaciones") q.delete("tab");
    else q.set("tab", id);
    const qs = q.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Equipo</p>
          <h2>Formación</h2>
        </div>
      </div>

      <div className="tab-list" role="tablist" aria-label="Secciones de formación">
        {visibles.map((p) => (
          <button
            key={p.id}
            type="button"
            role="tab"
            id={`tab-${p.id}`}
            aria-selected={activa === p.id}
            aria-controls={`panel-${p.id}`}
            className={`tab ${activa === p.id ? "tab-active" : ""}`}
            onClick={() => ir(p.id)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`panel-${activa}`} aria-labelledby={`tab-${activa}`}>
        {activa === "certificaciones" && <MisCertificaciones userId={user?.id} />}
        {activa === "skills" && <MisSkills userId={user?.id} />}
        {activa === "rutas" && <RutasEstudio userId={user?.id} />}
        {activa === "validar" && esAdmin && <Validar puedeValidar={esSuper} />}
        {activa === "equipo" && esAdmin && <MatrizEquipo />}
      </div>
    </section>
  );
}

export default function FormacionPage() {
  return (
    <Suspense fallback={<div className="empty-state">Cargando…</div>}>
      <Formacion />
    </Suspense>
  );
}
