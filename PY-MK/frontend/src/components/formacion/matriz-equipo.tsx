"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";

import { getTeamMatrix, type AreaCert, type CertificacionPublica } from "@/lib/api";
import { QK } from "@/lib/query-keys";
import { EmptyState } from "@/components/ui/empty-state";
import { ConMarca } from "@/components/ui/marca-icono";

import s from "./formacion.module.css";
import { Nivel } from "./mis-skills";
import { AREAS, fecha } from "./utils";

const ROL: Record<string, string> = { super_admin: "Super admin", admin: "Admin", collaborator: "Colaborador" };

const enArea = (c: CertificacionPublica, filtro: AreaCert | "todas") =>
  filtro === "todas" || c.area === filtro || c.area === "both";

/** Quién sabe qué: solo lo validado y vigente, que es lo que se le puede prometer a un cliente. */
export function MatrizEquipo() {
  const [filtro, setFiltro] = useState<AreaCert | "todas">("todas");
  const matriz = useQuery({ queryKey: QK.teamMatrix(), queryFn: getTeamMatrix });

  if (matriz.isLoading) return <div className="empty-state">Cargando el equipo…</div>;
  if (matriz.error) return <p className="form-error">No se pudo cargar la matriz del equipo.</p>;
  const filas = matriz.data ?? [];
  if (filas.length === 0) return <EmptyState icon={Users} title="Todavía no hay equipo" description="Invita colaboradores desde Usuarios." />;

  return (
    <div className="page-stack">
      <div className={s.toolbar}>
        <p className={s.intro}>Solo cuenta lo validado y vigente: es lo que puedes ofrecerle a un cliente.</p>
        <div className="tab-list" role="tablist" aria-label="Filtrar por área">
          {[{ value: "todas" as const, label: "Todas" }, ...AREAS.filter((a) => a.value !== "both")].map((a) => (
            <button
              key={a.value}
              type="button"
              role="tab"
              aria-selected={filtro === a.value}
              className={`tab ${filtro === a.value ? "tab-active" : ""}`}
              onClick={() => setFiltro(a.value)}
            >
              {a.label}
            </button>
          ))}
        </div>
      </div>

      <div className={s.matriz} role="table" aria-label="Capacidades del equipo">
        <div className={`${s.fila} ${s.filaHead}`} role="row">
          <span role="columnheader">Persona</span>
          <span role="columnheader">Certificaciones validadas</span>
          <span role="columnheader">Skills validadas</span>
        </div>
        {filas.map((f) => {
          const certs = f.certifications.filter((c) => enArea(c, filtro));
          return (
            <div key={f.user_id} className={s.fila} role="row">
              <div role="cell">
                <strong>{f.full_name}</strong>
                <p className="muted-small" style={{ margin: 0 }}>{ROL[f.role] ?? f.role}</p>
              </div>
              <div role="cell" className={s.chips}>
                {certs.length === 0 ? <span className="muted-small">—</span> : certs.map((c) => (
                  <span
                    key={`${c.name}-${c.issued_at}`}
                    className={`${s.chip} ${c.area ? s[`area-${c.area}`] : ""}`}
                    title={`${c.issuer ?? "Emisor sin indicar"}${c.expires_at ? ` · vence ${fecha(c.expires_at)}` : ""}`}
                  >
                    {c.name}
                  </span>
                ))}
              </div>
              <div role="cell" className={s.chips}>
                {f.skills.length === 0 ? <span className="muted-small">—</span> : f.skills.map((k) => (
                  <span key={k.name} className={`${s.chip} ${s.chipMarca}`} style={{ gap: 8 }}>
                    <ConMarca nombre={k.name} size={14} /> <Nivel valor={k.level} />
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
