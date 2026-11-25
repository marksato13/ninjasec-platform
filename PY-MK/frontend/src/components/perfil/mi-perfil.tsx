"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";

import {
  AuthUser,
  changeMyPassword,
  getMe,
  getUserCertifications,
  getUserSkills,
  updateMyProfile,
  UserCertificationItem,
  UserSkillItem,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { Modal } from "@/components/ui/modal";

const ROLES: Record<string, string> = {
  client: "Cliente",
  collaborator: "Colaborador",
  admin: "Administrador",
  super_admin: "Super administrador",
};

function roleLabel(role: string) {
  return ROLES[role] ?? role.replaceAll("_", " ");
}

function ProfileCompleteness({ user, skills, certifications }: { user: AuthUser | null; skills: UserSkillItem[]; certifications: UserCertificationItem[] }) {
  const esCliente = user?.role === "client";
  const steps = [
    { label: "Nombre completo",      done: !!(user?.name || user?.full_name) },
    { label: "Email",                done: !!user?.email },
    { label: "Cargo registrado",     done: !!user?.job_title },
    ...(esCliente
      ? []
      : [
          { label: "Al menos una habilidad",     done: skills.length > 0 },
          { label: "Al menos una certificación", done: certifications.length > 0 },
        ]),
  ];
  const pct = Math.round((steps.filter((s) => s.done).length / steps.length) * 100);
  const color = pct === 100 ? "var(--success)" : pct >= 60 ? "var(--warning)" : "var(--danger)";

  return (
    <article className="panel">
      <div className="panel-head">
        <div><p className="eyebrow">Completitud</p><h3>Estado del perfil</h3></div>
        <strong style={{ fontSize: "1.3rem", color }}>{pct}%</strong>
      </div>
      <div style={{ background: "var(--line)", borderRadius: 8, height: 8, overflow: "hidden", marginBottom: 16 }}>
        <div style={{ width: "100%", height: "100%", background: color, borderRadius: 8, transform: `scaleX(${pct / 100})`, transformOrigin: "left", transition: "transform 0.4s var(--ease-out, ease-out)" }} />
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {steps.map((step) => (
          <div key={step.label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.82rem", color: step.done ? "var(--success)" : "var(--muted)" }}>
            <span style={{ fontSize: "1rem" }} aria-hidden="true">{step.done ? "✓" : "○"}</span>
            {step.label}
          </div>
        ))}
      </div>
    </article>
  );
}

/** Resumen de skills y certificaciones. Se registran y validan en Formación: un solo lugar. */
function ResumenFormacion({ skills, certifications }: { skills: UserSkillItem[]; certifications: UserCertificationItem[] }) {
  const pendientes = skills.filter((s) => s.status === "pending").length
    + certifications.filter((c) => c.status === "pending").length;
  const vigentes = certifications.filter((c) => c.effective_status === "approved").length;
  const porVencer = certifications.filter((c) => !c.is_expired && c.days_until_expiry !== null && c.days_until_expiry <= 30).length;

  return (
    <article className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Formación</p>
          <h3>Skills y certificaciones</h3>
          <p className="muted-small" style={{ margin: 0 }}>
            {skills.length} skill{skills.length === 1 ? "" : "s"} · {vigentes} certificación{vigentes === 1 ? "" : "es"} vigente{vigentes === 1 ? "" : "s"}
            {pendientes > 0 ? ` · ${pendientes} por validar` : ""}
            {porVencer > 0 ? ` · ${porVencer} por vencer` : ""}
          </p>
        </div>
        <Link className="button button-primary button-sm" href="/dashboard/formacion" style={{ gap: 6 }}>
          <GraduationCap size={14} aria-hidden="true" /> Gestionar en Formación
        </Link>
      </div>
    </article>
  );
}

export function MiPerfil() {
  const [editOpen, setEditOpen] = useState(false);
  const [pwOpen, setPwOpen] = useState(false);
  const [pwCurrent, setPwCurrent] = useState("");
  const [pwNew, setPwNew] = useState("");
  const [pwConfirm, setPwConfirm] = useState("");
  const [pwSaving, setPwSaving] = useState(false);
  const [editName, setEditName] = useState("");
  const [editJobTitle, setEditJobTitle] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["portal-profile"],
    queryFn: async () => {
      const me = await getMe();
      if (me.role === "client") {
        return { me, userSkills: [] as UserSkillItem[], certifications: [] as UserCertificationItem[] };
      }
      const [userSkills, certifications] = await Promise.all([getUserSkills(), getUserCertifications()]);
      return { me, userSkills, certifications };
    },
  });
  const user = data?.me ?? null;
  const userSkills = data?.userSkills ?? [];
  const certifications = data?.certifications ?? [];

  async function handleEditProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSavingEdit(true);
    try {
      await updateMyProfile({
        full_name: editName.trim() || null,
        job_title: editJobTitle.trim() || null,
      });
      notifySuccess("Perfil actualizado");
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["portal-profile"] });
    } catch (err) {
      notifyError("No se pudo actualizar el perfil", err instanceof Error ? err.message : "");
    } finally {
      setSavingEdit(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <h2>Tu perfil</h2>
      </div>

      <ProfileCompleteness user={user} skills={userSkills} certifications={certifications} />

      <article className="panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Cuenta</p>
            <h3>Tus datos</h3>
          </div>
          <div className="panel-actions">
            <button
              className="button button-ghost button-sm"
              type="button"
              onClick={() => { setPwCurrent(""); setPwNew(""); setPwConfirm(""); setPwOpen(true); }}
            >
              Cambiar contraseña
            </button>
            <button
              className="button button-secondary"
              type="button"
              onClick={() => {
                setEditName(user?.name || user?.full_name || "");
                setEditJobTitle(user?.job_title || "");
                setEditOpen(true);
              }}
            >
              Editar
            </button>
          </div>
        </div>
        {error ? <p className="form-error">{error instanceof Error ? error.message : "No se pudo cargar el perfil"}</p> : null}
        {isLoading ? (
          <div className="empty-state">Cargando perfil…</div>
        ) : user ? (
          <ul className="stack-list">
            <li><strong>Nombre:</strong> {user.name || user.full_name}</li>
            <li><strong>Email:</strong> {user.email}</li>
            <li><strong>Rol:</strong> {roleLabel(user.role)}</li>
            <li><strong>Cargo:</strong> {user.job_title || "Sin cargo"}</li>
          </ul>
        ) : (
          <div className="empty-state">No hay información disponible.</div>
        )}
      </article>

      {user && user.role !== "client" && <ResumenFormacion skills={userSkills} certifications={certifications} />}

      <Modal isOpen={pwOpen} title="Cambiar contraseña" onClose={() => setPwOpen(false)}>
        <form
          className="entity-form"
          onSubmit={async (e) => {
            e.preventDefault();
            if (pwNew !== pwConfirm) {
              notifyError("Las contraseñas no coinciden");
              return;
            }
            if (pwNew.length < 8) {
              notifyError("La nueva contraseña debe tener al menos 8 caracteres");
              return;
            }
            setPwSaving(true);
            try {
              await changeMyPassword({ current_password: pwCurrent, new_password: pwNew });
              notifySuccess("Contraseña actualizada");
              setPwOpen(false);
              setPwCurrent(""); setPwNew(""); setPwConfirm("");
            } catch (err) {
              notifyError("No se pudo cambiar la contraseña", err instanceof Error ? err.message : undefined);
            } finally {
              setPwSaving(false);
            }
          }}
        >
          <input type="password" autoComplete="current-password" placeholder="Contraseña actual" aria-label="Contraseña actual" value={pwCurrent} onChange={(e) => setPwCurrent(e.target.value)} required />
          <input type="password" autoComplete="new-password" placeholder="Nueva contraseña (mín. 8)" aria-label="Nueva contraseña" value={pwNew} onChange={(e) => setPwNew(e.target.value)} required minLength={8} />
          <input type="password" autoComplete="new-password" placeholder="Confirmar nueva contraseña" aria-label="Confirmar nueva contraseña" value={pwConfirm} onChange={(e) => setPwConfirm(e.target.value)} required />
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={pwSaving}>
              {pwSaving ? "Guardando…" : "Cambiar contraseña"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => setPwOpen(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={editOpen} title="Editar datos personales" onClose={() => setEditOpen(false)}>
        <form className="entity-form" onSubmit={handleEditProfile}>
          <input placeholder="Nombre completo" aria-label="Nombre completo" value={editName} onChange={(e) => setEditName(e.target.value)} />
          <input placeholder="Cargo" aria-label="Cargo" value={editJobTitle} onChange={(e) => setEditJobTitle(e.target.value)} />
          <div className="panel-actions">
            <button className="button button-primary" type="submit" disabled={savingEdit}>
              {savingEdit ? "Guardando…" : "Guardar cambios"}
            </button>
            <button className="button button-ghost" type="button" onClick={() => setEditOpen(false)}>
              Cancelar
            </button>
          </div>
        </form>
      </Modal>
    </section>
  );
}
