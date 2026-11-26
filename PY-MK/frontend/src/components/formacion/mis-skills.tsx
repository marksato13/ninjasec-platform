"use client";

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { createSkill, createUserSkill, getSkills, getUserSkills, updateUserSkill } from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { EmptyState } from "@/components/ui/empty-state";
import { ConMarca } from "@/components/ui/marca-icono";

import s from "./formacion.module.css";

const NIVELES = [
  { value: "1", label: "1 · Lo conozco" },
  { value: "2", label: "2 · Lo uso con ayuda" },
  { value: "3", label: "3 · Lo uso solo" },
  { value: "4", label: "4 · Lo enseño" },
  { value: "5", label: "5 · Referente" },
];
const ESTADO: Record<string, { texto: string; clase: string }> = {
  pending: { texto: "En validación", clase: "badge-pending" },
  approved: { texto: "Validada", clase: "badge-active" },
  rejected: { texto: "Rechazada", clase: "badge-rejected" },
};

export function Nivel({ valor }: { valor: string | null | undefined }) {
  const n = Number(valor);
  if (!Number.isInteger(n) || n < 1 || n > 5) return <span className="muted-small">{valor || "—"}</span>;
  return (
    <span className={s.nivel} role="img" aria-label={`Nivel ${n} de 5`}>
      {[1, 2, 3, 4, 5].map((i) => <span key={i} data-on={i <= n} />)}
    </span>
  );
}

export function MisSkills({ userId }: { userId: number | undefined }) {
  const qc = useQueryClient();
  const [skillId, setSkillId] = useState("");
  const [nueva, setNueva] = useState("");
  const [nivel, setNivel] = useState("3");

  const catalogo = useQuery({ queryKey: QK.skills(), queryFn: getSkills });
  const declaradas = useQuery({ queryKey: QK.userSkills(), queryFn: getUserSkills });
  const mias = (declaradas.data ?? []).filter((u) => u.user_id === userId);
  const yaTengo = new Set(mias.map((m) => m.skill_id));

  const refrescar = () => qc.invalidateQueries({ queryKey: QK.userSkills() });

  const declarar = useMutation({
    mutationFn: async () => {
      let id = Number(skillId);
      if (skillId === "nueva") {
        const creada = await createSkill({ name: nueva.trim() });
        qc.invalidateQueries({ queryKey: QK.skills() });
        id = creada.id;
      }
      return createUserSkill({ skill_id: id, level: nivel });
    },
    onSuccess: () => {
      refrescar();
      setSkillId("");
      setNueva("");
      notifySuccess("Skill declarada", "Queda en validación.");
    },
    onError: (e) => notifyError("No se pudo declarar", e instanceof Error ? e.message : undefined),
  });

  const cambiarNivel = useMutation({
    mutationFn: (v: { id: number; level: string }) => updateUserSkill(v.id, { level: v.level }),
    onSuccess: refrescar,
    onError: (e) => notifyError("No se pudo cambiar el nivel", e instanceof Error ? e.message : undefined),
  });

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    if (!skillId || (skillId === "nueva" && nueva.trim().length < 2)) {
      notifyError("Elige una skill", "Selecciona una del catálogo o escribe una nueva.");
      return;
    }
    declarar.mutate();
  };

  return (
    <div className="page-stack">
      <article className="panel">
        <p className={s.intro} style={{ marginBottom: 14 }}>
          Declara lo que sabes hacer y en qué nivel. El super admin lo valida; las skills validadas cuentan para asignarte
          a proyectos.
        </p>
        <form className={s.form} onSubmit={enviar}>
          <label>
            Skill
            <select value={skillId} onChange={(e) => setSkillId(e.target.value)}>
              <option value="">Elige una</option>
              {(catalogo.data ?? [])
                .filter((k) => k.is_active && !yaTengo.has(k.id))
                .map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}
              <option value="nueva">Otra, que no está en la lista…</option>
            </select>
          </label>
          {skillId === "nueva" ? (
            <label>
              Nombre de la skill
              <input maxLength={120} value={nueva} onChange={(e) => setNueva(e.target.value)} placeholder="FortiGate SD-WAN" />
            </label>
          ) : null}
          <label>
            Nivel
            <select value={nivel} onChange={(e) => setNivel(e.target.value)}>
              {NIVELES.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
            </select>
          </label>
          <div className={s.formActions}>
            <button type="submit" className="button button-primary" disabled={declarar.isPending}>
              {declarar.isPending ? "Guardando…" : "Declarar skill"}
            </button>
          </div>
        </form>
      </article>

      {declaradas.error ? <p className="form-error">No se pudieron cargar tus skills.</p> : null}
      {!declaradas.isLoading && !declaradas.error && mias.length === 0 ? (
        <EmptyState icon={Sparkles} title="Aún no declaras skills" description="Empieza por la herramienta que más usas en los proyectos." />
      ) : null}

      {mias.length > 0 ? (
        <div className={s.skills}>
          {mias.map((m) => {
            const estado = ESTADO[m.status] ?? { texto: m.status, clase: "badge-pending" };
            return (
              <div key={m.id} className={s.skill}>
                <div>
                  <strong><ConMarca nombre={m.skill_name ?? `Skill #${m.skill_id}`} size={18} /></strong>
                  {m.status === "rejected" && m.rejection_reason ? (
                    <p className="muted-small" style={{ margin: "4px 0 0" }}>Motivo: {m.rejection_reason}</p>
                  ) : null}
                </div>
                <select
                  aria-label={`Nivel en ${m.skill_name}`}
                  value={m.level ?? ""}
                  disabled={cambiarNivel.isPending}
                  onChange={(e) => cambiarNivel.mutate({ id: m.id, level: e.target.value })}
                >
                  {!NIVELES.some((n) => n.value === m.level) ? <option value={m.level ?? ""}>{m.level || "Sin nivel"}</option> : null}
                  {NIVELES.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
                </select>
                <span className={`badge ${estado.clase}`}>{estado.texto}</span>
              </div>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
