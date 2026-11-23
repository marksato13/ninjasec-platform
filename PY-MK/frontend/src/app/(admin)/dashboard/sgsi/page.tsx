"use client";

import { MapaGuiaSgsi } from "@/components/sgsi/mapa-guia";

export default function PaginaGuiaSgsi() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header>
        <h1 style={{ margin: 0, fontSize: 22, color: "var(--text)" }}>
          Guía del SGSI
        </h1>
        <p style={{ margin: "6px 0 0", fontSize: 13.5, color: "var(--muted)", maxWidth: 760 }}>
          Cómo se construye la documentación de un sistema de gestión de seguridad de la
          información, qué herramienta cubre cada paso y dónde están las plantillas.
        </p>
      </header>

      <div
        style={{
          padding: "12px 16px",
          borderRadius: 12,
          border: "1px solid var(--line)",
          background: "var(--primary-soft)",
          fontSize: 12.5,
          color: "var(--muted)",
          lineHeight: 1.6,
        }}
      >
        <strong style={{ color: "var(--text)" }}>Lo que ya existe, se referencia.</strong>{" "}
        Hay plataformas de código abierto que gestionan activos, riesgos y evidencias mejor de lo
        que construiríamos — están señaladas en el mapa y se enlaza a ellas. Lo propio es la capa
        de entregables: plantillas en español y generación del expediente con la marca de la
        consultora.
      </div>

      <MapaGuiaSgsi />
    </div>
  );
}
