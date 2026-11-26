"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Pencil, Plus, Trash2 } from "lucide-react";

import {
  createSystemEnvironment,
  deleteClientSystem,
  deleteSystemEnvironment,
  getClients,
  getClientSystem,
  getProjects,
  updateClientSystem,
  updateSystemEnvironment,
  type DashboardClient,
  type EntornoIn,
  type EntornoSistema,
  type FichaSistema as Ficha,
  type ProjectItem,
  type SistemaIn,
  type TipoEntorno,
} from "@/lib/api";
import { confirmAction, notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";
import { DesplieguesBoard } from "./despliegues-board";
import { ENTORNO, ESTADO_SISTEMA, PLAN_SOPORTE, fechaCorta, mensajeError, textoVence } from "./etiquetas";
import { FormSistema } from "./form-sistema";
import s from "./ninja-dev.module.css";

const TIPOS: TipoEntorno[] = ["dev", "staging", "prod"];

type FormEntorno = {
  kind: TipoEntorno;
  url: string;
  hosting: string;
  domain_expires_at: string;
  certificate_expires_at: string;
  secrets_location: string;
  visible_to_client: boolean;
};

function formDe(e?: EntornoSistema | null, kind: TipoEntorno = "prod"): FormEntorno {
  return {
    kind: e?.kind ?? kind,
    url: e?.url ?? "",
    hosting: e?.hosting ?? "",
    domain_expires_at: e?.domain_expires_at ?? "",
    certificate_expires_at: e?.certificate_expires_at ?? "",
    secrets_location: e?.secrets_location ?? "",
    visible_to_client: e?.visible_to_client ?? (kind === "prod"),
  };
}

/** Ficha de un sistema: datos, entornos con sus vencimientos y despliegues. */
export function FichaSistema({ id }: { id: number }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  // null: cerrado. { env: null }: alta. { env }: edición.
  const [entornoModal, setEntornoModal] = useState<{ env: EntornoSistema | null } | null>(null);
  const [fe, setFe] = useState<FormEntorno>(formDe());

  const { data: sistema, isLoading, error } = useQuery<Ficha>({
    queryKey: QK.clientSystem(id),
    queryFn: () => getClientSystem(id),
    enabled: Number.isFinite(id),
  });
  const puede = !!sistema?.can_manage;
  const { data: clients = [] } = useQuery<DashboardClient[]>({ queryKey: QK.clients(), queryFn: getClients, enabled: puede });
  const { data: projects = [] } = useQuery<ProjectItem[]>({ queryKey: QK.projects(), queryFn: getProjects, enabled: puede });

  function aplicar(f: Ficha) {
    queryClient.setQueryData(QK.clientSystem(id), f);
    queryClient.invalidateQueries({ queryKey: ["client-systems"] });
  }

  async function guardar(payload: SistemaIn) {
    setSaving(true);
    try {
      // El cliente de un sistema no se cambia.
      const { name, description, stack, repository_url, status, warranty_until, support_plan, origin_project_id } = payload;
      aplicar(await updateClientSystem(id, {
        name, description, stack, repository_url, status, warranty_until, support_plan, origin_project_id,
      }));
      notifySuccess("Sistema actualizado");
      setEditOpen(false);
    } catch (err) {
      notifyError("No se pudo guardar", mensajeError(err));
    } finally {
      setSaving(false);
    }
  }

  async function borrar() {
    const ok = await confirmAction({
      title: "¿Borrar este sistema?",
      text: "Solo se puede mientras está en construcción. Uno que llegó a producción se marca como retirado.",
      confirmText: "Borrar",
    });
    if (!ok) return;
    try {
      await deleteClientSystem(id);
      queryClient.invalidateQueries({ queryKey: ["client-systems"] });
      notifySuccess("Sistema borrado");
      router.push("/dashboard/sistemas");
    } catch (err) {
      notifyError("No se pudo borrar", mensajeError(err));
    }
  }

  function abrirEntorno(env: EntornoSistema | null) {
    const libre = TIPOS.find((k) => !sistema?.environments.some((e) => e.kind === k)) ?? "prod";
    setFe(formDe(env, libre));
    setEntornoModal({ env });
  }

  async function guardarEntorno() {
    if (!entornoModal) return;
    const payload: EntornoIn = {
      kind: fe.kind,
      url: fe.url.trim() || null,
      hosting: fe.hosting.trim() || null,
      domain_expires_at: fe.domain_expires_at || null,
      certificate_expires_at: fe.certificate_expires_at || null,
      secrets_location: fe.secrets_location.trim() || null,
      visible_to_client: fe.visible_to_client,
    };
    setSaving(true);
    try {
      const f = entornoModal.env
        ? await updateSystemEnvironment(entornoModal.env.id, payload)
        : await createSystemEnvironment(id, payload);
      aplicar(f);
      notifySuccess(entornoModal.env ? "Entorno actualizado" : "Entorno añadido");
      setEntornoModal(null);
    } catch (err) {
      notifyError("No se pudo guardar el entorno", mensajeError(err));
    } finally {
      setSaving(false);
    }
  }

  async function quitarEntorno(env: EntornoSistema) {
    const ok = await confirmAction({
      title: `¿Quitar el entorno ${ENTORNO[env.kind].label}?`,
      text: "Los despliegues ya registrados se conservan con su tipo de entorno.",
      confirmText: "Quitar",
    });
    if (!ok) return;
    try {
      aplicar(await deleteSystemEnvironment(env.id));
      notifySuccess("Entorno quitado");
    } catch (err) {
      notifyError("No se pudo quitar", mensajeError(err));
    }
  }

  if (isLoading) return <div className="empty-state">Cargando…</div>;
  if (error || !sistema) {
    return (
      <div className="empty-state">
        No se encontró el sistema. <Link href="/dashboard/sistemas">Volver a Sistemas</Link>
      </div>
    );
  }

  return (
    <section className="page-stack">
      <div className="section-heading">
        <div>
          <Link href="/dashboard/sistemas" className="muted-small" style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
            <ArrowLeft size={13} /> Sistemas
          </Link>
          <h2 style={{ margin: "4px 0 0" }}>{sistema.name}</h2>
          <p className="muted-small" style={{ margin: "4px 0 0" }}>{sistema.client_name ?? `Cliente #${sistema.client_id}`}</p>
        </div>
        {puede && (
          <div className={s.barra}>
            <button className="button button-secondary" type="button" onClick={() => setEditOpen(true)} style={{ gap: 6 }}>
              <Pencil size={13} /> Editar
            </button>
            {sistema.status === "en_construccion" && (
              <button className="button button-ghost" type="button" onClick={borrar} style={{ gap: 6 }}>
                <Trash2 size={13} /> Borrar
              </button>
            )}
          </div>
        )}
      </div>

      <article className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Ficha</p><h3>Datos del sistema</h3></div>
          <div className={s.etiquetas}>
            <span className={`badge ${ESTADO_SISTEMA[sistema.status].cls}`}>{ESTADO_SISTEMA[sistema.status].label}</span>
            {sistema.warranty_expiring && <span className="badge badge-pending">Garantía por vencer</span>}
          </div>
        </div>
        <dl className={s.dl}>
          <dt className="muted-small">Qué hace</dt><dd>{sistema.description || "—"}</dd>
          <dt className="muted-small">Stack</dt><dd>{sistema.stack || "—"}</dd>
          <dt className="muted-small">Plan de soporte</dt><dd>{PLAN_SOPORTE[sistema.support_plan]}</dd>
          <dt className="muted-small">Garantía hasta</dt>
          <dd>
            {fechaCorta(sistema.warranty_until)}
            {sistema.warranty_until && <span className={sistema.warranty_expiring ? s.aviso : "muted-small"}> · {textoVence(sistema.warranty_until)}</span>}
          </dd>
          <dt className="muted-small">Repositorio</dt>
          <dd>
            {sistema.repository_url ? (
              <a href={sistema.repository_url} target="_blank" rel="noreferrer noopener" style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                {sistema.repository_url} <ExternalLink size={12} />
              </a>
            ) : "—"}
          </dd>
          <dt className="muted-small">Proyecto de origen</dt>
          <dd>
            {sistema.origin_project_id
              ? <Link href={`/dashboard/projects/${sistema.origin_project_id}`}>Proyecto #{sistema.origin_project_id}</Link>
              : "—"}
          </dd>
        </dl>
      </article>

      <article className="panel">
        <div className="panel-head">
          <div><p className="eyebrow">Dónde corre</p><h3>Entornos</h3></div>
          {puede && sistema.environments.length < TIPOS.length && (
            <button className="button button-primary" type="button" onClick={() => abrirEntorno(null)} style={{ gap: 6 }}>
              <Plus size={14} /> Añadir entorno
            </button>
          )}
        </div>
        {sistema.environments.length === 0 ? (
          <div className="empty-state">Sin entornos. Añade al menos producción para llevar dominio y certificado.</div>
        ) : (
          <div className={s.entornos}>
            {sistema.environments.map((e) => (
              <div key={e.id} className={s.entorno}>
                <div className={s.etiquetas} style={{ justifyContent: "space-between" }}>
                  <span className={`badge ${ENTORNO[e.kind].cls}`}>{ENTORNO[e.kind].label}</span>
                  {e.visible_to_client === false && <span className="muted-small">Oculto al cliente</span>}
                </div>
                {e.url ? (
                  <a href={e.url} target="_blank" rel="noreferrer noopener" className={s.celda} style={{ overflowWrap: "anywhere" }}>{e.url}</a>
                ) : <span className="muted-small">Sin URL</span>}
                <span className={s.celda}>{e.hosting || "Hosting sin indicar"}</span>
                <span className={e.expiring_soon && e.domain_expires_at ? s.aviso : "muted-small"}>
                  Dominio: {fechaCorta(e.domain_expires_at)}{e.domain_expires_at ? ` · ${textoVence(e.domain_expires_at)}` : ""}
                </span>
                <span className={e.expiring_soon && e.certificate_expires_at ? s.aviso : "muted-small"}>
                  Certificado: {fechaCorta(e.certificate_expires_at)}{e.certificate_expires_at ? ` · ${textoVence(e.certificate_expires_at)}` : ""}
                </span>
                {e.secrets_location && <span className="muted-small">Claves en: {e.secrets_location}</span>}
                {puede && (
                  <div className={s.barra}>
                    <button className="button button-ghost button-sm" type="button" onClick={() => abrirEntorno(e)}>Editar</button>
                    <button className="button button-ghost button-sm" type="button" onClick={() => quitarEntorno(e)}>Quitar</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </article>

      <DesplieguesBoard systemId={id} />

      <Modal isOpen={editOpen} title="Editar sistema" onClose={() => setEditOpen(false)}>
        <FormSistema sistema={sistema} clients={clients} projects={projects} saving={saving} onSubmit={guardar} />
      </Modal>

      <Modal
        isOpen={!!entornoModal}
        title={entornoModal?.env ? `Entorno ${ENTORNO[entornoModal.env.kind].label}` : "Añadir entorno"}
        onClose={() => setEntornoModal(null)}
      >
        <div className="entity-form">
          {!entornoModal?.env && (
            <select value={fe.kind} onChange={(e) => setFe({ ...fe, kind: e.target.value as TipoEntorno })} aria-label="Tipo de entorno">
              {TIPOS.map((k) => (
                <option key={k} value={k} disabled={sistema.environments.some((x) => x.kind === k)}>{ENTORNO[k].label}</option>
              ))}
            </select>
          )}
          <input value={fe.url} onChange={(e) => setFe({ ...fe, url: e.target.value })} placeholder="URL (https://…)" maxLength={500} />
          <input value={fe.hosting} onChange={(e) => setFe({ ...fe, hosting: e.target.value })} placeholder="Hosting (p. ej. Oracle Cloud, Vercel)" maxLength={120} />
          <div className={s.dosColumnas}>
            <label className="muted-small">
              Dominio vence
              <input type="date" value={fe.domain_expires_at} onChange={(e) => setFe({ ...fe, domain_expires_at: e.target.value })} />
            </label>
            <label className="muted-small">
              Certificado vence
              <input type="date" value={fe.certificate_expires_at} onChange={(e) => setFe({ ...fe, certificate_expires_at: e.target.value })} />
            </label>
          </div>
          <input
            value={fe.secrets_location}
            onChange={(e) => setFe({ ...fe, secrets_location: e.target.value })}
            placeholder="Dónde están las claves (nunca las claves)"
            maxLength={300}
          />
          <label className={s.check}>
            <input type="checkbox" checked={fe.visible_to_client} onChange={(e) => setFe({ ...fe, visible_to_client: e.target.checked })} />
            El cliente ve este entorno en su portal
          </label>
          <p className="muted-small" style={{ margin: 0 }}>
            Avisamos 30 días antes de que venzan el dominio o el certificado.
          </p>
          <button className="button button-primary" type="button" disabled={saving} onClick={guardarEntorno}>
            {saving ? "Guardando…" : "Guardar entorno"}
          </button>
        </div>
      </Modal>
    </section>
  );
}
