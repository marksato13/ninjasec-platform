"use client";

import { ExternalLink, FileCheck2, Paperclip } from "lucide-react";
import type { ReactNode } from "react";

import type { UserCertificationItem } from "@/lib/api";

import s from "./formacion.module.css";
import { areaLabel, estadoCertificacion, fecha } from "./utils";

type Props = {
  cert: UserCertificationItem;
  /** Nombre de la persona, cuando la tarjeta se ve fuera de "mis certificaciones". */
  persona?: string;
  children?: ReactNode;
};

/** Una certificacion como credencial: riel de estado, emisor, fechas y adjunto. */
export function Credencial({ cert, persona, children }: Props) {
  const estado = estadoCertificacion(cert);
  const area = areaLabel(cert.area);
  return (
    <article className={`${s.cred} ${s[estado.tono]}`} aria-label={`${cert.name}: ${estado.texto}`}>
      <div className={s.credHead}>
        <div>
          <h4 className={s.credName}>{cert.name}</h4>
          <p className={s.issuer}>
            {persona ? `${persona} · ` : ""}
            {cert.issuer || "Emisor sin indicar"}
          </p>
        </div>
        <span className={`${s.estado} ${s[estado.tono]}`}>{estado.texto}</span>
      </div>

      <dl className={s.meta}>
        <div><dt>Emitida</dt><dd>{fecha(cert.issued_at)}</dd></div>
        <div><dt>Vence</dt><dd>{cert.expires_at ? fecha(cert.expires_at) : "No vence"}</dd></div>
        {cert.credential_id ? <div><dt>ID</dt><dd>{cert.credential_id}</dd></div> : null}
      </dl>

      <div className={s.actions}>
        {area ? <span className={`${s.area} ${s[`area-${cert.area}`]}`}>{area}</span> : null}
        <span className={s.area}>
          {cert.has_file ? (
            <><FileCheck2 size={14} aria-hidden="true" /> {cert.file_name}</>
          ) : (
            <><Paperclip size={14} aria-hidden="true" /> Sin certificado adjunto</>
          )}
        </span>
        {cert.url ? (
          <a className={s.area} href={cert.url} target="_blank" rel="noopener noreferrer">
            <ExternalLink size={14} aria-hidden="true" /> Verificar en el emisor
          </a>
        ) : null}
      </div>

      {cert.effective_status === "rejected" && cert.rejection_reason ? (
        <p className={s.motivo}>Motivo del rechazo: {cert.rejection_reason}</p>
      ) : null}

      {children}
    </article>
  );
}
