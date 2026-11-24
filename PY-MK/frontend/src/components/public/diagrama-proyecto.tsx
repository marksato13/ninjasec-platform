"use client";

import {
  Background,
  Handle,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useMemo } from "react";

import type { AristaDiagrama, Capa, NodoDiagrama } from "@/lib/portafolio";

/**
 * Diagrama de solo lectura de un proyecto del portafolio.
 *
 * No se arrastra ni se conecta: es una ilustración, no un editor. Por eso el
 * lienzo no atrapa la rueda del ratón (no se queda «pegada» al hacer scroll en
 * la página) y cada nodo es alcanzable con el teclado solo si lleva información.
 *
 * El color de cada capa NO es lo único que la distingue: lleva una etiqueta de
 * texto, para que no dependa de ver colores.
 */

const COLOR: Record<Capa, { var: string; texto: string }> = {
  usuario: { var: "var(--warning)", texto: "Usuario" },
  borde: { var: "var(--primary)", texto: "Entrada" },
  aplicacion: { var: "var(--security)", texto: "Aplicación" },
  datos: { var: "var(--success)", texto: "Datos" },
  operacion: { var: "var(--primary-strong)", texto: "Operación" },
  red: { var: "var(--muted)", texto: "Red" },
  externo: { var: "var(--danger)", texto: "Externo" },
};

type DatosNodo = { etiqueta: string; detalle?: string; capa: Capa };

function Nodo({ data }: NodeProps<Node<DatosNodo>>) {
  const c = COLOR[data.capa];
  return (
    <div
      style={{
        minWidth: 150,
        padding: "10px 14px",
        borderRadius: 12,
        background: "var(--panel)",
        border: `1.5px solid ${c.var}`,
        boxShadow: `0 0 0 3px color-mix(in srgb, ${c.var} 14%, transparent)`,
        color: "var(--text)",
        textAlign: "center",
      }}
    >
      <Handle id="l" type="target" position={Position.Left} style={{ opacity: 0 }} isConnectable={false} />
      <Handle id="t" type="target" position={Position.Top} style={{ opacity: 0 }} isConnectable={false} />
      <div style={{ fontSize: 10, letterSpacing: 0.4, color: c.var, fontWeight: 700 }}>{c.texto}</div>
      <div style={{ fontWeight: 700, fontSize: 14 }}>{data.etiqueta}</div>
      {data.detalle && <div style={{ fontSize: 11, color: "var(--muted)" }}>{data.detalle}</div>}
      <Handle id="r" type="source" position={Position.Right} style={{ opacity: 0 }} isConnectable={false} />
      <Handle id="b" type="source" position={Position.Bottom} style={{ opacity: 0 }} isConnectable={false} />
    </div>
  );
}

const TIPOS = { nodo: Nodo };

export function DiagramaProyecto({
  titulo,
  nodos,
  aristas,
  alto = 420,
}: {
  titulo: string;
  nodos: NodoDiagrama[];
  aristas: AristaDiagrama[];
  alto?: number;
}) {
  const nodes: Node<DatosNodo>[] = useMemo(
    () =>
      nodos.map((n) => ({
        id: n.id,
        type: "nodo",
        position: { x: n.x, y: n.y },
        data: { etiqueta: n.etiqueta, detalle: n.detalle, capa: n.capa },
        draggable: false,
        selectable: false,
        focusable: false,
      })),
    [nodos],
  );

  const edges: Edge[] = useMemo(() => {
    const pos = new Map(nodos.map((n) => [n.id, n]));
    return aristas.map((a, i) => {
      // Si los dos nodos estan mas apilados que alineados, la flecha sale por abajo y
      // entra por arriba. Sin esto sale por un lado y entra por el opuesto y da una vuelta.
      const o = pos.get(a.de), d = pos.get(a.a);
      // Baja con claridad (70 px o mas) y no se desplaza demasiado de lado: sale por abajo y
      // entra por arriba. El resto, de lado a lado.
      const dy = o && d ? d.y - o.y : 0;
      const dx = o && d ? Math.abs(d.x - o.x) : 0;
      const vertical = dy >= 70 && dx <= 1.8 * dy;
      return {
        id: `${a.de}-${a.a}-${i}`,
        source: a.de,
        target: a.a,
        sourceHandle: vertical ? "b" : "r",
        targetHandle: vertical ? "t" : "l",
        label: a.etiqueta,
        animated: a.animada ?? false,
        style: { stroke: "var(--line-strong, var(--muted))", strokeWidth: 1.6 },
        labelStyle: { fill: "var(--muted)", fontSize: 11 },
        labelBgStyle: { fill: "var(--bg-soft)" },
        focusable: false,
      };
    });
  }, [aristas, nodos]);

  return (
    <figure style={{ margin: 0 }}>
      <div
        role="img"
        aria-label={`Diagrama: ${titulo}. ${nodos.map((n) => n.etiqueta).join(", ")}.`}
        style={{ height: alto, borderRadius: 14, border: "1px solid var(--line)", background: "var(--bg-soft)" }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={TIPOS}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          zoomOnScroll={false}
          panOnScroll={false}
          preventScrolling={false}
          zoomOnDoubleClick={false}
          panOnDrag={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} size={1} color="var(--line)" />
        </ReactFlow>
      </div>
      <figcaption className="muted-small" style={{ marginTop: 6 }}>
        {titulo}
      </figcaption>
    </figure>
  );
}
