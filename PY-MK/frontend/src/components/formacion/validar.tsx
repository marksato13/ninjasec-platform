"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCheck, ExternalLink, FileText } from "lucide-react";

import {
  getCertificateFileUrl,
  getTeamMatrix,
  getUserCertifications,
  getUserSkills,
  verifyUserCertification,
  verifyUserSkill,
  type UserCertificationItem,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { EmptyState } from "@/components/ui/empty-state";
import { ConMarca } from "@/components/ui/marca-icono";

import { Credencial } from "./credencial";
import s from "./formacion.module.css";
import { Nivel } from "./mis-skills";

type Vista = { certId: number; url: string; type: string };

/** Rechazar siempre pide motivo: es lo que lee la persona para corregir. */
function Decision({
  pendiente,
  onAprobar,
  onRechazar,
}: {
  pendiente: boolean;
  onAprobar: () => void;
  onRechazar: (motivo: string) => void;
}) {
  const [rechazando, setRechazando] = useState(false);
  const [motivo, setMotivo] = useState("");
  if (rechazando) {
    return (
      <div className={s.rechazo}>
        <label className="muted-small" style={{ display: "grid", gap: 6 }}>
          Motivo del rechazo
          <textarea
            value={motivo}
            maxLength={500}
            onChange={(e) => setMotivo(e.target.value)}
            placeholder="El certificado está ilegible; súbelo en PDF."
          />
        </label>
        <div className={s.actions}>
          <button type="button" className="button button-ghost button-sm" onClick={() => { setRechazando(false); setMotivo(""); }}>
            Cancelar
          </button>
          <button
            type="button"
            className="button button-danger button-sm"
            disabled={pendiente || motivo.trim().length < 3}
            onClick={() => onRechazar(motivo.trim())}
          >
            Rechazar
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className={s.actions}>
      <button type="button" className="button button-success button-sm" disabled={pendiente} onClick={onAprobar}>
        Validar
      </button>
      <button type="button" className="button button-ghost button-sm" disabled={pendiente} onClick={() => setRechazando(true)}>
        Rechazar…
      </button>
    </div>
  );
}

export function Validar({ puedeValidar }: { puedeValidar: boolean }) {
  const qc = useQueryClient();
  const [vista, setVista] = useState<Vista | null>(null);
  const [abriendo, setAbriendo] = useState<number | null>(null);

  const certs = useQuery({ queryKey: QK.certifications(), queryFn: getUserCertifications });
  const skills = useQuery({ queryKey: QK.userSkills(), queryFn: getUserSkills });
  const equipo = useQuery({ queryKey: QK.teamMatrix(), queryFn: getTeamMatrix });
  const nombres = new Map((equipo.data ?? []).map((f) => [f.user_id, f.full_name]));

  const pendientesCert = (certs.data ?? []).filter((c) => c.status === "pending");
  const pendientesSkill = (skills.data ?? []).filter((k) => k.status === "pending");

  const refrescar = () => {
    qc.invalidateQueries({ queryKey: ["certifications"] });
    qc.invalidateQueries({ queryKey: QK.userSkills() });
    qc.invalidateQueries({ queryKey: QK.pendingApprovals() });
  };
  const alFallar = (e: unknown) => notifyError("No se pudo guardar la decisión", e instanceof Error ? e.message : undefined);

  const decidirCert = useMutation({
    mutationFn: (v: { id: number; status: "approved" | "rejected"; motivo?: string }) =>
      verifyUserCertification(v.id, v.status, v.motivo),
    onSuccess: (c) => {
      refrescar();
      if (vista?.certId === c.id) cerrarVista();
      notifySuccess(c.status === "approved" ? "Certificación validada" : "Certificación rechazada");
    },
    onError: alFallar,
  });
  const decidirSkill = useMutation({
    mutationFn: (v: { id: number; status: "approved" | "rejected"; motivo?: string }) =>
      verifyUserSkill(v.id, v.status, v.motivo),
    onSuccess: (k) => {
      refrescar();
      notifySuccess(k.status === "approved" ? "Skill validada" : "Skill rechazada");
    },
    onError: alFallar,
  });

  function cerrarVista() {
    setVista((actual) => {
      if (actual) URL.revokeObjectURL(actual.url);
      return null;
    });
  }

  async function verArchivo(c: UserCertificationItem) {
    setAbriendo(c.id);
    try {
      const archivo = await getCertificateFileUrl(c.id);
      if (archivo.type === "application/pdf") {
        // El PDF se abre en otra pestaña: la CSP no deja incrustar blobs en un iframe.
        window.open(archivo.url, "_blank", "noopener");
        setTimeout(() => URL.revokeObjectURL(archivo.url), 60_000);
      } else {
        cerrarVista();
        setVista({ certId: c.id, url: archivo.url, type: archivo.type });
      }
    } catch (e) {
      notifyError("No se pudo abrir el certificado", e instanceof Error ? e.message : undefined);
    } finally {
      setAbriendo(null);
    }
  }

  if (certs.isLoading || skills.isLoading) return <div className="empty-state">Cargando pendientes…</div>;

  return (
    <div className="page-stack">
      {!puedeValidar ? (
        <p className="muted-small" style={{ margin: 0 }}>
          Puedes revisar lo pendiente; validar o rechazar lo hace el super admin.
        </p>
      ) : null}

      <article className="panel">
        <div className="panel-head">
          <div>
            <h3>Certificaciones por validar</h3>
            <p className="muted-small" style={{ margin: 0 }}>
              Abre el certificado, compáralo con el enlace del emisor y decide.
            </p>
          </div>
          <span className="badge badge-pending">{pendientesCert.length}</span>
        </div>

        {pendientesCert.length === 0 ? (
          <EmptyState icon={CheckCheck} title="No hay certificaciones pendientes" />
        ) : (
          <div className="page-stack">
            {pendientesCert.map((c) => (
              <div key={c.id} className={s.revision}>
                <Credencial cert={c} persona={nombres.get(c.user_id) ?? `Persona #${c.user_id}`}>
                  <div className={s.actions}>
                    {c.has_file ? (
                      <button
                        type="button"
                        className="button button-secondary button-sm"
                        disabled={abriendo === c.id}
                        onClick={() => verArchivo(c)}
                      >
                        <FileText size={14} aria-hidden="true" />
                        {abriendo === c.id ? "Abriendo…" : "Ver certificado"}
                      </button>
                    ) : null}
                    {c.url ? (
                      <a className="button button-ghost button-sm" href={c.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink size={14} aria-hidden="true" /> Verificar en el emisor
                      </a>
                    ) : null}
                  </div>
                  {puedeValidar ? (
                    <Decision
                      pendiente={decidirCert.isPending}
                      onAprobar={() => decidirCert.mutate({ id: c.id, status: "approved" })}
                      onRechazar={(motivo) => decidirCert.mutate({ id: c.id, status: "rejected", motivo })}
                    />
                  ) : null}
                </Credencial>
                <div className={s.preview} aria-live="polite">
                  {vista?.certId === c.id ? (
                    // eslint-disable-next-line @next/next/no-img-element -- blob local, sin optimizacion posible
                    <img src={vista.url} alt={`Certificado ${c.name}`} />
                  ) : c.has_file ? (
                    "Pulsa «Ver certificado». Las imágenes se muestran aquí; los PDF se abren en otra pestaña."
                  ) : (
                    "Sin certificado adjunto. Valida solo si el enlace del emisor lo confirma."
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </article>

      <article className="panel">
        <div className="panel-head">
          <div>
            <h3>Skills por validar</h3>
          </div>
          <span className="badge badge-pending">{pendientesSkill.length}</span>
        </div>
        {pendientesSkill.length === 0 ? (
          <EmptyState icon={CheckCheck} title="No hay skills pendientes" />
        ) : (
          <div className={s.skills}>
            {pendientesSkill.map((k) => (
              <div key={k.id} className={s.skill} style={{ gridTemplateColumns: "minmax(0,1.4fr) auto minmax(0,1.4fr)" }}>
                <div>
                  <strong><ConMarca nombre={k.skill_name ?? `Skill #${k.skill_id}`} /></strong>
                  <p className="muted-small" style={{ margin: "2px 0 0" }}>{nombres.get(k.user_id) ?? `Persona #${k.user_id}`}</p>
                </div>
                <Nivel valor={k.level} />
                {puedeValidar ? (
                  <Decision
                    pendiente={decidirSkill.isPending}
                    onAprobar={() => decidirSkill.mutate({ id: k.id, status: "approved" })}
                    onRechazar={(motivo) => decidirSkill.mutate({ id: k.id, status: "rejected", motivo })}
                  />
                ) : <span />}
              </div>
            ))}
          </div>
        )}
      </article>
    </div>
  );
}
