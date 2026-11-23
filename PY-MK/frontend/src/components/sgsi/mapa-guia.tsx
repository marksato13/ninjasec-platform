"use client";

/**
 * Mapa guía del SGSI.
 *
 * Dibuja el recorrido de la documentación y qué herramienta cubre cada paso.
 * Todo el contenido vive en `lib/sgsi/guia-datos.ts`: este componente no sabe
 * nada de ISO 27001, solo de cómo pintar nodos, aristas y un panel de
 * detalle. Para adaptarlo a otro proceso basta con cambiar los datos.
 */

import { useCallback, useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ExternalLink, Info, X } from "lucide-react";

import {
  CAPAS,
  ORIGEN_ETIQUETA,
  VISTAS,
  type Capa,
  type NodoGuia,
  type Origen,
} from "@/lib/sgsi/guia-datos";

const COLOR_CAPA: Record<Capa, string> = {
  entrada: "var(--warning)",
  registro: "var(--primary)",
  generacion: "var(--security)",
  entrega: "var(--success)",
};

const COLOR_ORIGEN: Record<Origen, string> = {
  propio: "var(--security)",
  abierto: "var(--primary)",
  comercial: "var(--danger)",
  manual: "var(--warning)",
};

/** Orden vertical de las capas en el lienzo. */
const ORDEN_CAPA: Capa[] = ["entrada", "registro", "generacion", "entrega"];

type DatosNodo = { guia: NodoGuia; seleccionado: boolean };

function NodoMapa({ data }: NodeProps) {
  const { guia, seleccionado } = data as unknown as DatosNodo;
  const color = COLOR_CAPA[guia.capa];

  return (
    <div
      style={{
        minWidth: 190,
        maxWidth: 230,
        padding: "12px 14px",
        borderRadius: 12,
        background: "var(--panel)",
        border: `1px solid ${seleccionado ? color : "var(--line)"}`,
        boxShadow: seleccionado ? `0 0 0 2px ${color}44` : "var(--shadow-card)",
        cursor: "pointer",
        transition: "border-color .15s, box-shadow .15s",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>
        <span
          aria-hidden
          style={{ width: 7, height: 7, borderRadius: 99, background: color, flexShrink: 0 }}
        />
        <strong style={{ fontSize: 13, color: "var(--text)", lineHeight: 1.25 }}>
          {guia.titulo}
        </strong>
      </div>
      <p style={{ fontSize: 11.5, color: "var(--muted)", margin: 0, lineHeight: 1.4 }}>
        {guia.resumen}
      </p>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

const TIPOS_NODO = { guia: NodoMapa };

export function MapaGuiaSgsi() {
  const [vistaId, setVistaId] = useState(VISTAS[0].id);
  const [activo, setActivo] = useState<NodoGuia | null>(null);

  const vista = useMemo(
    () => VISTAS.find((v) => v.id === vistaId) ?? VISTAS[0],
    [vistaId],
  );

  const { nodes, edges } = useMemo(() => {
    // Se reparten por capa: eje Y según la capa, eje X según el orden dentro
    // de ella. Así el dibujo se lee de arriba abajo como el proceso real.
    const porCapa = new Map<Capa, NodoGuia[]>();
    for (const n of vista.nodos) {
      porCapa.set(n.capa, [...(porCapa.get(n.capa) ?? []), n]);
    }

    const nodos: Node[] = [];
    ORDEN_CAPA.forEach((capa, fila) => {
      const enCapa = porCapa.get(capa) ?? [];
      enCapa.forEach((guia, columna) => {
        nodos.push({
          id: guia.id,
          type: "guia",
          position: { x: columna * 270, y: fila * 165 },
          data: { guia, seleccionado: activo?.id === guia.id },
        });
      });
    });

    const aristas: Edge[] = vista.aristas.map((a) => ({
      id: `${a.desde}-${a.hacia}`,
      source: a.desde,
      target: a.hacia,
      label: a.etiqueta,
      animated: true,
      style: { stroke: "var(--line-active)", strokeWidth: 1.5 },
      labelStyle: { fill: "var(--muted)", fontSize: 10 },
      labelBgStyle: { fill: "var(--bg-soft)" },
    }));

    return { nodes: nodos, edges: aristas };
  }, [vista, activo]);

  const alPulsarNodo = useCallback(
    (_: unknown, nodo: Node) => {
      const guia = vista.nodos.find((n) => n.id === nodo.id) ?? null;
      setActivo((previo) => (previo?.id === guia?.id ? null : guia));
    },
    [vista],
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Pestañas de vista */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        {VISTAS.map((v) => (
          <button
            key={v.id}
            type="button"
            onClick={() => {
              setVistaId(v.id);
              setActivo(null);
            }}
            className={v.id === vistaId ? "button button-primary" : "button button-ghost"}
            style={{ fontSize: 13 }}
          >
            {v.titulo}
          </button>
        ))}
        <span style={{ fontSize: 12, color: "var(--muted)", marginLeft: 4 }}>
          {vista.proposito}
        </span>
      </div>

      {/* Leyenda de capas */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        {ORDEN_CAPA.map((capa) => (
          <span
            key={capa}
            title={CAPAS[capa].descripcion}
            style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5, color: "var(--muted)" }}
          >
            <span
              aria-hidden
              style={{ width: 7, height: 7, borderRadius: 99, background: COLOR_CAPA[capa] }}
            />
            {CAPAS[capa].titulo}
          </span>
        ))}
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "stretch" }}>
        {/* Lienzo */}
        <div
          style={{
            flex: 1,
            height: 520,
            borderRadius: 14,
            border: "1px solid var(--line)",
            overflow: "hidden",
            background: "var(--bg-soft)",
          }}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={TIPOS_NODO}
            onNodeClick={alPulsarNodo}
            fitView
            fitViewOptions={{ padding: 0.18 }}
            proOptions={{ hideAttribution: false }}
            nodesDraggable={false}
            nodesConnectable={false}
          >
            <Background gap={18} size={1} color="var(--line)" />
            <Controls showInteractive={false} />
            <MiniMap pannable zoomable style={{ background: "var(--panel)" }} />
          </ReactFlow>
        </div>

        {/* Panel de detalle */}
        {activo && (
          <aside
            style={{
              width: 350,
              flexShrink: 0,
              padding: 18,
              borderRadius: 14,
              border: "1px solid var(--line)",
              background: "var(--panel)",
              overflowY: "auto",
              maxHeight: 520,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 15, color: "var(--text)" }}>{activo.titulo}</h3>
              <button
                type="button"
                onClick={() => setActivo(null)}
                aria-label="Cerrar detalle"
                className="button button-ghost"
                style={{ padding: 4, lineHeight: 0 }}
              >
                <X size={15} />
              </button>
            </div>

            <span
              style={{
                display: "inline-block",
                marginTop: 8,
                padding: "2px 8px",
                borderRadius: 99,
                fontSize: 10.5,
                background: `${COLOR_CAPA[activo.capa]}1f`,
                color: COLOR_CAPA[activo.capa],
              }}
            >
              {CAPAS[activo.capa].titulo}
            </span>

            {activo.detalle.split("\n\n").map((parrafo, i) => (
              <p
                key={i}
                style={{ fontSize: 12.5, color: "var(--muted)", lineHeight: 1.6, marginTop: 10 }}
              >
                {parrafo}
              </p>
            ))}

            {activo.norma && (
              <p style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 12, display: "flex", gap: 6 }}>
                <Info size={13} style={{ flexShrink: 0, marginTop: 2 }} />
                {activo.norma}
              </p>
            )}

            {activo.entregables && activo.entregables.length > 0 && (
              <>
                <h4 style={{ fontSize: 12, color: "var(--text)", marginTop: 16, marginBottom: 6 }}>
                  Qué sale de aquí
                </h4>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--muted)" }}>
                  {activo.entregables.map((e) => (
                    <li key={e} style={{ marginBottom: 3 }}>{e}</li>
                  ))}
                </ul>
              </>
            )}

            <h4 style={{ fontSize: 12, color: "var(--text)", marginTop: 16, marginBottom: 8 }}>
              Con qué se hace
            </h4>
            {activo.herramientas.map((h) => (
              <div
                key={h.nombre}
                style={{
                  padding: 10,
                  borderRadius: 10,
                  border: "1px solid var(--line)",
                  marginBottom: 8,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                  <strong style={{ fontSize: 12.5, color: "var(--text)" }}>{h.nombre}</strong>
                  <span
                    style={{
                      padding: "1px 7px",
                      borderRadius: 99,
                      fontSize: 10,
                      background: `${COLOR_ORIGEN[h.origen]}1f`,
                      color: COLOR_ORIGEN[h.origen],
                    }}
                  >
                    {ORIGEN_ETIQUETA[h.origen]}
                  </span>
                  {h.url && (
                    <a
                      href={h.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "var(--primary)", lineHeight: 0 }}
                      aria-label={`Abrir ${h.nombre}`}
                    >
                      <ExternalLink size={12} />
                    </a>
                  )}
                </div>
                <p style={{ fontSize: 11.5, color: "var(--muted)", margin: "6px 0 0", lineHeight: 1.5 }}>
                  {h.papel}
                </p>
                {h.limite && (
                  <p
                    style={{
                      fontSize: 11,
                      color: "var(--warning)",
                      margin: "6px 0 0",
                      lineHeight: 1.5,
                    }}
                  >
                    ⚠ {h.limite}
                  </p>
                )}
              </div>
            ))}
          </aside>
        )}
      </div>

      {!activo && (
        <p style={{ fontSize: 12, color: "var(--muted)", margin: 0 }}>
          Pulsa cualquier paso para ver qué produce, con qué herramienta y qué cláusula de la
          norma lo respalda.
        </p>
      )}
    </div>
  );
}
