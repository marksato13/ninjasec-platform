"use client";

import { useState } from "react";

import type { DashboardClient, EstadoSistema, PlanSoporte, ProjectItem, SistemaCliente, SistemaIn } from "@/lib/api";
import { notifyError } from "@/lib/alerts";
import { ESTADO_SISTEMA, PLAN_SOPORTE } from "./etiquetas";
import s from "./ninja-dev.module.css";

type Props = {
  /** Sin sistema: alta. Con sistema: edición (el cliente no se cambia). */
  sistema?: SistemaCliente | null;
  /** Cliente fijo (pestaña de la ficha del cliente). */
  clientId?: number;
  clients: DashboardClient[];
  projects: ProjectItem[];
  saving: boolean;
  onSubmit: (payload: SistemaIn) => void;
};

export function FormSistema({ sistema, clientId, clients, projects, saving, onSubmit }: Props) {
  const [f, setF] = useState({
    client_id: String(sistema?.client_id ?? clientId ?? ""),
    name: sistema?.name ?? "",
    description: sistema?.description ?? "",
    stack: sistema?.stack ?? "",
    repository_url: sistema?.repository_url ?? "",
    status: (sistema?.status ?? "en_construccion") as EstadoSistema,
    warranty_until: sistema?.warranty_until ?? "",
    support_plan: (sistema?.support_plan ?? "ninguno") as PlanSoporte,
    origin_project_id: sistema?.origin_project_id ? String(sistema.origin_project_id) : "",
  });

  const proyectosDelCliente = projects.filter((p) => !f.client_id || p.client_id === Number(f.client_id));

  function enviar() {
    if (!f.client_id || !f.name.trim()) {
      notifyError("Faltan datos", "Cliente y nombre del sistema son obligatorios.");
      return;
    }
    onSubmit({
      client_id: Number(f.client_id),
      name: f.name.trim(),
      description: f.description.trim() || null,
      stack: f.stack.trim() || null,
      repository_url: f.repository_url.trim() || null,
      status: f.status,
      warranty_until: f.warranty_until || null,
      support_plan: f.support_plan,
      origin_project_id: f.origin_project_id ? Number(f.origin_project_id) : null,
    });
  }

  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setF((x) => ({ ...x, [k]: e.target.value }));

  return (
    <div className="entity-form">
      {!sistema && !clientId && (
        <select value={f.client_id} onChange={set("client_id")} aria-label="Cliente">
          <option value="">Cliente *</option>
          {clients.map((c) => <option key={c.id} value={c.id}>{c.company_name}</option>)}
        </select>
      )}
      <input value={f.name} onChange={set("name")} placeholder="Nombre del sistema *" maxLength={160} />
      <textarea
        value={f.description}
        onChange={set("description")}
        placeholder="Qué hace, en una línea que entienda el cliente"
        rows={2}
      />
      <input value={f.stack} onChange={set("stack")} placeholder="Stack (p. ej. Next.js + FastAPI + PostgreSQL)" maxLength={200} />
      <input value={f.repository_url} onChange={set("repository_url")} placeholder="Repositorio (no lo ve el cliente)" maxLength={500} />
      <div className={s.dosColumnas}>
        <label className="muted-small">
          Estado
          <select value={f.status} onChange={set("status")}>
            {(Object.keys(ESTADO_SISTEMA) as EstadoSistema[]).map((k) => (
              <option key={k} value={k}>{ESTADO_SISTEMA[k].label}</option>
            ))}
          </select>
        </label>
        <label className="muted-small">
          Plan de soporte
          <select value={f.support_plan} onChange={set("support_plan")}>
            {(Object.keys(PLAN_SOPORTE) as PlanSoporte[]).map((k) => (
              <option key={k} value={k}>{PLAN_SOPORTE[k]}</option>
            ))}
          </select>
        </label>
        <label className="muted-small">
          Garantía hasta
          <input type="date" value={f.warranty_until} onChange={set("warranty_until")} />
        </label>
        <label className="muted-small">
          Proyecto que lo construyó
          <select value={f.origin_project_id} onChange={set("origin_project_id")}>
            <option value="">Ninguno</option>
            {proyectosDelCliente.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
      </div>
      <p className="muted-small" style={{ margin: 0 }}>
        El colaborador ve el sistema solo si es miembro del proyecto que lo construyó.
      </p>
      <button className="button button-primary" type="button" disabled={saving} onClick={enviar}>
        {saving ? "Guardando…" : sistema ? "Guardar cambios" : "Registrar sistema"}
      </button>
    </div>
  );
}
