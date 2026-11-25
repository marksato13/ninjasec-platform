"use client";

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Award, Upload } from "lucide-react";

import {
  createUserCertification,
  getUserCertifications,
  uploadCertificateFile,
  type AreaCert,
  type UserCertificationItem,
} from "@/lib/api";
import { notifyError, notifySuccess } from "@/lib/alerts";
import { QK } from "@/lib/query-keys";
import { EmptyState } from "@/components/ui/empty-state";

import { Credencial } from "./credencial";
import s from "./formacion.module.css";
import { AREAS, AVISO_DIAS, errorDeArchivo } from "./utils";

type Borrador = {
  name: string; issuer: string; credential_id: string; url: string;
  issued_at: string; expires_at: string; area: AreaCert | "";
};
const VACIO: Borrador = { name: "", issuer: "", credential_id: "", url: "", issued_at: "", expires_at: "", area: "" };

function Adjuntar({ cert }: { cert: UserCertificationItem }) {
  const qc = useQueryClient();
  const subir = useMutation({
    mutationFn: (file: File) => uploadCertificateFile(cert.id, file),
    onSuccess: (c) => {
      qc.invalidateQueries({ queryKey: QK.certifications() });
      notifySuccess(
        "Certificado adjuntado",
        c.status === "pending" ? "Queda en validación hasta que el super admin lo revise." : undefined,
      );
    },
    onError: (e) => notifyError("No se pudo adjuntar", e instanceof Error ? e.message : undefined),
  });

  return (
    <label className={`button button-secondary button-sm ${s.fileLabel}`}>
      <Upload size={14} aria-hidden="true" />
      {subir.isPending ? "Subiendo…" : cert.has_file ? "Reemplazar certificado" : "Adjuntar certificado"}
      <input
        type="file"
        accept="application/pdf,image/png,image/jpeg,image/webp"
        disabled={subir.isPending}
        aria-label={`Adjuntar el certificado de ${cert.name}`}
        onChange={(e) => {
          const file = e.target.files?.[0];
          e.target.value = "";
          if (!file) return;
          const error = errorDeArchivo(file);
          if (error) {
            notifyError("Archivo no válido", error);
            return;
          }
          subir.mutate(file);
        }}
      />
    </label>
  );
}

export function MisCertificaciones({ userId }: { userId: number | undefined }) {
  const qc = useQueryClient();
  const [abierto, setAbierto] = useState(false);
  const [b, setB] = useState<Borrador>(VACIO);

  const certs = useQuery({ queryKey: QK.certifications(), queryFn: getUserCertifications });
  const mias = (certs.data ?? []).filter((c) => c.user_id === userId);
  const porVencer = mias.filter(
    (c) => c.effective_status === "approved" && c.days_until_expiry !== null && c.days_until_expiry <= AVISO_DIAS,
  );

  const crear = useMutation({
    mutationFn: () =>
      createUserCertification({
        name: b.name.trim(),
        issuer: b.issuer.trim() || null,
        credential_id: b.credential_id.trim() || null,
        url: b.url.trim() || null,
        issued_at: b.issued_at || null,
        expires_at: b.expires_at || null,
        area: b.area || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QK.certifications() });
      setB(VACIO);
      setAbierto(false);
      notifySuccess("Certificación registrada", "Adjunta el certificado para que se pueda validar.");
    },
    onError: (e) => notifyError("No se pudo registrar", e instanceof Error ? e.message : undefined),
  });

  const enviar = (e: FormEvent) => {
    e.preventDefault();
    if (b.name.trim().length < 2) {
      notifyError("Falta el nombre", "Escribe el nombre de la certificación, por ejemplo «Fortinet NSE 4».");
      return;
    }
    crear.mutate();
  };

  const campo = (k: keyof Borrador) => ({
    value: b[k],
    onChange: (e: { target: { value: string } }) => setB({ ...b, [k]: e.target.value }),
  });

  return (
    <div className="page-stack">
      <article className="panel">
        <div className={s.toolbar}>
          <p className={s.intro}>
            Te preparas donde ofrece el curso el fabricante. Aquí registras el resultado y adjuntas el certificado:
            cuando se valida, el cliente lo ve en los proyectos en los que participas.
          </p>
          {!abierto ? (
            <button type="button" className="button button-primary" onClick={() => setAbierto(true)}>
              Registrar certificación
            </button>
          ) : null}
        </div>

        {abierto ? (
          <form className={s.form} onSubmit={enviar} style={{ marginTop: 16 }}>
            <label>
              Certificación
              <input required minLength={2} maxLength={150} placeholder="Fortinet NSE 4 Network Security Professional" {...campo("name")} />
            </label>
            <label>
              Emisor
              <input maxLength={120} placeholder="Fortinet" {...campo("issuer")} />
            </label>
            <label>
              Área
              <select {...campo("area")}>
                <option value="">Sin indicar</option>
                {AREAS.map((a) => <option key={a.value} value={a.value}>{a.label}</option>)}
              </select>
            </label>
            <label>
              ID de la credencial
              <input maxLength={120} placeholder="Opcional" {...campo("credential_id")} />
            </label>
            <label>
              Fecha de emisión
              <input type="date" {...campo("issued_at")} />
            </label>
            <label>
              Fecha de vencimiento
              <input type="date" {...campo("expires_at")} />
            </label>
            <label className={s.full}>
              Enlace de verificación del emisor
              <input type="url" maxLength={255} placeholder="https://www.credly.com/badges/…" {...campo("url")} />
            </label>
            <div className={s.formActions}>
              <button type="button" className="button button-ghost" onClick={() => { setAbierto(false); setB(VACIO); }}>
                Cancelar
              </button>
              <button type="submit" className="button button-primary" disabled={crear.isPending}>
                {crear.isPending ? "Registrando…" : "Registrar certificación"}
              </button>
            </div>
          </form>
        ) : null}
      </article>

      {porVencer.length > 0 ? (
        <p className="form-error" role="status" style={{ margin: 0 }}>
          {porVencer.length === 1
            ? `«${porVencer[0].name}» vence en ${porVencer[0].days_until_expiry} días. Renuévala y adjunta el certificado nuevo.`
            : `${porVencer.length} certificaciones vencen en los próximos ${AVISO_DIAS} días. Renuévalas y adjunta los certificados nuevos.`}
        </p>
      ) : null}

      {certs.isLoading ? <div className="empty-state">Cargando certificaciones…</div> : null}
      {certs.error ? <p className="form-error">No se pudieron cargar tus certificaciones.</p> : null}

      {!certs.isLoading && !certs.error && mias.length === 0 ? (
        <EmptyState
          icon={Award}
          title="Aún no registras certificaciones"
          description="Registra la primera y adjunta el PDF o la imagen del certificado."
          action={abierto ? undefined : { label: "Registrar certificación", onClick: () => setAbierto(true) }}
        />
      ) : null}

      {mias.length > 0 ? (
        <div className={s.grid}>
          {mias.map((c) => (
            <Credencial key={c.id} cert={c}>
              <div className={s.actions}>
                <Adjuntar cert={c} />
              </div>
            </Credencial>
          ))}
        </div>
      ) : null}
    </div>
  );
}
