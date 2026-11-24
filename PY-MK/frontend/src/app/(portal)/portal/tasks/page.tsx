"use client";

import { ListChecks } from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getProjectTasks, updateMyTaskStatus } from "@/lib/api";
import { notifyError } from "@/lib/alerts";

const STATUS_LABEL: Record<string, string> = {
  pending:     "Pendiente",
  in_progress: "En curso",
  done:        "Hecha",
};

export default function PortalTasksPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const qc = useQueryClient();

  const mover = useMutation({
    mutationFn: ({ id, status }: { id: number; status: "pending" | "in_progress" | "done" }) =>
      updateMyTaskStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portal-my-tasks"] }),
    onError: (e: unknown) =>
      notifyError("No se pudo cambiar el estado", e instanceof Error ? e.message : undefined),
  });

  const { data: tasks = [], isLoading, error } = useQuery({
    queryKey: ["portal-my-tasks"],
    queryFn:  () => getProjectTasks(),
  });

  const filtered = tasks.filter((t) =>
    statusFilter ? t.status === statusFilter : true
  );

  const pendingCount    = tasks.filter((t) => t.status === "pending").length;
  const inProgressCount = tasks.filter((t) => t.status === "in_progress").length;
  const doneCount       = tasks.filter((t) => t.status === "done").length;

  return (
    <section className="page-stack">
      {/* Encabezado */}
      <div className="section-heading">
        <div>
          <p className="eyebrow">Portal</p>
          <h2>Mis tareas</h2>
        </div>
        <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
          {tasks.length} tarea{tasks.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* KPIs */}
      <div className="metrics-grid">
        {[
          { label: "Pendientes", value: pendingCount },
          { label: "En curso",   value: inProgressCount },
          { label: "Hechas",     value: doneCount },
          { label: "Total",      value: tasks.length },
        ].map((kpi) => (
          <article className="metric-card panel" key={kpi.label}>
            <p className="eyebrow">{kpi.label}</p>
            <strong>{kpi.value}</strong>
          </article>
        ))}
      </div>

      {/* Filtro */}
      <div className="panel-actions">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Todos los estados</option>
          <option value="pending">Pendientes</option>
          <option value="in_progress">En curso</option>
          <option value="done">Hechas</option>
        </select>
      </div>

      {/* Lista */}
      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Asignaciones</p>
            <h3>Tareas de tus proyectos</h3>
          </div>
        </div>

        {error && <p className="form-error">Error al cargar tareas</p>}

        {isLoading ? (
          <div className="empty-state">Cargando tareas…</div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <ListChecks size={28} style={{ opacity: 0.35, margin: "0 auto 8px", display: "block" }} />
            No tienes tareas{statusFilter ? " con ese estado" : ""} todavía.
          </div>
        ) : (
          <div className="table-like">
            <div className="table-row table-head" style={{ gridTemplateColumns: "2fr 1.4fr 1fr 1fr 2fr" }}>
              <span>Tarea</span>
              <span>Proyecto</span>
              <span>Responsable</span>
              <span>Estado</span>
              <span>Descripción</span>
            </div>
            {filtered.map((task) => (
              <div
                className="table-row"
                key={task.id}
                style={{ gridTemplateColumns: "2fr 1.4fr 1fr 1fr 2fr" }}
              >
                <span style={{ fontWeight: 600 }}>{task.title}</span>
                <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>{task.project_name}</span>
                <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>{task.assigned_user_name}</span>
                <span>
                  <select
                    aria-label={`Estado de la tarea ${task.title}`}
                    value={task.status}
                    disabled={mover.isPending}
                    onChange={(e) =>
                      mover.mutate({ id: task.id, status: e.target.value as "pending" | "in_progress" | "done" })
                    }
                  >
                    <option value="pending">{STATUS_LABEL.pending}</option>
                    <option value="in_progress">{STATUS_LABEL.in_progress}</option>
                    <option value="done">{STATUS_LABEL.done}</option>
                  </select>
                </span>
                <span style={{ color: "var(--muted)", fontSize: "0.82rem" }}>
                  {task.description?.slice(0, 60) ?? "—"}
                  {(task.description?.length ?? 0) > 60 ? "…" : ""}
                </span>
              </div>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}
