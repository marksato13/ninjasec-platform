"use client";

import { useMemo, useState } from "react";
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Cloud, HelpCircle, Monitor, Network, Plus, Radio, Router, Server, Shield, X } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createConnection,
  deleteConnection,
  getTopology,
  type LinkType,
  type TopologyNode,
  type TopologyResponse,
} from "@/lib/api";
import { confirmDelete, notifyError, notifySuccess } from "@/lib/alerts";
import { getStoredUser } from "@/lib/auth";
import { QK } from "@/lib/query-keys";
import { Modal } from "@/components/ui/modal";

const LINK_TYPES: LinkType[] = ["ethernet", "wifi", "wan", "vpn", "mpls", "trunk", "cloud_peering"];
const EDITOR_ROLES = new Set(["super_admin", "admin", "collaborator"]);

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

type PendingConnection = { source: string; target: string };

export function NetworkTopology({ clientId }: { clientId?: number }) {
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const [pendingConnection, setPendingConnection] = useState<PendingConnection | null>(null);
  const [linkForm, setLinkForm] = useState({ link_type: "ethernet" as LinkType, port_source: "", port_target: "", vlan_id: "" });
  const [saving, setSaving] = useState(false);
  const role = getStoredUser()?.role ?? "";
  const isClient = role === "client";
  const canEdit = EDITOR_ROLES.has(role);
  const queryClient = useQueryClient();
  const { data, isLoading, isError } = useQuery({
    queryKey: clientId ? QK.topology(clientId) : ["topology", "none"],
    queryFn: () => getTopology(clientId!),
    enabled: Boolean(clientId),
  });
  const flow = useMemo(() => data ? buildFlow(data) : { nodes: [], edges: [] }, [data]);

  function closeConnectionModal() {
    setPendingConnection(null);
    setLinkForm({ link_type: "ethernet", port_source: "", port_target: "", vlan_id: "" });
  }

  async function handleConnect(connection: Connection | PendingConnection) {
    if (!connection.source || !connection.target) return;
    if (connection.source === connection.target) {
      notifyError("No se puede enlazar un dispositivo consigo mismo");
      return;
    }
    setPendingConnection({ source: connection.source, target: connection.target });
  }

  async function handleCreateConnection() {
    if (!pendingConnection) return;
    setSaving(true);
    try {
      await createConnection({
        source_device_id: Number(pendingConnection.source),
        target_device_id: Number(pendingConnection.target),
        link_type: linkForm.link_type,
        port_source: linkForm.port_source || null,
        port_target: linkForm.port_target || null,
        vlan_id: linkForm.vlan_id ? Number(linkForm.vlan_id) : null,
      });
      notifySuccess("Conexión creada");
      if (clientId) queryClient.invalidateQueries({ queryKey: QK.topology(clientId) });
      closeConnectionModal();
    } catch (err) {
      notifyError("No se pudo crear la conexión", err instanceof Error ? err.message : undefined);
    } finally {
      setSaving(false);
    }
  }

  async function handleEdgeClick(_: unknown, edge: Edge) {
    if (!canEdit) return;
    const ok = await confirmDelete({
      title: "¿Eliminar esta conexión?",
      text: "El enlace se borra del diagrama de topología y no se puede deshacer.",
    });
    if (!ok) return;
    try {
      await deleteConnection(Number(edge.id));
      notifySuccess("Conexión eliminada");
      if (clientId) queryClient.invalidateQueries({ queryKey: QK.topology(clientId) });
    } catch (err) {
      notifyError("No se pudo eliminar la conexión", err instanceof Error ? err.message : undefined);
    }
  }

  if (!clientId) return <div className="empty-state">Selecciona un cliente para visualizar su topología.</div>;
  if (isLoading) return <div className="state-panel">Cargando topología…</div>;
  if (isError) return <div className="empty-state">No se pudo cargar la topología del cliente.</div>;
  if (!data?.nodes.length) return <div className="empty-state"><strong>Topología aún no declarada.</strong><br />Este cliente necesita al menos dos activos registrados.</div>;
  if (!data.edges.length && !canEdit) return <div className="empty-state"><strong>Topología aún no declarada.</strong><br />Este cliente todavía no tiene conexiones registradas.</div>;

  const devices = data.nodes;

  return (
    <div className="topology-shell">
      {canEdit && (
        <div className="panel-actions" style={{ marginBottom: 8 }}>
          <button
            type="button"
            className="button button-primary button-sm"
            onClick={() => devices.length >= 2 && setPendingConnection({ source: String(devices[0].id), target: String(devices[1].id) })}
            disabled={devices.length < 2}
          >
            <Plus size={14} /> Nueva conexión
          </button>
          <span className="muted-small">O arrastra desde el borde de un nodo hasta otro en el diagrama.</span>
        </div>
      )}
      {!data.edges.length && (
        <div className="empty-state">Sin conexiones todavía -- crea la primera con el botón de arriba o arrastrando entre nodos.</div>
      )}
      <div className="topology-canvas" aria-label={`Topología de ${data.client_name || "cliente"}`}>
        <ReactFlow
          nodes={flow.nodes}
          edges={flow.edges}
          nodeTypes={{ device: DeviceNode }}
          nodesDraggable={false}
          nodesConnectable={canEdit}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.25}
          onNodeClick={(_, node) => { if (node.type === "device") setSelected((node.data as DeviceNodeData).device); }}
          onConnect={handleConnect}
          onEdgeClick={handleEdgeClick}
        >
          <Background gap={22} size={1} />
          <MiniMap pannable zoomable nodeColor={(node) => node.type === "group" ? "#334155" : CRITICALITY_COLOR[(node.data as DeviceNodeData).device?.criticality || ""] || "#94a3b8"} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
      <Modal
        isOpen={Boolean(pendingConnection)}
        title="Nueva conexión"
        onClose={closeConnectionModal}
        footer={
          <>
            <button type="button" className="button button-ghost" onClick={closeConnectionModal}>Cancelar</button>
            <button
              type="button"
              className="button button-primary"
              disabled={saving || !pendingConnection || pendingConnection.source === pendingConnection.target}
              onClick={handleCreateConnection}
            >
              {saving ? "Guardando…" : "Crear conexión"}
            </button>
          </>
        }
      >
        {pendingConnection && (
          <div className="form-grid">
            <label>
              Origen
              <select value={pendingConnection.source} onChange={(e) => setPendingConnection((p) => p && { ...p, source: e.target.value })}>
                {devices.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
              </select>
            </label>
            <label>
              Destino
              <select value={pendingConnection.target} onChange={(e) => setPendingConnection((p) => p && { ...p, target: e.target.value })}>
                {devices.map((d) => <option key={d.id} value={d.id}>{d.label}</option>)}
              </select>
            </label>
            <label>
              Tipo de enlace
              <select value={linkForm.link_type} onChange={(e) => setLinkForm((f) => ({ ...f, link_type: e.target.value as LinkType }))}>
                {LINK_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>
            <label>Puerto origen <input value={linkForm.port_source} onChange={(e) => setLinkForm((f) => ({ ...f, port_source: e.target.value }))} placeholder="Gi0/1" /></label>
            <label>Puerto destino <input value={linkForm.port_target} onChange={(e) => setLinkForm((f) => ({ ...f, port_target: e.target.value }))} placeholder="Gi0/24" /></label>
            <label>VLAN <input type="number" value={linkForm.vlan_id} onChange={(e) => setLinkForm((f) => ({ ...f, vlan_id: e.target.value }))} /></label>
            {pendingConnection.source === pendingConnection.target && (
              <p className="form-error">Origen y destino deben ser dispositivos distintos.</p>
            )}
          </div>
        )}
      </Modal>
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
