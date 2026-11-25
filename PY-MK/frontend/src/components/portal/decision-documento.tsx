"use client";

import { useState } from "react";
import { CheckCircle2, MessageSquareWarning } from "lucide-react";

import { decideProjectDoc, type ProjectDocItem } from "@/lib/api";
import { askReason, confirmApprove, notifyError, notifySuccess } from "@/lib/alerts";

/**
 * C1: aprobación del cliente sobre un documento entregado.
 *
 * El cliente ve "Aprobar" y "Pedir cambios" mientras no lo haya aprobado. El
 * equipo ve solo el estado, con el motivo si pidió cambios. Si el equipo sube
 * una versión nueva, el backend reabre la decisión.
 */
export function DecisionDocumento({
  doc,
  esCliente,
  onDecidido,
}: {
  doc: ProjectDocItem;
  esCliente: boolean;
  onDecidido: () => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const fecha = doc.client_decision_at
    ? new Date(doc.client_decision_at).toLocaleDateString("es-PE", { day: "numeric", month: "short", year: "numeric" })
    : "";

  async function decidir(decision: "approved" | "changes_requested") {
    let nota: string | null = null;
    if (decision === "approved") {
      const ok = await confirmApprove({
        title: "¿Apruebas este documento?",
        text: `«${doc.title}» quedará como aprobado por tu empresa. Si después hace falta un cambio, el equipo subirá una versión nueva.`,
        confirmText: "Aprobar",
      });
      if (!ok) return;
    } else {
      nota = await askReason({
        title: "¿Qué cambios necesitas?",
        text: "El equipo verá tu comentario y subirá una versión corregida.",
        placeholder: "Por ejemplo: falta el diagrama de la sede 2",
        confirmText: "Pedir cambios",
      });
      if (nota === null) return;
    }
    setEnviando(true);
    try {
      await decideProjectDoc(doc.id, decision, nota);
      notifySuccess(decision === "approved" ? "Documento aprobado" : "Pedido de cambios enviado");
      onDecidido();
    } catch (err) {
      notifyError("No se pudo registrar tu decisión", err instanceof Error ? err.message : "");
    } finally {
      setEnviando(false);
    }
  }

  const estado =
    doc.client_decision === "approved" ? (
      <span className="badge badge-active" style={{ gap: 4 }}>
        <CheckCircle2 size={12} aria-hidden="true" /> Aprobado por el cliente{fecha ? ` · ${fecha}` : ""}
      </span>
    ) : doc.client_decision === "changes_requested" ? (
      <span className="badge badge-pending" style={{ gap: 4 }} title={doc.client_decision_note ?? ""}>
        <MessageSquareWarning size={12} aria-hidden="true" /> Cambios pedidos{fecha ? ` · ${fecha}` : ""}
      </span>
    ) : !esCliente ? (
      <span className="badge badge-draft">Sin revisión del cliente</span>
    ) : null;

  return (
    <div style={{ display: "grid", gap: 6 }}>
      {estado && <div>{estado}</div>}
      {doc.client_decision === "changes_requested" && doc.client_decision_note && (
        <p className="doc-summary" style={{ fontSize: "0.78rem", margin: 0 }}>
          «{doc.client_decision_note}»
        </p>
      )}
      {esCliente && doc.client_decision !== "approved" && (
        <div style={{ display: "flex", gap: 8 }}>
          <button className="button button-success button-sm" type="button" disabled={enviando} onClick={() => decidir("approved")}>
            Aprobar
          </button>
          <button className="button button-ghost button-sm" type="button" disabled={enviando} onClick={() => decidir("changes_requested")}>
            Pedir cambios
          </button>
        </div>
      )}
    </div>
  );
}
