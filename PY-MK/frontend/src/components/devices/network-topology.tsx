"use client";

import { useMemo, useState } from "react";
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
import { Cloud, HelpCircle, Monitor, Network, Radio, Router, Server, Shield, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getTopology, type TopologyNode, type TopologyResponse } from "@/lib/api";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";

type DeviceNodeData = { device: TopologyNode };

const TYPE_RANK: Record<string, number> = { firewall: 0, router: 1, cloud: 1, switch: 2, server: 3, ap: 3, camera: 4, endpoint: 4, other: 4 };
const CRITICALITY_COLOR: Record<string, string> = { low: "#10b981", medium: "#3b82f6", high: "#f59e0b", critical: "#dc2626" };
const LINK_COLOR: Record<string, string> = { ethernet: "#64748b", wifi: "#8b5cf6", wan: "#0ea5e9", vpn: "#f59e0b", mpls: "#ec4899", trunk: "#14b8a6", cloud_peering: "#6366f1" };

function DeviceIcon({ type }: { type?: string | null }) {
  const Icon = type === "firewall" ? Shield : type === "router" ? Router : type === "switch" ? Network : type === "server" ? Server : type === "ap" ? Radio : type === "endpoint" ? Monitor : type === "cloud" ? Cloud : HelpCircle;
  return <Icon size={18} aria-hidden="true" />;
}

function DeviceNode({ data }: NodeProps<Node<DeviceNodeData>>) {
  const device = data.device;
  const color = CRITICALITY_COLOR[device.criticality || ""] || "#94a3b8";
  return (
    <div className="topology-device-node" style={{ borderColor: color }}>
      <Handle type="target" position={Position.Top} />
      <span className="topology-device-icon"><DeviceIcon type={device.device_type} /></span>
      <span><strong>{device.label}</strong><small>{device.device_type || "otro"} · {device.status}</small></span>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

function bandwidthWidth(value?: number | null) {
  if (!value) return 1.5;
  return Math.min(7, 1.5 + Math.log10(Math.max(1, value)));
}

function dashFor(type: string) {
  if (type === "trunk") return "2 5";
  if (type === "vpn" || type === "wifi") return "8 5";
  return undefined;
}

function buildFlow(topology: TopologyResponse) {
  const nodes: Node<DeviceNodeData>[] = [];
  const clusters = topology.clusters.length ? topology.clusters : [{ label: "Sin sede", site_id: null, node_ids: topology.nodes.map((node) => node.id) }];
  let offsetX = 0;

  clusters.forEach((cluster, clusterIndex) => {
    const devices = topology.nodes.filter((device) => cluster.node_ids.includes(device.id));
    const ranks = devices.map((device) => TYPE_RANK[device.device_type || "other"] ?? 4);
    const maxAtRank = Math.max(1, ...ranks.map((rank) => ranks.filter((item) => item === rank).length));
    const clusterWidth = Math.max(360, maxAtRank * 220 + 80);
    const maxRank = Math.max(0, ...ranks);
    const parentId = `site-${cluster.site_id ?? `none-${clusterIndex}`}`;

    nodes.push({
      id: parentId,
      type: "group",
      data: { device: { id: -1, label: cluster.label, status: "" } },
      position: { x: offsetX, y: 0 },
      style: { width: clusterWidth, height: Math.max(360, (maxRank + 1) * 140 + 90) },
      className: "topology-site-node",
      selectable: false,
    });

    const rankIndexes = new Map<number, number>();
    devices.sort((a, b) => (TYPE_RANK[a.device_type || "other"] ?? 4) - (TYPE_RANK[b.device_type || "other"] ?? 4)).forEach((device) => {
      const rank = TYPE_RANK[device.device_type || "other"] ?? 4;
      const index = rankIndexes.get(rank) || 0;
      rankIndexes.set(rank, index + 1);
      const count = ranks.filter((item) => item === rank).length;
      nodes.push({
        id: String(device.id),
        type: "device",
        parentId,
        extent: "parent",
        data: { device },
        position: { x: (clusterWidth - count * 190) / 2 + index * 190, y: 55 + rank * 130 },
      });
    });
    offsetX += clusterWidth + 60;
  });

  const edges: Edge[] = topology.edges.map((edge) => ({
    id: String(edge.id),
    source: String(edge.source),
    target: String(edge.target),
    label: edge.bandwidth_mbps ? `${edge.link_type} · ${edge.bandwidth_mbps} Mbps` : edge.link_type,
    type: "smoothstep",
    style: { stroke: LINK_COLOR[edge.link_type], strokeWidth: bandwidthWidth(edge.bandwidth_mbps), strokeDasharray: dashFor(edge.link_type) },
    labelStyle: { fill: "var(--text)", fontSize: 10, fontWeight: 600 },
    labelBgStyle: { fill: "var(--surface)", fillOpacity: 0.92 },
  }));
  return { nodes, edges };
}

export function NetworkTopology({ clientId }: { clientId?: number }) {
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const isClient = getStoredUser()?.role === "client";
  const { data, isLoading, isError } = useQuery({
    queryKey: clientId ? QK.topology(clientId) : ["topology", "none"],
    queryFn: () => getTopology(clientId!),
    enabled: Boolean(clientId),
  });
  const flow = useMemo(() => data ? buildFlow(data) : { nodes: [], edges: [] }, [data]);

  if (!clientId) return <div className="empty-state">Selecciona un cliente para visualizar su topología.</div>;
  if (isLoading) return <div className="state-panel">Cargando topología…</div>;
  if (isError) return <div className="empty-state">No se pudo cargar la topología del cliente.</div>;
  if (!data?.nodes.length || !data.edges.length) return <div className="empty-state"><strong>Topología aún no declarada.</strong><br />Este cliente necesita al menos dos activos y una conexión registrada.</div>;

  return (
    <div className="topology-shell">
      <div className="topology-canvas" aria-label={`Topología de ${data.client_name || "cliente"}`}>
        <ReactFlow
          nodes={flow.nodes}
          edges={flow.edges}
          nodeTypes={{ device: DeviceNode }}
          nodesDraggable={false}
          nodesConnectable={false}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.25}
          onNodeClick={(_, node) => { if (node.type === "device") setSelected((node.data as DeviceNodeData).device); }}
        >
          <Background gap={22} size={1} />
          <MiniMap pannable zoomable nodeColor={(node) => node.type === "group" ? "#334155" : CRITICALITY_COLOR[(node.data as DeviceNodeData).device?.criticality || ""] || "#94a3b8"} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      {selected && (
        <aside className="topology-detail" aria-label="Ficha del activo">
          <button className="topology-detail-close" type="button" onClick={() => setSelected(null)} aria-label="Cerrar ficha"><X size={18} /></button>
          <div className="topology-detail-title"><span className="topology-device-icon"><DeviceIcon type={selected.device_type} /></span><div><small>Activo seleccionado</small><h3>{selected.label}</h3></div></div>
          <dl>
            <div><dt>Tipo</dt><dd>{selected.device_type || "Otro"}</dd></div>
            <div><dt>Estado</dt><dd>{selected.status}</dd></div>
            <div><dt>Criticidad</dt><dd>{selected.criticality || "Sin clasificar"}</dd></div>
            <div><dt>Fabricante</dt><dd>{[selected.vendor, selected.model].filter(Boolean).join(" · ") || "—"}</dd></div>
            <div><dt>Responsable</dt><dd>{selected.responsible_user_name || "—"}</dd></div>
            {!isClient && <div><dt>Dirección IP</dt><dd>{selected.ip_address || "—"}</dd></div>}
          </dl>
          {isClient && <p className="topology-privacy-note">La vista de cliente oculta direcciones IP y detalles de puertos.</p>}
        </aside>
      )}
    </div>
  );
}
