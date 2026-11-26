"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

import { toggleProjectDoc, type ProjectDocItem } from "@/lib/api";
import { notifyError } from "@/lib/alerts";
import { getDocVisibilityLabel } from "@/lib/role-utils";
import { DecisionDocumento } from "@/components/portal/decision-documento";

/**
 * Lo que el equipo controla de un documento dentro de su proyecto: quién lo
 * ve, si está habilitado y qué decidió el cliente.
 *
 * Antes vivía suelto en "Aprobaciones", lejos del proyecto al que pertenece.
 */
export function ControlDocumento({ doc, onCambio }: { doc: ProjectDocItem; onCambio: () => void }) {
  const [enviando, setEnviando] = useState(false);

  async function alternar() {
    setEnviando(true);
    try {
      await toggleProjectDoc(doc.id, !doc.enabled);
      onCambio();
    } catch (err) {
      notifyError("No se pudo cambiar el documento", err instanceof Error ? err.message : "");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, alignItems: "center" }}>
        <span className="badge badge-info">{getDocVisibilityLabel(doc.visibility)}</span>
        {!doc.enabled && <span className="badge badge-rejected">Deshabilitado</span>}
      </div>
      <DecisionDocumento doc={doc} esCliente={false} onDecidido={onCambio} />
      <div>
        <button className="button button-ghost button-sm" type="button" disabled={enviando} onClick={alternar}
          style={{ gap: 5 }}>
          {doc.enabled ? <><EyeOff size={13} aria-hidden="true" /> Deshabilitar</> : <><Eye size={13} aria-hidden="true" /> Habilitar</>}
        </button>
      </div>
    </div>
  );
}
